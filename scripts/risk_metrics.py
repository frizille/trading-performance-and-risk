#!/usr/bin/env python3
"""Portfolio risk & performance metrics — Python standard library only (no pandas).

Subcommands:
  nav     Return + risk-adjusted metrics from a daily portfolio-value series.
  trades  Trade-quality metrics from a closed-trade log.

CSV schemas are documented in references/computation-notes.md (section 7).

Examples:
  python risk_metrics.py nav --nav nav.csv --flows flows.csv --rf 0.04
  python risk_metrics.py trades --trades trades.csv --type-col type --pnl-col pnl
"""
import argparse, csv, math, datetime as dt
from statistics import mean, pstdev


def _read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _parse_date(s):
    return dt.date.fromisoformat(str(s).strip()[:10])


def _num(x):
    try:
        return float(str(x).replace(",", "").replace("$", "").strip())
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------- NAV panel
def nav_metrics(a):
    rows = _read_csv(a.nav)
    series = []
    for r in rows:
        v = _num(r.get(a.value_col))
        if v is not None:
            series.append((_parse_date(r[a.date_col]), v))
    series.sort()
    if a.weekdays_only:
        series = [(d, v) for d, v in series if d.weekday() < 5]
    if not series or len(series) < 3:
        raise SystemExit("Need at least 3 dated values in the NAV series.")

    flows = {}
    if a.flows:
        for r in _read_csv(a.flows):
            d = _parse_date(r[a.flow_date_col])
            flows[d] = flows.get(d, 0.0) + (_num(r[a.flow_amount_col]) or 0.0)

    dates = [d for d, _ in series]
    vals = [v for _, v in series]
    rets, flagged = [], []
    for i in range(1, len(vals)):
        cf = flows.get(dates[i], 0.0)
        r = (vals[i] - cf) / vals[i - 1] - 1
        if a.anomaly_pct and abs(r) > a.anomaly_pct and dates[i] not in flows:
            flagged.append((dates[i], r))
            if a.drop_anomalies:
                continue
        rets.append(r)

    P = a.periods
    m, sd = mean(rets), pstdev(rets)
    twr = 1.0
    for r in rets:
        twr *= (1 + r)
    twr -= 1
    ann_ret = (1 + m) ** P - 1
    ann_vol = sd * math.sqrt(P)
    rf_daily = (1 + a.rf) ** (1 / P) - 1
    sharpe = (m - rf_daily) / sd * math.sqrt(P) if sd > 0 else float("nan")
    dd_dev = math.sqrt(sum(min(0.0, r) ** 2 for r in rets) / len(rets))
    sortino = m / dd_dev * math.sqrt(P) if dd_dev > 0 else float("nan")
    idx, peak, mdd = 1.0, 1.0, 0.0
    for r in rets:
        idx *= (1 + r)
        peak = max(peak, idx)
        mdd = min(mdd, idx / peak - 1)
    calmar = ann_ret / abs(mdd) if mdd < 0 else float("nan")
    naive = vals[-1] / vals[0] - 1

    print(f"NAV panel  {dates[0]} -> {dates[-1]}  ({len(rets)+1} points)")
    print(f"  naive point-to-point : {naive*100:+.1f}%")
    print(f"  time-weighted return : {twr*100:+.1f}%")
    print(f"  annualized return    : {ann_ret*100:+.1f}%   (unstable on <1yr)")
    print(f"  annualized vol       : {ann_vol*100:.1f}%")
    print(f"  Sharpe (rf={a.rf:.2%})    : {sharpe:.2f}")
    print(f"  Sortino (MAR=0)      : {sortino:.2f}")
    print(f"  max drawdown         : {mdd*100:.1f}%")
    print(f"  Calmar               : {calmar:.2f}")
    if flagged:
        tag = "dropped" if a.drop_anomalies else "kept"
        print(f"  anomaly days ({tag}, |r|>{a.anomaly_pct:.0%}, no matching flow): {len(flagged)}")
        for d, r in flagged:
            print(f"     {d} {r*100:+.1f}%")


# --------------------------------------------------------- Trade-quality panel
def trade_metrics(a):
    rows = _read_csv(a.trades)
    open_vals = {v.strip().lower() for v in a.open_values.split(",") if v.strip()}
    closed = []
    for r in rows:
        pnl = _num(r.get(a.pnl_col))
        if pnl is None:
            continue
        status = str(r.get(a.status_col, "")).strip().lower()
        if a.status_col in r and status in open_vals:
            continue
        if pnl == 0:  # scratch excluded
            continue
        closed.append((str(r.get(a.type_col, "ALL")).strip() or "ALL", pnl,
                       _num(r.get(a.capital_col)) if a.capital_col else None))

    if not closed:
        raise SystemExit("No closed, non-scratch trades found. Check --status-col / --pnl-col.")

    def stats(sample):
        pnls = [p for _, p, _ in sample]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gw, gl = sum(wins), sum(losses)
        caps = [c for _, _, c in sample if c]
        pnl_with_cap = sum(p for _, p, c in sample if c)
        return {
            "n": len(pnls),
            "win": len(wins) / len(pnls) * 100,
            "exp": sum(pnls) / len(pnls),
            "pf": (gw / abs(gl)) if gl else float("inf"),
            "aw": (gw / len(wins)) if wins else 0.0,
            "al": (gl / len(losses)) if losses else 0.0,
            "rr": ((gw / len(wins)) / abs(gl / len(losses))) if wins and losses else float("inf"),
            "total": sum(pnls),
            "roc": (pnl_with_cap / sum(caps) * 100) if caps else None,
        }

    buckets = {"ALL": closed}
    for t, p, c in closed:
        buckets.setdefault(t, []).append((t, p, c))

    hdr = f"{'bucket':<14}{'n':>5}{'win%':>7}{'exp$':>10}{'PF':>7}{'avgW':>9}{'avgL':>10}{'R:R':>7}{'ROC%':>7}{'total$':>12}"
    print(hdr)
    print("-" * len(hdr))
    order = ["ALL"] + sorted(k for k in buckets if k != "ALL")
    for k in order:
        s = stats(buckets[k])
        pf = f"{s['pf']:.2f}" if s["pf"] != float("inf") else "inf"
        rr = f"{s['rr']:.2f}" if s["rr"] != float("inf") else "inf"
        roc = f"{s['roc']:.2f}" if s["roc"] is not None else "-"
        print(f"{k:<14}{s['n']:>5}{s['win']:>6.1f}{s['exp']:>10.0f}{pf:>7}"
              f"{s['aw']:>9.0f}{s['al']:>10.0f}{rr:>7}{roc:>7}{s['total']:>12,.0f}")
    print("\nReminder: read win% together with R:R — a high win rate can hide negative expectancy.")


def main():
    ap = argparse.ArgumentParser(description="Portfolio risk & performance metrics (stdlib only).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("nav", help="risk-adjusted metrics from a daily value series")
    n.add_argument("--nav", required=True, help="CSV with date,total_value")
    n.add_argument("--flows", help="optional CSV with date,amount (deposit +, withdrawal -)")
    n.add_argument("--date-col", default="date")
    n.add_argument("--value-col", default="total_value")
    n.add_argument("--flow-date-col", default="date")
    n.add_argument("--flow-amount-col", default="amount")
    n.add_argument("--rf", type=float, default=0.04, help="annual risk-free rate (default 0.04)")
    n.add_argument("--periods", type=int, default=252, help="periods/yr for annualization (default 252)")
    n.add_argument("--weekdays-only", action="store_true", default=True)
    n.add_argument("--anomaly-pct", type=float, default=0.12,
                   help="flag daily moves beyond this with no matching flow (default 0.12)")
    n.add_argument("--drop-anomalies", action="store_true",
                   help="exclude flagged anomaly days from the return series")
    n.set_defaults(func=nav_metrics)

    t = sub.add_parser("trades", help="trade-quality metrics from a closed-trade log")
    t.add_argument("--trades", required=True, help="CSV trade log")
    t.add_argument("--type-col", default="type")
    t.add_argument("--status-col", default="status")
    t.add_argument("--pnl-col", default="pnl")
    t.add_argument("--capital-col", default="capital", help="capital committed per trade (for ROC); optional")
    t.add_argument("--open-values", default="open,pending",
                   help="comma-separated status values that mean 'not closed'")
    t.set_defaults(func=trade_metrics)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
