"""Quote validation -> forward/discount factor -> OTM selection -> implied volatility.

Input is the compact wide frame from ``ingestion.optionsdx``. Output is one row per *kept* out-of-the-money
quote with its Black-76 implied volatility, plus a conserved ledger explaining every dropped row.

Method (assumptions are deliberate and listed in KNOWN_LIMITATIONS):

* The forward ``F`` and discount factor ``DF`` of each (date, expiry) slice come from put-call parity on
  near-ATM pairs: ``C - P = DF * (F - K)``. With >= ``regression_min_pairs`` pairs and a long enough
  maturity both are fitted by OLS; otherwise ``DF = 1`` and ``F`` is the median of ``C - P + K``.
  No external rate or dividend series is used.
* The underlying ETF options are American-style. Black-76 is a European model, so deep ITM quotes would be
  biased; only the OTM side of each strike is used, which keeps the early-exercise premium small.
* Quotes are mid prices of a closing snapshot, not executable prices.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from volatility_lab.config.settings import DataConfig
from volatility_lab.ingestion.optionsdx import RejectLedger
from volatility_lab.pricing import bs

QUOTE_REASONS = ("no_parity_forward", "implausible_forward", "k_out_of_range", "missing_or_no_bid",
                 "crossed_or_locked", "low_price", "wide_spread", "iv_below_lower_bound",
                 "iv_above_upper_bound", "iv_invalid_input", "iv_out_of_bounds",
                 "iv_below_solver_floor", "iv_above_solver_ceiling")


def estimate_forwards(wide: pd.DataFrame, cfg: DataConfig) -> pd.DataFrame:
    """Per (date, expiry): ``F``, ``DF``, pair count, method and plausibility status.

    ``fstat``: 0 ok, 1 no usable parity pairs, 2 implausible forward vs spot.
    """
    c_ok = (wide.c_bid > 0) & (wide.c_ask > wide.c_bid)
    p_ok = (wide.p_bid > 0) & (wide.p_ask > wide.p_bid)
    with np.errstate(invalid="ignore", divide="ignore"):
        near = np.abs(np.log(wide.strike / wide.spot)) <= cfg.parity_window_k
    sel = c_ok & p_ok & near
    g = wide.loc[sel, ["date", "expiry", "strike", "spot"]].copy()
    g["D"] = 0.5 * (wide.c_bid[sel] + wide.c_ask[sel]) - 0.5 * (wide.p_bid[sel] + wide.p_ask[sel])
    g["KK"] = g.strike ** 2
    g["KD"] = g.strike * g.D
    g["F1"] = g.D + g.strike
    st = g.groupby(["date", "expiry"], sort=False).agg(
        n=("strike", "size"), sK=("strike", "sum"), sD=("D", "sum"), sKK=("KK", "sum"),
        sKD=("KD", "sum"), medF=("F1", "median"), spot=("spot", "mean"))
    idx = st.index.to_frame(index=False)
    T = (idx.expiry.to_numpy() - idx.date.to_numpy()) / 365.0
    n = st.n.to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        den = n * st.sKK.to_numpy() - st.sK.to_numpy() ** 2
        slope = (n * st.sKD.to_numpy() - st.sK.to_numpy() * st.sD.to_numpy()) / den
        icpt = (st.sD.to_numpy() - slope * st.sK.to_numpy()) / n
        df_reg = -slope
        f_reg = icpt / df_reg
    lo, hi = cfg.df_bounds
    use_reg = ((n >= cfg.regression_min_pairs) & (T >= cfg.regression_min_T) & (den > 0)
               & np.isfinite(df_reg) & np.isfinite(f_reg) & (df_reg >= lo) & (df_reg <= hi))
    DF = np.where(use_reg, df_reg, 1.0)
    F = np.where(use_reg, f_reg, st.medF.to_numpy())
    ratio = F / st.spot.to_numpy()
    rlo, rhi = cfg.forward_ratio_bounds
    fstat = np.where(n < cfg.min_parity_pairs, 1,
                     np.where((ratio < rlo) | (ratio > rhi) | ~np.isfinite(ratio), 2, 0))
    out = pd.DataFrame({"date": idx.date.to_numpy(), "expiry": idx.expiry.to_numpy(), "F": F, "DF": DF,
                        "n_pairs": n.astype(int), "regression": use_reg, "fstat": fstat.astype(np.int8)})
    return out.set_index(["date", "expiry"])


def build_otm_quotes(wide: pd.DataFrame, cfg: DataConfig):
    """Return ``(quotes, ledger, diagnostics)``; see module docstring."""
    ledger = RejectLedger()
    ledger.rows_in = len(wide)
    fw = estimate_forwards(wide, cfg)
    df = wide.join(fw[["F", "DF", "fstat"]], on=["date", "expiry"])
    F, K, S = df.F.to_numpy(), df.strike.to_numpy(), df.spot.to_numpy()
    T = (df.expiry.to_numpy() - df.date.to_numpy()) / 365.0
    fstat = df.fstat.to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        is_call = K >= F
        bid = np.where(is_call, df.c_bid, df.p_bid)
        ask = np.where(is_call, df.c_ask, df.p_ask)
        vend = np.where(is_call, df.c_iv, df.p_iv).astype(float)
        k = np.log(K / F)
        mid = 0.5 * (bid + ask)
        rel = (ask - bid) / mid
        conds = [~np.isfinite(fstat) | (fstat == 1),
                 fstat == 2,
                 ~(np.abs(k) <= cfg.max_abs_k),
                 ~((bid > 0) & (ask > 0)),
                 ask <= bid,
                 mid < cfg.min_mid,
                 rel > cfg.max_rel_spread]
    first = np.select(conds, np.arange(1, len(conds) + 1), default=0)
    for i, reason in enumerate(QUOTE_REASONS[:len(conds)], start=1):
        ledger.reject(reason, int((first == i).sum()))
    ok = first == 0

    DFv = df.DF.to_numpy()
    iv, status = bs.implied_vol(mid[ok] / DFv[ok], F[ok], K[ok], T[ok], is_call[ok])
    for code, reason in ((bs.BELOW_LOWER_BOUND, "iv_below_lower_bound"), (bs.ABOVE_UPPER_BOUND, "iv_above_upper_bound"),
                         (bs.INVALID_INPUT, "iv_invalid_input"), (bs.BELOW_SOLVER_FLOOR, "iv_below_solver_floor"),
                         (bs.ABOVE_SOLVER_CEILING, "iv_above_solver_ceiling")):
        ledger.reject(reason, int((status == code).sum()))
    in_bounds = (status == bs.OK) & (iv >= cfg.min_iv) & (iv <= cfg.max_iv)
    ledger.reject("iv_out_of_bounds", int(((status == bs.OK) & ~in_bounds).sum()))
    ledger.kept = int(in_bounds.sum())

    # per-snapshot ledger (Phase 1 A2): every row's terminal disposition, 0 = kept, else 1-based index into QUOTE_REASONS
    terminal = first.astype(int)
    solver = np.zeros(status.shape, dtype=int)
    for code, reason in ((bs.BELOW_LOWER_BOUND, "iv_below_lower_bound"), (bs.ABOVE_UPPER_BOUND, "iv_above_upper_bound"),
                         (bs.INVALID_INPUT, "iv_invalid_input"), (bs.BELOW_SOLVER_FLOOR, "iv_below_solver_floor"),
                         (bs.ABOVE_SOLVER_CEILING, "iv_above_solver_ceiling")):
        solver[status == code] = QUOTE_REASONS.index(reason) + 1
    solver[(status == bs.OK) & ~in_bounds] = QUOTE_REASONS.index("iv_out_of_bounds") + 1
    terminal[ok] = solver
    ledger.note_dates(df.date.to_numpy(), terminal, QUOTE_REASONS)

    sel = np.flatnonzero(ok)[in_bounds]
    quotes = pd.DataFrame({
        "date": df.date.to_numpy()[sel], "expiry": df.expiry.to_numpy()[sel], "T": T[sel],
        "strike": K[sel], "k": k[sel], "iv": iv[in_bounds], "is_call": is_call[sel], "mid": mid[sel],
        "rel_spread": rel[sel], "F": F[sel], "DF": DFv[sel], "spot": S[sel], "vendor_iv": vend[sel],
        # GR-QNT-03: per-quote solver residual, |model_price(iv) - undiscounted mid| / F (decimal of forward)
        "reprice_err": np.abs(bs.black76_price(F[sel], K[sel], T[sel], iv[in_bounds], is_call[sel])
                              - mid[sel] / DFv[sel]) / F[sel],
    }).sort_values(["date", "expiry", "strike"], kind="mergesort").reset_index(drop=True)
    ledger.check()

    vv = quotes.vendor_iv.to_numpy()
    good = np.isfinite(vv) & (vv > 1e-4)
    ours = quotes.iv.to_numpy()
    diag = {
        "forward_slices": int(len(fw)),
        "forward_slices_regression": int(fw.regression.sum()),
        "forward_slices_no_pairs": int((fw.fstat == 1).sum()),
        "forward_slices_implausible": int((fw.fstat == 2).sum()),
        "quotes_kept": int(len(quotes)),
        # GR-QNT-03: solver residual of kept quotes and solver-status reject counts (all non-OK statuses)
        "reprice_err_max": float(quotes.reprice_err.max()) if len(quotes) else None,
        "reprice_err_median": float(quotes.reprice_err.median()) if len(quotes) else None,
        "solver_status_rejects": {name: int((status == code).sum())
                                  for code, name in bs.STATUS_NAMES.items() if code != bs.OK},
        "vendor_iv_compared": int(good.sum()),
        # unit-agnostic: ~1.0 if the vendor IV is a decimal, ~100 if it is in percent
        "vendor_iv_median_ratio_vendor_over_ours": float(np.median(vv[good] / ours[good])) if good.any() else None,
        "vendor_iv_median_abs_diff_decimal": float(np.median(np.abs(vv[good] - ours[good]))) if good.any() else None,
    }
    return quotes, ledger, diag
