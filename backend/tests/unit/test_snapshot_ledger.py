"""Phase 1 A2/A3/A4: per-snapshot reconciliation, dataset verification, calendar-day fixtures. SYNTHETIC rows only.

A2: for every snapshot, rows_in = kept + excluded and every exclusion has a reason code; a report is written.
A4: weekend / holiday day counts are plain calendar days by owner decision DEC-005 (2026-10-20); there is deliberately
no exchange-holiday or early-close calendar, so those fixtures assert the *absence* of special handling.
"""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.config.settings import Config, DataConfig
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.ingestion import optionsdx as ox
from volatility_lab.storage.raw_store import OverwriteError, ingest, verify_dataset
from .test_ingestion_robustness import day, raw_rows

CFG = Config()
DCFG = DataConfig()


class SnapshotLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        wide, _ = make_chain(12, seed=4)
        cls.src = cls.dir / "chain.csv"
        wide.to_csv(cls.src, index=False)
        cls.m = ingest(cls.dir / "store", [cls.src], CFG)
        cls.out = cls.dir / "store" / "datasets" / cls.m["version_id"]
        cls.report = json.loads((cls.out / "quality_report.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_every_snapshot_conserves_in_both_stages_and_has_reason_codes(self):
        for stage in ("prefilter_by_snapshot", "quotes_by_snapshot"):
            snaps = self.report[stage]
            self.assertGreater(len(snaps), 5)
            for dt, c in snaps.items():
                self.assertEqual(c["rows_in"], c["kept"] + sum(c["rejects"].values()), (stage, dt))
                self.assertGreaterEqual(c["kept"], 0)
                self.assertTrue(all(isinstance(r, str) and r for r in c["rejects"]))

    def test_snapshots_add_up_to_the_global_ledgers(self):
        for stage, key in (("prefilter_by_snapshot", "ledger_prefilter"), ("quotes_by_snapshot", "ledger_quotes")):
            g, snaps = self.m[key], self.report[stage].values()
            self.assertEqual(sum(c["rows_in"] for c in snaps), g["rows_in"])
            self.assertEqual(sum(c["kept"] for c in snaps), g["kept"])
            by_reason = {}
            for c in snaps:
                for r, n in c["rejects"].items():
                    by_reason[r] = by_reason.get(r, 0) + n
            self.assertEqual(by_reason, g["rejects"])

    def test_report_is_hashed_in_the_manifest_and_dataset_verifies(self):
        self.assertIn("quality_report_sha256", self.m)
        self.assertEqual(verify_dataset(self.dir / "store", self.m["version_id"]), [])

    def test_tampering_with_the_report_is_detected_and_a_reingest_refuses_it(self):
        root = self.dir / "store_t"
        m = ingest(root, [self.src], CFG)
        qr = root / "datasets" / m["version_id"] / "quality_report.json"
        original = qr.read_text()
        qr.write_text(original.replace('"kept"', '"kept_x"', 1))
        self.assertTrue(any("quality report hash" in p for p in verify_dataset(root, m["version_id"])))
        qr.write_text(original)
        self.assertEqual(verify_dataset(root, m["version_id"]), [])
        qr.write_text(original + " ")
        with self.assertRaises(OverwriteError):
            ingest(root, [self.src], CFG)

    def test_tampering_with_the_panel_is_detected(self):
        root = self.dir / "store_p"
        m = ingest(root, [self.src], CFG)
        pf = root / "datasets" / m["version_id"] / "panel.npz"
        with np.load(pf) as z:
            panel = {k: z[k] for k in z.files}
        i = tuple(np.argwhere(np.isfinite(panel["iv"]))[0])
        panel["iv"][i] += 1e-6
        np.savez_compressed(pf, **panel)
        self.assertIn("panel hash mismatch", verify_dataset(root, m["version_id"]))

    def test_missing_dataset_files_are_reported_not_raised(self):
        self.assertTrue(verify_dataset(self.dir / "store", "0" * 64))

    def test_reuse_keeps_the_same_report(self):
        again = ingest(self.dir / "store", [self.src], CFG)
        self.assertTrue(again["reused"])
        self.assertEqual(again["quality_report_sha256"], self.m["quality_report_sha256"])


class DefectsLandOnTheirSnapshotTests(unittest.TestCase):
    def test_each_defect_is_counted_on_its_own_date_and_unknown_dates_get_a_bucket(self):
        raw = raw_rows(["2020-01-02"] * 3 + ["2020-01-03"] * 3 + ["not a date"],
                       ["2020-01-17"] * 7, strike=[100.0, 101.0, 102.0, 100.0, 101.0, 102.0, 100.0])
        for c in ("[C_BID]", "[C_ASK]", "[P_BID]", "[P_ASK]"):
            raw.loc[4, c] = 0.0                                            # unusable row on 3 Jan
        led = ox.RejectLedger()
        wide = ox.prefilter_batch(raw, DCFG, led)
        rep = led.by_date_report()
        self.assertEqual(rep["2020-01-02"], {"rows_in": 3, "kept": 3, "rejects": {}})
        self.assertEqual(rep["2020-01-03"], {"rows_in": 3, "kept": 2, "rejects": {"no_usable_side": 1}})
        self.assertEqual(rep["unknown_date"], {"rows_in": 1, "kept": 0, "rejects": {"bad_quote_date": 1}})
        led.check()
        self.assertEqual(len(wide), 5)

    def test_duplicates_move_from_kept_to_rejected_on_the_right_snapshot(self):
        raw = raw_rows(["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03", "2020-01-03"], ["2020-01-17"] * 5,
                       strike=[100.0, 100.0, 100.0, 101.0, 101.0])
        raw.loc[4, "[C_BID]"] = 0.9                                        # conflicting copy of the 3 Jan 101 row
        led = ox.RejectLedger()
        wide = ox.drop_duplicates_with_ledger(ox.prefilter_batch(raw, DCFG, led), led)
        rep = led.by_date_report()
        self.assertEqual(rep["2020-01-02"], {"rows_in": 2, "kept": 1, "rejects": {"duplicate_row_exact": 1}})
        self.assertEqual(rep["2020-01-03"], {"rows_in": 3, "kept": 1, "rejects": {"conflicting_duplicate_key": 2}})
        led.check()
        self.assertEqual(len(wide), 2)

    def test_a_per_snapshot_imbalance_is_caught(self):
        led = ox.RejectLedger()
        led.note_dates(np.array([day("2020-01-02")] * 2), np.array([0, 0]), ("r",))
        led.rows_in, led.kept = 2, 2
        led.by_date[day("2020-01-02")]["kept"] = 1                         # lose a row on the snapshot only
        with self.assertRaises(AssertionError):
            led.check()


class CalendarDayFixtureTests(unittest.TestCase):
    """DEC-005: maturity is calendar days / 365; no holiday or early-close calendar exists (asserted, not hidden)."""

    def _dte(self, quote, expire):
        d = ox.prefilter_batch(raw_rows([quote], [expire]), DCFG, ox.RejectLedger())
        return int(d["expiry"].iloc[0] - d["date"].iloc[0])

    def test_weekend_and_holiday_gaps_are_plain_calendar_days(self):
        self.assertEqual(self._dte("2020-12-18", "2020-12-21"), 3)       # Friday -> Monday
        self.assertEqual(self._dte("2020-12-24", "2020-12-28"), 4)       # Christmas Day and a weekend inside
        self.assertEqual(self._dte("2020-07-02", "2020-07-06"), 4)       # 3 July holiday (observed) and a weekend

    def test_weekend_quote_dates_are_not_special_cased(self):
        led = ox.RejectLedger()
        d = ox.prefilter_batch(raw_rows(["2020-12-19"], ["2020-12-28"]), DCFG, led)      # a Saturday
        self.assertEqual(len(d), 1)
        self.assertEqual(led.to_dict()["rejects"], {})

    def test_early_close_days_have_no_effect_on_day_counts(self):
        self.assertEqual(self._dte("2020-11-27", "2020-12-04"), 7)       # day after Thanksgiving (13:00 close)


if __name__ == "__main__":
    unittest.main()
