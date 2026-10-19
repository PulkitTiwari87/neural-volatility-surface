import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from volatility_lab.ingestion import optionsdx as ox
from volatility_lab.datasets.synthetic import true_sigma
from volatility_lab.validation.quotes import build_otm_quotes, estimate_forwards
from ._fixtures import CFG, pipeline

R, Q = 0.02, 0.015


class IngestionTests(unittest.TestCase):
    def test_name_normalisation(self):
        self.assertEqual(ox.normalize_name(" [QUOTE_DATE] "), "quote_date")

    def test_messy_vendor_strings_parse_and_ledger_conserves(self):
        P = pipeline()
        led = P["ledger1"].to_dict()
        self.assertEqual(led["rows_in"], len(P["raw"]))
        self.assertEqual(led["rows_in"], led["kept"] + sum(led["rejects"].values()))
        self.assertGreater(led["kept"], 0)
        self.assertTrue(np.isfinite(P["wide"].strike).all())

    def test_each_bad_row_gets_exactly_its_reason(self):
        raw = pipeline()["raw"].head(20).copy()
        raw.loc[0, "[QUOTE_DATE]"] = "garbage"
        raw.loc[1, "[EXPIRE_DATE]"] = ""
        raw.loc[2, "[STRIKE]"] = " -5.0 "
        raw.loc[3, "[EXPIRE_DATE]"] = raw.loc[3, "[QUOTE_DATE]"]          # dte = 0
        raw.loc[4, "[STRIKE]"] = " 1.0 "                                   # far from spot
        for c in ("[C_BID]", "[C_ASK]", "[P_BID]", "[P_ASK]"):
            raw.loc[5, c] = " 0.000000 "
        led = ox.RejectLedger()
        ox.prefilter_batch(raw, CFG.data, led)
        d = led.to_dict()
        for reason in ("bad_quote_date", "bad_expiry", "bad_strike_or_spot", "dte_out_of_range", "strike_far_from_spot", "no_usable_side"):
            self.assertEqual(d["rejects"].get(reason), 1, reason)
        self.assertEqual(d["rows_in"], 20)

    def test_missing_required_column_is_a_schema_error(self):
        raw = pipeline()["raw"].head(5).drop(columns=["[C_BID]"])
        with self.assertRaises(ox.SchemaError):
            ox.prefilter_batch(raw, CFG.data, ox.RejectLedger())

    def test_parquet_and_csv_streaming_match_direct_prefilter(self):
        raw = pipeline()["raw"].head(6000)
        direct = ox.prefilter_batch(raw, CFG.data, ox.RejectLedger())
        with tempfile.TemporaryDirectory() as d:
            raw.to_parquet(Path(d) / "a.parquet")
            wide, led = ox.load_wide(ox.discover_files(d), CFG.data)
            self.assertEqual(len(wide), len(direct))
            self.assertEqual(led.to_dict()["rows_in"], 6000)
        with tempfile.TemporaryDirectory() as d:
            raw.to_csv(Path(d) / "a.csv", index=False)
            wide, _ = ox.load_wide(ox.discover_files(d), CFG.data)
            self.assertEqual(len(wide), len(direct))
        with tempfile.TemporaryDirectory() as d:
            raw.to_parquet(Path(d) / "a.parquet")
            wide, led = ox.load_wide(ox.discover_files(d), CFG.data, max_rows=1000)
            self.assertEqual(led.to_dict()["rows_in"], 1000)

    def test_fingerprint_is_deterministic_and_content_sensitive(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.csv"
            f.write_text("a,b\n1,2\n")
            a = ox.fingerprint_files([f])
            self.assertEqual(a, ox.fingerprint_files([f]))
            f.write_text("a,b\n1,3\n")
            self.assertNotEqual(a["combined_sha256"], ox.fingerprint_files([f])["combined_sha256"])


class ValidationTests(unittest.TestCase):
    def test_forward_and_discount_factor_are_recovered(self):
        P = pipeline()
        fw = estimate_forwards(P["wide"], CFG.data).reset_index()
        truth = P["truth"].copy()
        truth["day"] = truth.date.values.astype("datetime64[D]").astype("int64")
        fw = fw.merge(truth[["day", "spot"]], left_on="date", right_on="day")
        T = (fw.expiry - fw.date) / 365.0
        rel = np.abs(fw.F / (fw.spot * np.exp((R - Q) * T)) - 1)
        self.assertLess(np.median(rel), 5e-4)
        reg = fw[fw.regression]
        self.assertGreater(len(reg), 100)
        self.assertLess(np.median(np.abs(reg.DF - np.exp(-R * T[reg.index]))), 2e-3)

    def test_iv_recovers_the_known_surface(self):
        P = pipeline()
        q = P["quotes"].copy()
        t = P["truth"].copy()
        t["date"] = t.date.values.astype("datetime64[D]").astype("int64")
        q = q.merge(t[["date", "level", "skew"]], on="date")
        err = np.abs(q.iv - true_sigma(q.k, q["T"], q["level"], q["skew"]))
        self.assertLess(np.median(err), 5e-4)
        self.assertLess(np.quantile(err, 0.99), 5e-3)
        self.assertAlmostEqual(P["diag"]["vendor_iv_median_ratio_vendor_over_ours"], 1.0, places=3)

    def test_crossed_and_missing_quotes_are_rejected_with_reasons(self):
        full = pipeline()["wide"]
        wide = full[full.date == full.date.iloc[0]].copy()          # one complete day keeps the parity pairs intact
        sel = wide.index[::7]
        wide.loc[sel, "c_ask"] = wide.loc[sel, "c_bid"] * 0.9
        wide.loc[sel, "p_ask"] = wide.loc[sel, "p_bid"] * 0.9
        quotes, led, _ = build_otm_quotes(wide, CFG.data)
        d = led.to_dict()
        self.assertEqual(d["rows_in"], d["kept"] + sum(d["rejects"].values()))
        self.assertGreaterEqual(d["rejects"].get("crossed_or_locked", 0), 1)
        self.assertEqual(d["kept"], len(quotes))
        self.assertTrue((quotes.rel_spread <= CFG.data.max_rel_spread + 1e-12).all())
        self.assertTrue((quotes.mid >= CFG.data.min_mid - 1e-12).all())

    def test_only_the_otm_side_is_used(self):
        q = pipeline()["quotes"]
        self.assertTrue((q.is_call == (q.k >= 0)).all())


if __name__ == "__main__":
    unittest.main()