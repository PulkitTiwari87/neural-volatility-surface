"""Phase 1 ingestion robustness (GR-QNT-05 date handling, GR-DATA duplicates). SYNTHETIC rows generated here.

Scope: calendar-date parsing, timezone/DST/leap-day behaviour of the quote-date -> expiry-date arithmetic, and
duplicate contract rows. Exchange holiday calendars and early closes are NOT covered: they need a maturity
convention (DEC-005, undecided) and are recorded as an open gap in docs/engineering/CORE_STATUS.md.
"""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from volatility_lab.config.settings import DataConfig
from volatility_lab.ingestion import optionsdx as ox

CFG = DataConfig()
EPOCH = np.datetime64("1970-01-01")


def day(s: str) -> int:
    return int((np.datetime64(s) - EPOCH) / np.timedelta64(1, "D"))


def raw_rows(quote, expire, strike=100.0, **over):
    """One OptionsDX-style row per (quote, expire) pair; ``over`` replaces a column (bracketed name)."""
    n = len(quote)
    df = pd.DataFrame({"[QUOTE_DATE]": quote, "[EXPIRE_DATE]": expire,
                       "[STRIKE]": np.broadcast_to(strike, n).astype(float), "[UNDERLYING_LAST]": 100.0,
                       "[C_BID]": 1.0, "[C_ASK]": 1.1, "[P_BID]": 1.0, "[P_ASK]": 1.1, "[C_IV]": 0.2, "[P_IV]": 0.2})
    for k, v in over.items():
        df[k] = v
    return df


class DateParsingTests(unittest.TestCase):
    def test_iso_dates_keep_the_calendar_date_as_written_even_with_time_or_offset(self):
        written = ["2020-01-02", " 2020-01-02 ", "2020-01-02 23:30:00", "2020-01-02T23:30:00-05:00",
                   "2020-01-02 23:30:00+09:00"]
        d = ox.prefilter_batch(raw_rows(written, ["2020-01-17"] * len(written)), CFG, ox.RejectLedger())
        self.assertEqual(set(d["date"]), {day("2020-01-02")})
        self.assertEqual(len(d), len(written))

    def test_non_iso_and_impossible_dates_are_rejected_not_guessed(self):
        # 01/02/2020 is month-first or day-first depending on the parser: it must not be silently interpreted
        bad = ["01/02/2020", "02/01/2020", "2020-02-30", "20200102", "2020-1-2", "garbage"]
        led = ox.RejectLedger()
        out = ox.prefilter_batch(raw_rows(bad, ["2020-03-01"] * len(bad)), CFG, led)
        self.assertEqual(len(out), 0)
        d = led.to_dict()
        self.assertEqual(d["rejects"], {"bad_quote_date": len(bad)})
        self.assertEqual(d["rows_in"], len(bad))

    def test_tz_aware_datetime_column_is_not_shifted_through_utc(self):
        """23:30 New York on 2 Jan is already 3 Jan in UTC; the quote date must remain 2 Jan."""
        q = pd.Series(pd.to_datetime(["2020-01-02 23:30:00"]).tz_localize("America/New_York"))
        e = pd.Series(pd.to_datetime(["2020-01-17 00:00:00"]).tz_localize("America/New_York"))
        self.assertEqual(q.dt.tz_convert("UTC").dt.date.iloc[0].isoformat(), "2020-01-03")   # the trap
        d = ox.prefilter_batch(raw_rows(q, e), CFG, ox.RejectLedger())
        self.assertEqual(int(d["date"].iloc[0]), day("2020-01-02"))
        self.assertEqual(int(d["expiry"].iloc[0]), day("2020-01-17"))

    def test_naive_datetime_column_parses(self):
        q = pd.Series(pd.to_datetime(["2020-01-02", "2020-01-03"]))
        e = pd.Series(pd.to_datetime(["2020-01-17", "2020-01-17"]))
        d = ox.prefilter_batch(raw_rows(q, e), CFG, ox.RejectLedger())
        self.assertEqual(list(d["date"]), [day("2020-01-02"), day("2020-01-03")])

    def test_days_to_expiry_is_exact_across_dst_changes_and_a_leap_day(self):
        """Dates are calendar days, so a 23/25-hour DST day or a 29 Feb never changes the day count."""
        pairs = [("2020-03-06", "2020-03-13"),   # US spring-forward on 8 Mar
                 ("2020-10-30", "2020-11-06"),   # US fall-back on 1 Nov
                 ("2020-02-24", "2020-03-02"),   # contains 29 Feb 2020
                 ("2021-02-24", "2021-03-03"),   # same span, no leap day
                 ("2020-12-28", "2021-01-04")]   # year boundary
        d = ox.prefilter_batch(raw_rows([p[0] for p in pairs], [p[1] for p in pairs]), CFG, ox.RejectLedger())
        self.assertEqual(len(d), len(pairs))
        self.assertEqual(list((d["expiry"] - d["date"]).astype(int)), [7] * len(pairs))
        # 24 Feb -> 2 Mar is 7 days in 2020 (leap) but 6 days in 2021 (no 29 Feb)
        leap = ox.prefilter_batch(raw_rows(["2020-02-24"], ["2020-03-02"]), CFG, ox.RejectLedger())
        self.assertEqual(int(leap["expiry"].iloc[0] - leap["date"].iloc[0]), 7)
        nonleap = ox.prefilter_batch(raw_rows(["2021-02-24"], ["2021-03-02"]), CFG, ox.RejectLedger())
        self.assertEqual(int(nonleap["expiry"].iloc[0] - nonleap["date"].iloc[0]), 6)


class DuplicateTests(unittest.TestCase):
    def _prefiltered(self, raw):
        led = ox.RejectLedger()
        return ox.prefilter_batch(raw, CFG, led), led

    def test_exact_duplicates_collapse_and_conflicting_duplicates_are_all_rejected(self):
        raw = raw_rows(["2020-01-02"] * 5, ["2020-01-17"] * 5, strike=[100.0, 100.0, 101.0, 101.0, 102.0])
        raw.loc[3, "[C_BID]"] = 0.9                                     # same key as row 2, different quote
        wide, led = self._prefiltered(raw)
        self.assertEqual(len(wide), 5)
        wide = ox.drop_duplicates_with_ledger(wide, led)
        d = led.to_dict()                                               # also asserts conservation
        self.assertEqual(sorted(wide["strike"]), [100.0, 102.0])
        self.assertEqual(d["rejects"], {"duplicate_row_exact": 1, "conflicting_duplicate_key": 2})
        self.assertEqual((d["rows_in"], d["kept"]), (5, 2))

    def test_clean_data_is_untouched_and_order_is_preserved(self):
        raw = raw_rows(["2020-01-02"] * 3, ["2020-01-17"] * 3, strike=[102.0, 100.0, 101.0])
        wide, led = self._prefiltered(raw)
        out = ox.drop_duplicates_with_ledger(wide, led)
        self.assertEqual(list(out["strike"]), [102.0, 100.0, 101.0])
        self.assertEqual(led.to_dict()["rejects"], {})

    def test_same_strike_on_different_dates_or_expiries_is_not_a_duplicate(self):
        raw = raw_rows(["2020-01-02", "2020-01-03", "2020-01-02"], ["2020-01-17", "2020-01-17", "2020-01-24"])
        wide, led = self._prefiltered(raw)
        self.assertEqual(len(ox.drop_duplicates_with_ledger(wide, led)), 3)

    def test_duplicates_across_files_are_found_by_load_wide(self):
        raw = raw_rows(["2020-01-02", "2020-01-02"], ["2020-01-17", "2020-01-17"], strike=[100.0, 101.0])
        with tempfile.TemporaryDirectory() as d:
            raw.to_csv(Path(d) / "a.csv", index=False)
            raw.iloc[[0]].to_csv(Path(d) / "b.csv", index=False)         # the same contract again, other file
            wide, led = ox.load_wide(ox.discover_files(d), CFG)
        info = led.to_dict()
        self.assertEqual(len(wide), 2)
        self.assertEqual(info["rows_in"], 3)
        self.assertEqual(info["rejects"], {"duplicate_row_exact": 1})
        self.assertEqual(info["rows_in"], info["kept"] + sum(info["rejects"].values()))


if __name__ == "__main__":
    unittest.main()
