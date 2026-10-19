"""Tests for chainpipe (chain -> surface -> evaluation). SYNTHETIC fixtures only; stdlib unittest."""
import csv
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from chainpipe import fixtures as fx
from chainpipe import run as cli
from chainpipe.artifact import SCHEMA_VERSION, build_artifact, canonical_json, code_hashes, load_artifact, write_artifact
from chainpipe.diagnostics import check_surface
from chainpipe.evaluation import AuditedHistory, ChronologyError, assert_chronology, chronological_split, evaluate_baselines
from chainpipe.pipeline import ChainRunConfig, config_dict, run_chain
from chainpipe.schema import (CANONICAL_COLUMNS, ChainSchemaError, CsvChainProvider, ListChainProvider, RowError, SchemaReason, parse_row)
from phase0.forecast import LookaheadError
from phase0.run import OUT_DIR

FIX = fx.FIXTURE_DIR


def read(name):
    return CsvChainProvider(FIX / fx.FILES[name]).read()


def build(read_):
    cfg = ChainRunConfig()
    res = run_chain(read_, cfg)
    return res, build_artifact(read_, res, cfg)


class Schema(unittest.TestCase):
    def test_every_malformed_fixture_row_gets_its_tagged_terminal_disposition(self):
        p = FIX / fx.FILES["malformed"]
        res = run_chain(CsvChainProvider(p).read())
        with open(p, newline="", encoding="utf-8") as fh:
            tags = {i: r["fixture_expected"] for i, r in enumerate(csv.DictReader(fh), 1)}
        self.assertEqual(len(res.dispositions), len(tags))  # exactly one disposition per input row, none dropped
        for i, tag in tags.items():
            got = res.dispositions[i]
            self.assertTrue(got in ("USED", "FORWARD_ONLY") if tag == "OK" else got == tag, (i, tag, got))
        self.assertTrue(res.file_ledger["conserved"])
        self.assertEqual(sum(res.file_ledger["terminal_counts"].values()), len(tags))

    def test_schema_precedence_normalisation_and_timezones(self):
        base = {"quote_timestamp": "2026-03-02T16:00:00-05:00", "underlying_id": "X", "underlying_price": "100", "expiration": "2026-04-17",
                "strike": "100", "option_type": "C", "bid": "1.0", "ask": "1.1", "origin": "synthetic", "source": "s"}
        q = parse_row(1, base)
        self.assertEqual((q.quote_ts.isoformat(), q.option_type), ("2026-03-02T21:00:00+00:00", "call"))  # converted to UTC, 'C' normalised
        self.assertEqual(parse_row(1, dict(base, quote_timestamp="2026-03-02T21:00:00Z")).quote_ts.hour, 21)
        both = parse_row(7, dict(base, quote_timestamp="nope", strike="-1"))
        self.assertEqual((both.row, both.code), (7, SchemaReason.BAD_TIMESTAMP.value))  # first failing check wins
        self.assertEqual(parse_row(1, dict(base, strike="1e999")).code, "BAD_STRIKE")  # non-finite
        self.assertEqual(parse_row(1, dict(base, expiration="2026-03-02")).code, "BAD_EXPIRY")  # T = 0
        self.assertIsNone(parse_row(1, dict(base, bid="nan")).bid)  # becomes None; phase0 validation reports MISSING_FIELD
        self.assertIsInstance(parse_row(1, dict(base, bid="x")), RowError)

    def test_file_level_problems_fail_fast(self):
        rows = [{c: "" for c in CANONICAL_COLUMNS if c != "ask"}]
        with self.assertRaises(ChainSchemaError):
            ListChainProvider(rows).read()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.csv"
            p.write_bytes(b"\xff\xfe\x00bad")
            with self.assertRaises(ChainSchemaError):
                CsvChainProvider(p).read()

    def test_extra_columns_are_ignored_and_recorded(self):
        r = read("malformed")
        self.assertEqual(r.extra_columns, ("fixture_expected",))
        _, art = build(r)
        self.assertEqual(art["provenance"]["extra_columns_ignored"], ["fixture_expected"])

    def test_in_memory_provider_uses_the_same_contract(self):
        rows = fx.normal_rows()
        a = ListChainProvider(rows).read()
        b = CsvChainProvider(FIX / fx.FILES["normal"]).read()
        self.assertEqual([s.quote_ts for s in a.snapshots], [s.quote_ts for s in b.snapshots])
        self.assertEqual(a.n_rows, b.n_rows)


class Pipeline(unittest.TestCase):
    def test_iv_recovery_against_the_known_generating_vol(self):
        res = run_chain(read("normal"))
        s = res.snapshots[0]
        T = {e["expiration"]: e["T"] for e in s["expiries"]}
        err = max(abs(o["iv"] - fx.true_iv(o["k"], T[o["expiration"]], 0.20)) for o in s["observations"])
        self.assertLess(err, 1e-7)
        self.assertEqual(len(s["observations"]), 39)

    def test_surface_statuses_are_honest_and_never_extrapolated(self):
        s = run_chain(read("normal")).snapshots[0]
        surf, k = s["surface"], s["surface"]["k_nodes"]
        self.assertNotIn("extrapolated", {c for r in surf["status"] for c in r})
        for ri, e in enumerate(s["expiries"]):
            ks = [o["k"] for o in s["observations"] if o["expiration"] == e["expiration"]]
            for j, node in enumerate(k):
                st, v = surf["status"][ri][j], surf["iv"][ri][j]
                if st == "missing":
                    self.assertIsNone(v)
                else:
                    self.assertIsNotNone(v)
                    self.assertTrue(min(ks) <= node <= max(ks))  # inside the observed hull only
        self.assertEqual(s["diagnostics"]["cell_status_counts"], {"missing": 9, "interpolated": 18})

    def test_strikes_on_the_node_grid_give_observed_cells_with_exact_values(self):
        ts, spot, e = "2026-03-02T21:00:00+00:00", 100.0, "2026-04-17"
        T = (fx.date.fromisoformat(e) - fx.date(2026, 3, 2)).days / 365.0
        F = spot * math.exp((fx.RATE - fx.DIV) * T)
        cfg = ChainRunConfig()
        rows = []
        for k in cfg.surface.k_nodes:
            K = F * math.exp(k)
            iv = fx.true_iv(k, T, 0.20)
            for ot in ("call", "put"):
                m = fx.black76_price(F, K, T, fx.RATE, iv, ot == "call")
                h = min(0.5 * m, 0.02 * m + 0.005)
                rows.append(dict(fx._row(ts, spot, e, K, ot, 0.0, 0.0), strike=repr(K), bid=repr(m - h), ask=repr(m + h)))
        s = run_chain(ListChainProvider(rows).read(), cfg).snapshots[0]
        self.assertEqual(set(s["surface"]["status"][0]), {"observed"})
        for j, k in enumerate(cfg.surface.k_nodes):
            self.assertAlmostEqual(s["surface"]["iv"][0][j], fx.true_iv(k, T, 0.20), delta=1e-8)

    def test_solver_failures_are_explicit_and_no_iv_is_fabricated(self):
        res = run_chain(read("malformed"))
        s = res.snapshots[0]
        self.assertEqual({f["status"] for f in s["solver_failures"]}, {"PRICE_ABOVE_UPPER_BOUND", "NO_BRACKET"})
        failed = {f["row"] for f in s["solver_failures"]}
        self.assertFalse(failed & {o["row"] for o in s["observations"]})  # a failed solve never becomes an observation
        self.assertEqual(s["solver_status_counts"], {"CONVERGED": 10, "NO_BRACKET": 1, "PRICE_ABOVE_UPPER_BOUND": 1})
        for f in s["solver_failures"]:
            self.assertTrue(f["reason"])

    def test_unalignable_and_implausible_expiries_are_reported_and_left_missing(self):
        s = run_chain(read("malformed")).snapshots[0]
        status = {e["expiration"]: e["status"] for e in s["expiries"]}
        self.assertEqual(status, {"2026-04-17": "ALIGNED", "2026-05-15": "UNALIGNABLE_EXPIRY", "2026-06-18": "ALIGNED", "2026-07-17": "FORWARD_IMPLAUSIBLE"})
        for ri, e in enumerate(s["expiries"]):
            if e["status"] != "ALIGNED":
                self.assertEqual(set(s["surface"]["status"][ri]), {"missing"})
        implaus = [e for e in s["expiries"] if e["status"] == "FORWARD_IMPLAUSIBLE"][0]
        self.assertGreater(implaus["forward_over_spot"], 1.25)  # reported, not hidden

    def test_the_modal_underlying_price_defines_the_snapshot(self):
        s = run_chain(read("malformed")).snapshots[0]
        self.assertEqual(s["underlying_price"], 100.0)

    def test_config_is_recorded_with_the_day_count_and_is_stable(self):
        d = config_dict(ChainRunConfig())
        self.assertIn("ACT/365", d["day_count"])
        self.assertEqual(canonical_json(d), canonical_json(config_dict(ChainRunConfig())))
        self.assertNotEqual(canonical_json(d), canonical_json(config_dict(ChainRunConfig(rate=0.03))))


class Diagnostics(unittest.TestCase):
    K = [-0.1, 0.0, 0.1]

    def rows(self, *Ts):
        return [{"T": T, "F": 100.0} for T in Ts]

    def test_a_flat_surface_passes_every_check(self):
        d = check_surface(self.rows(0.1, 0.2), [[0.2] * 3, [0.2] * 3], [["observed"] * 3] * 2, self.K, 0.0)
        self.assertEqual((d["calendar_violations"], d["butterfly_violations"], d["slope_bound_violations"]), (0, 0, 0))
        self.assertEqual(d["checked"], {"calendar_pairs": 3, "butterfly_triples": 2, "slope_pairs": 4})
        self.assertTrue(d["flags_only"])

    def test_calendar_violation_is_detected_with_its_size_and_interpolation_flag(self):
        st = [["observed"] * 3, ["observed", "interpolated", "observed"]]
        d = check_surface(self.rows(0.1, 0.2), [[0.30] * 3, [0.15] * 3], st, self.K, 0.0)
        self.assertEqual(d["calendar_violations"], 3)
        ex = d["examples"]["calendar"]
        self.assertAlmostEqual(ex[0]["shortfall"], 0.30 ** 2 * 0.1 - 0.15 ** 2 * 0.2, places=12)
        self.assertEqual([e["uses_interpolated"] for e in ex], [False, True, False])

    def test_a_concave_price_bump_breaks_butterfly_convexity(self):
        d = check_surface(self.rows(0.1), [[0.2, 0.9, 0.2]], [["observed"] * 3], self.K, 0.0)
        self.assertEqual(d["butterfly_violations"], 1)
        self.assertGreater(d["examples"]["butterfly"][0]["convexity_shortfall"], 0)

    def test_an_increasing_call_price_in_strike_breaks_the_slope_bound(self):
        d = check_surface(self.rows(0.1), [[0.05, 0.05, 2.0]], [["observed"] * 3], self.K, 0.0)
        self.assertGreaterEqual(d["slope_bound_violations"], 1)

    def test_missing_cells_and_rows_are_skipped_not_guessed(self):
        d = check_surface([None, {"T": 0.2, "F": 100.0}], [[None] * 3, [0.2, None, 0.2]], [["missing"] * 3, ["observed", "missing", "observed"]], self.K, 0.0)
        self.assertEqual(d["checked"], {"calendar_pairs": 0, "butterfly_triples": 0, "slope_pairs": 1})
        self.assertEqual(d["cell_status_counts"], {"missing": 4, "observed": 2})


class Artifact(unittest.TestCase):
    def test_deterministic_content_hash_and_provenance(self):
        r = read("normal")
        _, a = build(r)
        _, b = build(read("normal"))
        self.assertEqual(canonical_json(a), canonical_json(b))
        self.assertEqual(a["version_id"], "sfc-" + a["content_sha256"][:16])
        self.assertEqual(a["label"], "SYNTHETIC - not market data")
        self.assertEqual(a["provenance"]["input_sha256"], hashlib.sha256((FIX / fx.FILES["normal"]).read_bytes()).hexdigest())
        self.assertTrue(any(k.startswith("chainpipe/") for k in a["provenance"]["code_sha256"]) and any(k.startswith("phase0/") for k in a["provenance"]["code_sha256"]))
        self.assertEqual(a["provenance"]["code_sha256"], code_hashes())
        self.assertEqual(a["schema"], SCHEMA_VERSION)

    def test_round_trip_tamper_detection_and_refusals(self):
        _, art = build(read("normal"))
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            write_artifact(p, art)
            self.assertEqual(load_artifact(p)["content_sha256"], art["content_sha256"])
            with self.assertRaises(SystemExit):
                write_artifact(p, art)  # overwrite refused
            p.write_text(p.read_text().replace('"underlying_price":100.0', '"underlying_price":101.0'))
            with self.assertRaises(ValueError):
                load_artifact(p)  # modified after writing
            q = Path(td) / "old.json"
            q.write_text(canonical_json(dict(art, schema="chainpipe-surface-0")))
            with self.assertRaises(ValueError):
                load_artifact(q)
        with self.assertRaises(SystemExit):
            write_artifact(OUT_DIR / "chainpipe_should_never_exist.json", art)
        self.assertFalse((OUT_DIR / "chainpipe_should_never_exist.json").exists())

    def test_nan_cannot_be_serialised(self):
        with self.assertRaises(ValueError):
            canonical_json({"x": float("nan")})

    def test_non_synthetic_origin_changes_the_label(self):
        rows = [dict(r, origin="provider") for r in fx.normal_rows()]
        rd = ListChainProvider(rows).read()
        res = run_chain(rd)
        art = build_artifact(rd, res, ChainRunConfig())
        self.assertEqual(art["origins"], ["provider"])
        self.assertIn("NON-SYNTHETIC", art["label"])


def toy_artifact(ivs, drop_origin_contract=False):
    """Minimal artifact from a list of IVs for one contract and one surface cell (hand-checkable)."""
    snaps = []
    for i, v in enumerate(ivs):
        obs = [] if (drop_origin_contract and i == 1) else [{"row": 1, "expiration": "2026-06-18", "strike": 100.0, "option_type": "call", "k": 0.0, "iv": v}]
        snaps.append({"underlying_id": "X", "quote_timestamp": "2026-03-%02dT21:00:00+00:00" % (i + 2),
                      "expiries": [{"expiration": "2026-06-18", "T": 0.25}], "observations": obs,
                      "surface": {"k_nodes": [0.0], "iv": [[v]], "status": [["observed"]]}})
    return {"snapshots": snaps, "label": "SYNTHETIC - not market data", "version_id": "toy", "content_sha256": "0" * 64}


class Evaluation(unittest.TestCase):
    def test_chronological_split_is_contiguous_ordered_and_never_empty(self):
        s = chronological_split(10, 0.6, 0.2)
        self.assertEqual((len(s["train"]), len(s["valid"]), len(s["test"])), (6, 2, 2))
        self.assertEqual(s["train"] + s["valid"] + s["test"], list(range(10)))  # no shuffling
        self.assertEqual([len(v) for v in chronological_split(3, 0.6, 0.2).values()], [1, 1, 1])
        with self.assertRaises(ValueError):
            chronological_split(2, 0.6, 0.2)  # an empty validation block is refused

    def test_chronology_violations_are_rejected(self):
        snaps = toy_artifact([0.2, 0.2, 0.2])["snapshots"]
        assert_chronology(snaps)
        for bad in ([snaps[1], snaps[0], snaps[2]], [snaps[0], snaps[0], snaps[2]]):
            with self.assertRaises(ChronologyError):
                assert_chronology(bad)
        with self.assertRaises(ChronologyError):
            assert_chronology([snaps[0], dict(snaps[1], underlying_id="Y")])

    def test_baseline_metrics_equal_a_hand_computation(self):
        art = toy_artifact([0.20, 0.22, 0.21, 0.25, 0.24])
        r = evaluate_baselines(art, 0.5, 0.25)
        self.assertEqual({s: v["n_targets"] for s, v in r["splits"].items()}, {"train": 2, "valid": 1, "test": 1})
        p = r["tasks"]["contract_level"]["persistence"]["metrics"]
        self.assertEqual((p["train"]["n"], p["valid"]["n"], p["test"]["n"]), (2, 1, 1))
        self.assertAlmostEqual(p["train"]["mae"], 0.015, places=12)  # errors -0.02, +0.01
        self.assertAlmostEqual(p["train"]["rmse"], math.sqrt(2.5e-4), places=12)
        self.assertAlmostEqual(p["valid"]["bias_pred_minus_actual"], -0.04, places=12)
        self.assertAlmostEqual(p["test"]["mae_volpts"], 1.0, places=9)
        m = r["tasks"]["contract_level"]["historical_mean"]["metrics"]
        self.assertAlmostEqual(m["train"]["mae"], 0.01, places=12)  # errors -0.02 and 0.0
        self.assertAlmostEqual(m["valid"]["bias_pred_minus_actual"], -0.04, places=12)
        self.assertAlmostEqual(m["test"]["bias_pred_minus_actual"], -0.02, places=12)
        self.assertTrue(r["leakage_audit"]["all_passed"])

    def test_a_later_snapshot_cannot_change_an_earlier_prediction(self):
        a = evaluate_baselines(toy_artifact([0.20, 0.22, 0.21, 0.25, 0.24]), 0.5, 0.25)
        b = evaluate_baselines(toy_artifact([0.20, 0.22, 0.21, 0.25, 0.99]), 0.5, 0.25)  # only the very last snapshot differs
        for task in ("contract_level", "surface_cell_level"):
            for base in ("persistence", "historical_mean"):
                for split in ("train", "valid"):
                    self.assertEqual(a["tasks"][task][base]["metrics"][split], b["tasks"][task][base]["metrics"][split])
                self.assertNotEqual(a["tasks"][task][base]["metrics"]["test"], b["tasks"][task][base]["metrics"]["test"])

    def test_history_guard_raises_on_lookahead_and_records_the_largest_index_read(self):
        h = AuditedHistory([10, 20, 30, 40], 1)
        self.assertEqual((h[0], h[-1]), (10, 20))
        self.assertEqual(h.max_index, 1)
        with self.assertRaises(LookaheadError):
            h[2]

    def test_skipped_cells_are_counted_by_reason(self):
        r = evaluate_baselines(toy_artifact([0.20, 0.22, 0.21, 0.25, 0.24], drop_origin_contract=True), 0.5, 0.25)
        self.assertEqual(r["tasks"]["contract_level"]["persistence"]["skipped_cells"], {"cell_not_in_origin": 1})
        self.assertEqual(r["tasks"]["contract_level"]["historical_mean"]["skipped_cells"], {})  # history before the origin still has the contract

    def test_too_few_snapshots_are_refused(self):
        with self.assertRaises(ValueError):
            evaluate_baselines(toy_artifact([0.2, 0.2, 0.2]))

    def test_synthetic_series_evaluation_is_audited_labelled_and_deterministic(self):
        _, art = build(read("series"))
        a, b = evaluate_baselines(art), evaluate_baselines(art)
        self.assertEqual(a["content_sha256"], b["content_sha256"])
        self.assertTrue(a["leakage_audit"]["all_passed"])
        self.assertEqual(a["artifact_version_id"], art["version_id"])
        self.assertEqual(a["label"], "SYNTHETIC - not market data")
        for base in ("persistence", "historical_mean"):
            self.assertGreater(a["tasks"]["contract_level"][base]["metrics"]["test"]["n"], 0)
        surf = a["tasks"]["surface_cell_level"]["persistence"]["by_target_status"]["test"]
        self.assertEqual(set(surf), {"interpolated"})  # strikes are not on the node grid: no observed cells, and the report says so


class FixturesAndCli(unittest.TestCase):
    def test_committed_fixtures_equal_the_generator_output_and_are_labelled_synthetic(self):
        for name, text in fx.generate().items():
            self.assertIn(".synthetic.", name)
            self.assertEqual((FIX / name).read_text(encoding="utf-8"), text)
            with open(FIX / name, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    if row.get("fixture_expected") != "BAD_ORIGIN":  # the one deliberately invalid-origin row
                        self.assertEqual(row["origin"], "synthetic")

    def test_fixture_writer_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(SystemExit):
                fx.main(["--out-dir", td])
            fx.main(["--out-dir", str(Path(td) / "new")])
            self.assertEqual(len(list((Path(td) / "new").iterdir())), 3)

    def test_cli_build_then_evaluate_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            a, e = Path(td) / "s.json", Path(td) / "e.json"
            self.assertEqual(cli.main(["build", "--input", str(FIX / fx.FILES["series"]), "--out", str(a)]), 0)
            self.assertEqual(cli.main(["evaluate", "--artifact", str(a), "--out", str(e)]), 0)
            ev = json.loads(e.read_text())
            self.assertEqual(ev["artifact_content_sha256"], load_artifact(a)["content_sha256"])
            for args in (["build", "--input", str(FIX / fx.FILES["series"]), "--out", str(a)], ["evaluate", "--artifact", str(a), "--out", str(e)]):
                with self.assertRaises(SystemExit):
                    cli.main(args)  # existing outputs are refused
            a.write_text(a.read_text().replace('"rate":0.02', '"rate":0.05'))
            with self.assertRaises(ValueError):
                cli.main(["evaluate", "--artifact", str(a), "--out", str(Path(td) / "e2.json")])  # tampered artifact

    def test_cli_refuses_experiments_directory_and_missing_columns(self):
        with self.assertRaises(SystemExit):
            cli.main(["build", "--input", str(FIX / fx.FILES["normal"]), "--out", str(OUT_DIR / "chainpipe_should_never_exist.json")])
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.csv"
            bad.write_text("quote_timestamp,strike\n2026-03-02T21:00:00Z,100\n")
            with self.assertRaises(ChainSchemaError):
                cli.main(["build", "--input", str(bad), "--out", str(Path(td) / "o.json")])


if __name__ == "__main__":
    unittest.main()
