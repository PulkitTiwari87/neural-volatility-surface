"""Contract-level quote persistence (Q-D5; STORAGE_DESIGN 8.8 D1-D10). SYNTHETIC data and temp directories only.

Checks: the store is additive (dataset files, panel_sha256 and the default outputs of load_wide / build_otm_quotes
are unchanged); every quote-stage row and every no_usable_side reject is persisted with its reason and reconciles
with the ledgers; both sides are stored; contract ids are stable across days; a rebuild is reused, tampering is
detected, derived floats are compared within the policy tolerance; purge keeps the manifest; real data is refused.
"""
import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from volatility_lab.config.settings import Config, QuotePolicy
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.ingestion.optionsdx import load_wide
from volatility_lab.storage import quote_store as qs
from volatility_lab.storage.raw_store import OverwriteError, ingest
from volatility_lab.validation.quotes import build_otm_quotes

CFG = Config()


def _tree_hashes(d: Path) -> dict:
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}


def _chain(path: Path) -> int:
    """Synthetic chain with 3 injected no_usable_side rows (near the money) plus one exact copy of one of them."""
    wide, _ = make_chain(12, seed=1, messy_format=False)
    spot = wide["[UNDERLYING_LAST]"].astype(float)
    near = wide.index[(np.abs(np.log(wide["[STRIKE]"] / spot)) < 0.05) & (wide["[DTE]"] > 20)][[0, 40, 80]]
    for c in ("[C_BID]", "[C_ASK]", "[P_BID]", "[P_ASK]"):
        wide.loc[near, c] = 0.0
    wide = pd.concat([wide, wide.loc[[near[0]]]], ignore_index=True)
    wide.to_csv(path, index=False)
    return len(near)


class QuoteStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        cls.src = cls.dir / "chain.synthetic.csv"
        cls.n_unusable = _chain(cls.src)
        cls.root = cls.dir / "store"
        cls.ds = ingest(cls.root, [cls.src], CFG, origin="synthetic")
        cls.ds_dir = cls.root / "datasets" / cls.ds["version_id"]
        cls.before = _tree_hashes(cls.ds_dir)
        cls.m = qs.build_quote_set(cls.root, [cls.src], CFG, underlying="SYNTH", exercise_style="european")
        cls.qid = cls.m["quote_set_id"]
        cls.rows = qs.load_quote_rows(cls.root, cls.qid)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    # --- additive: nothing existing changes -------------------------------------------------------------------------
    def test_dataset_files_and_panel_hash_are_untouched(self):
        self.assertEqual(_tree_hashes(self.ds_dir), self.before)
        again = ingest(self.root, [self.src], CFG, origin="synthetic")
        self.assertTrue(again["reused"])
        self.assertEqual(again["panel_sha256"], self.ds["panel_sha256"])
        self.assertEqual(self.m["panel_sha256"], self.ds["panel_sha256"])

    def test_opt_in_flags_do_not_change_the_default_outputs(self):
        stored = sorted((self.root / "raw").rglob("*.csv"))
        w0, l0 = load_wide(stored, CFG.data)
        w1, l1, unusable = load_wide(stored, CFG.data, return_unusable=True)
        pd.testing.assert_frame_equal(w0, w1)
        self.assertEqual(l0.to_dict(), l1.to_dict())
        self.assertEqual(len(unusable), self.n_unusable + 1)            # the injected exact copy is still there
        q0, g0, d0 = build_otm_quotes(w0, CFG.data)
        q1, g1, d1, rows = build_otm_quotes(w0, CFG.data, return_rows=True)
        pd.testing.assert_frame_equal(q0, q1)
        self.assertEqual(g0.to_dict(), g1.to_dict())
        self.assertEqual(json.dumps(d0, sort_keys=True), json.dumps(d1, sort_keys=True))
        self.assertEqual(len(rows), len(w0))

    def test_config_hash_does_not_include_the_quote_policy(self):
        self.assertEqual([f.name for f in dataclasses.fields(Config)], ["data", "surface", "features", "split", "train"])
        def keys(d):
            return set(d) | {k for v in d.values() if isinstance(v, dict) for k in keys(v)}
        cfg_keys = keys(Config().to_dict())
        self.assertFalse(cfg_keys & {f.name for f in dataclasses.fields(QuotePolicy)}, cfg_keys)
        self.assertNotIn("quote_policy", cfg_keys)

    # --- content: reconciliation, both sides, reasons ---------------------------------------------------------------
    def test_rows_reconcile_with_the_dataset_ledgers(self):
        lq, lp = self.ds["ledger_quotes"], self.ds["ledger_prefilter"]
        sel = self.rows[self.rows["otm_selected"]]
        self.assertEqual(int((sel["disposition"] == "retained").sum()), lq["kept"])
        self.assertEqual(len(sel), lq["rows_in"])
        for reason, n in lq["rejects"].items():
            self.assertEqual(int((sel["reason"] == reason).sum()), n, reason)
        unusable = self.rows[self.rows["reason"] == "no_usable_side"]
        self.assertEqual(len(unusable), 2 * self.n_unusable)             # both sides of each injected row
        self.assertEqual(self.m["counts"]["unusable_exact_duplicates"], 1)
        self.assertEqual(self.n_unusable + 1, lp["rejects"]["no_usable_side"])
        self.assertTrue((self.rows.loc[self.rows["disposition"] == "excluded", "reason"].notna()).all())
        self.assertTrue(self.rows.loc[self.rows["disposition"] != "excluded", "reason"].isna().all())

    def test_both_sides_are_stored_and_exactly_one_is_selected(self):
        stage = self.rows[self.rows["reason"] != "no_usable_side"]
        g = stage.groupby(["quote_date", "expiry", "strike"])
        self.assertTrue((g.size() == 2).all())
        self.assertTrue((g["otm_selected"].sum() == 1).all())
        other = stage[~stage["otm_selected"]]
        self.assertTrue((other["disposition"] == "not_selected").all())
        self.assertTrue(other["iv"].isna().all())
        self.assertTrue((other["solver_status"] == "not_attempted").all())

    def test_retained_rows_carry_the_same_iv_as_the_surface_input(self):
        quotes, _, _ = build_otm_quotes(load_wide(sorted((self.root / "raw").rglob("*.csv")), CFG.data)[0], CFG.data)
        kept = self.rows[self.rows["disposition"] == "retained"]
        self.assertEqual(len(kept), len(quotes))
        merged = kept.merge(quotes, left_on=["quote_date", "expiry", "strike"], right_on=["date", "expiry", "strike"])
        self.assertEqual(len(merged), len(quotes))
        np.testing.assert_array_equal(merged["iv_x"].to_numpy(dtype=float), merged["iv_y"].to_numpy(dtype=float))
        self.assertTrue(((merged["option_type"] == "C") == merged["is_call"]).all())

    def test_contract_id_is_stable_across_days_and_distinguishes_sides(self):
        r = self.rows
        per_key = r.groupby(["expiry", "strike", "option_type"])["contract_id"].nunique()
        self.assertTrue((per_key == 1).all())
        self.assertGreater(r.groupby("contract_id")["quote_date"].nunique().max(), 1)
        self.assertEqual(r["contract_id"].nunique(), len(per_key))
        self.assertFalse(r.duplicated(["contract_id", "quote_date"]).any())
        a = qs.contract_ids("SYNTH", [17000], [300.0], ["C"])[0]
        self.assertEqual(a, hashlib.sha256(b"SYNTH|2016-07-18|300|C").hexdigest())

    def test_nulls_labels_and_timestamp_convention(self):
        r = self.rows
        for c in ("settlement", "quote_time_local", "tz"):
            self.assertTrue(r[c].isna().all(), c)
        self.assertTrue((r["snapshot_kind"] == "eod_close").all())
        for c in qs.DERIVED_FLOATS:
            v = pd.to_numeric(r[c]).to_numpy(dtype=float)
            self.assertFalse(np.isinf(v).any(), c)
        self.assertEqual(self.m["origin"], "synthetic")
        self.assertEqual(self.m["licence_class"], "synthetic")
        self.assertIn("not live", self.m["data_mode"])
        self.assertIn("DEC-009 benchmark not run", self.m["file_format"])
        self.assertTrue((self.root / "quotes" / self.qid / "slice_forward.parquet").is_file())

    # --- identity, rebuild, tamper, tolerance -----------------------------------------------------------------------
    def test_rebuild_is_reused_and_the_id_depends_on_policy(self):
        again = qs.build_quote_set(self.root, [self.src], CFG, underlying="SYNTH", exercise_style="european")
        self.assertTrue(again["reused"])
        self.assertEqual(again["quote_set_id"], self.qid)
        self.assertEqual(qs.verify_quote_set(self.root, self.qid), [])
        other = qs.quote_set_id(self.ds["version_id"], QuotePolicy(rebuild_rel_tol=1e-8))
        self.assertNotEqual(other, self.qid)

    def test_derived_floats_are_compared_within_the_policy_tolerance(self):
        near = self.rows.copy()
        near["iv"] = pd.to_numeric(near["iv"]) * (1 + 1e-14)              # the size of the L-34 cross-platform drift
        self.assertEqual(qs.verify_quote_set(self.root, self.qid, rebuilt=near), [])
        far = self.rows.copy()
        far["iv"] = pd.to_numeric(far["iv"]) * (1 + 1e-6)
        self.assertIn("rebuild: derived column iv outside tolerance 1e-09", qs.verify_quote_set(self.root, self.qid,
                                                                                              rebuilt=far))
        moved = self.rows.copy()
        moved.loc[0, "bid"] = moved.loc[0, "bid"] + 0.01
        self.assertIn("rebuild: source columns differ", qs.verify_quote_set(self.root, self.qid, rebuilt=moved))

    def test_tampered_file_is_detected_and_blocks_a_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "s"
            ingest(root, [self.src], CFG, origin="synthetic")
            m = qs.build_quote_set(root, [self.src], CFG, underlying="SYNTH", exercise_style="european")
            part = sorted((root / "quotes" / m["quote_set_id"] / "rows").glob("*.parquet"))[0]
            part.write_bytes(part.read_bytes() + b"x")
            self.assertTrue(qs.verify_quote_set(root, m["quote_set_id"]))
            with self.assertRaises(OverwriteError):
                qs.build_quote_set(root, [self.src], CFG, underlying="SYNTH", exercise_style="european")

    # --- purge (D3) -------------------------------------------------------------------------------------------------
    def test_purge_keeps_the_manifest_and_blocks_silent_recreation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "s"
            ingest(root, [self.src], CFG, origin="synthetic")
            m = qs.build_quote_set(root, [self.src], CFG, underlying="SYNTH", exercise_style="european")
            out = root / "quotes" / m["quote_set_id"]
            with self.assertRaises(ValueError):
                qs.purge_quote_set(root, m["quote_set_id"], " ")
            rec = qs.purge_quote_set(root, m["quote_set_id"], "synthetic purge drill")
            self.assertEqual(rec["reason"], "synthetic purge drill")
            self.assertTrue((out / "manifest.json").is_file())
            self.assertEqual(list(out.rglob("*.parquet")), [])
            self.assertEqual(qs.verify_quote_set(root, m["quote_set_id"]), [])
            with self.assertRaises(FileNotFoundError):
                qs.load_quote_rows(root, m["quote_set_id"])
            with self.assertRaises(OverwriteError):
                qs.purge_quote_set(root, m["quote_set_id"], "again")
            with self.assertRaises(OverwriteError):
                qs.build_quote_set(root, [self.src], CFG, underlying="SYNTH", exercise_style="european")

    # --- guards: synthetic only (Q-D5) ------------------------------------------------------------------------------
    def test_real_data_and_unlabelled_inputs_are_refused(self):
        with self.assertRaises(ValueError):
            qs.build_quote_set(self.root, [self.src], CFG, underlying="SYNTH", exercise_style="european", origin="real")
        with tempfile.TemporaryDirectory() as td:
            plain = Path(td) / "chain.csv"
            plain.write_bytes(self.src.read_bytes())
            with self.assertRaises(ValueError):
                qs.build_quote_set(Path(td) / "s", [plain], CFG, underlying="SYNTH", exercise_style="european")
            root = Path(td) / "no_origin"
            with self.assertRaises(FileNotFoundError):                    # not ingested yet
                qs.build_quote_set(root, [self.src], CFG, underlying="SYNTH", exercise_style="european")
            ingest(root, [self.src], CFG)                                 # ingested without an origin label
            with self.assertRaises(ValueError):
                qs.build_quote_set(root, [self.src], CFG, underlying="SYNTH", exercise_style="european")
            self.assertFalse((root / "quotes").exists())
        with self.assertRaises(ValueError):
            qs.build_quote_set(self.root, [self.src], CFG, underlying="SYNTH", exercise_style="bermudan")


if __name__ == "__main__":
    unittest.main()
