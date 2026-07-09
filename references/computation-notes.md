# Computation Notes: Sourcing, Schemas, and Method

Read before ingesting data. Covers where the inputs come from, the file schemas, the time-weighted-return method, risk-unit (R) definitions, and the data-quality traps that most often corrupt results.

## Contents
1. NAV panel inputs (SnapTrade + manual)
2. Time-weighted return & cash-flow neutralization
3. Trade-log schema
4. Risk unit (R) by trade type
5. Share-position risk lenses
6. Data-hygiene traps
7. Manual CSV schemas for the script

---

## 1. NAV panel inputs

The NAV panel needs a **daily portfolio-value series** and **dated external cash flows**.

**Via the SnapTrade MCP server** (preferred when connected). Typical tools:
- Account balance history → daily total value per account. Aggregate across all *invested* accounts for a whole-portfolio curve.
- Account activities, filtered to cash-flow types (contribution / withdrawal / transfer) → the dated external flows to neutralize.
- Income summary → totals for reconciliation (contributions, withdrawals, net deposits; dividends; interest; fees).
- Portfolio summary → current positions, per-name weight, and unrealized P&L for the concentration section.

Notes: balance-history values are often *estimated* daily marks; a per-account series usually covers up to ~1 year. If a tool errors on auth, prompt the user to reconnect the connector.

**Manual alternative:** a daily-value CSV plus a cash-flow CSV (schemas in §7).

**Scoping:** measure the *invested* book. Exclude pure cash-sweep/savings accounts with large in/out churn — folding them in understates volatility and muddies the return. State any exclusions in the report.

---

## 2. Time-weighted return & cash-flow neutralization

Deposits and withdrawals distort a naive start-to-end return. Neutralize them:

- Daily sub-period return: `r_t = (V_t − CF_t) / V_{t−1} − 1`, where `CF_t` = net external cash flow settled on day *t* (deposit +, withdrawal −).
- Chain-link: `TWR = Π(1 + r_t) − 1`.
- Compute volatility, Sharpe, Sortino, and drawdown on this cash-flow-adjusted return series (build a clean index from `r_t` for the drawdown).

**Internal transfers cancel.** A transfer between two accounts you are aggregating nets to zero at the portfolio level — do not treat it as an external flow. Only flows crossing the boundary of the measured book count.

**Weekends/holidays:** balance feeds often repeat the prior value on non-trading days, which injects false 0% returns and deflates volatility. Filter to trading days (weekday filter is a reasonable default).

**Anomaly check:** flag any single-day move beyond a plausible market range (e.g. >12% for a diversified book) that is *not* matched by a known cash flow — it usually signals an unrecorded transfer. Investigate before trusting it.

---

## 3. Trade-log schema

One row per trade. Column names vary by source; map the user's columns to these roles and confirm before computing:

| Role | Typical column | Notes |
| --- | --- | --- |
| Open / close date | open date, close date | for holding period |
| Status | status | open vs closed; and win/loss if the log marks it |
| Strategy type | type | e.g. cash-secured put, covered call, long call/put, spread |
| Contracts / size | contracts | |
| Premium / price | premium in, premium out | credit received / debit paid, **per share** |
| Cost basis | cost basis | for covered-call risk |
| Capital committed | capital required | collateral or debit — the denominator for return-on-capital |
| Net P&L | total profit | the trade's realized result, fully scaled (× contracts) |

**Universe:** closed trades only for the trade-quality panel (status = closed / a realized outcome). Exclude open positions and exact-$0 scratches. Exclude buy-and-hold share positions entirely — they have no defined exit.

---

## 4. Risk unit (R) by trade type

R is the initial dollar risk on a trade — the unit outcomes are measured in (P&L ÷ R = R-multiple; mean R-multiple = expectancy in R). Route each structure to the R definition that carries information; premium is per share, so multiply by 100 × contracts.

| Type | R | Notes |
| --- | --- | --- |
| Long option | net debit | max loss = premium paid |
| Debit spread | net debit | |
| Credit spread | width − net credit | loss capped by spread width |
| Cash-secured put | **managed**: (exit multiple − 1) × credit | e.g. a "close at 2× credit" rule ⇒ R = 1× credit. Structural strike-to-zero R makes premium-selling R-multiples meaninglessly small — prefer managed R or return-on-capital |
| Covered call | **managed to a stock stop**: max(0, cost basis − stop) × 100 × ct | if the stop sits above cost basis, R = 0 ("house money"). An unstopped covered call's R-multiple is weak — lean on return-on-capital instead |
| Naked short put | same as cash-secured put, margin-flagged | |
| Naked short call | no finite R | unbounded; flag, never fabricate a number |

For premium-selling styles, **return-on-capital** (`P&L / capital required`) is usually the more meaningful expectancy denominator than R-multiples.

---

## 5. Share-position risk lenses

Buy-and-hold shares get no R-multiple, but they carry risk measured three ways. Each needs the current price and one floor; the lens nearest current price is the binding one. Reward is anchored to an upside target, giving a reward:risk per lens.

| Lens | Capital-at-risk | Needs |
| --- | --- | --- |
| Valuation | (price − valuation-floor) × shares | a fundamental downside estimate (e.g. a bear-case fair value) |
| Trend stop | (price − moving average) × shares | a price-history feed to compute e.g. a 100-day moving average |
| Volatility | (k × ATR) × shares | a price-history feed for Average True Range |

**Price-feed dependency:** the trend-stop and volatility lenses need OHLC candle history. A brokerage/positions feed alone does not provide candles, and sandboxed compute environments often block market-data APIs. If no candle source is available, compute the valuation lens (if a floor is supplied) and clearly mark the other two as pending a price feed — do not fabricate moving-average or ATR values. Clamp capital-at-risk at 0 (never negative); when price is already below a floor, flag "at/through floor" instead.

---

## 6. Data-hygiene traps

- **Per-contract vs fully-scaled columns.** Some logs store premium totals per contract (× 100 only) while P&L is fully scaled (× contracts). Drive calculations off the fully-scaled P&L and capital columns; don't mix scales.
- **Long-option capital fields.** A "capital required" column is reliable for cash-secured puts and covered calls (collateral / cost basis) but is often mis-set to strike notional on long options, understating their return-on-capital. Compute long-option R from the debit, not that column.
- **Inconsistent outcome/label codes.** Normalize spacing/spelling variants (e.g. `STO/BTC` vs `STO / BTC`) before grouping. Strategy type, not outcome text, should drive routing.
- **High win rate ≠ profitable.** A premium book can post a 90% win rate and negative expectancy when a few large losses swamp many small gains — always compute profit factor and average loss, not just win rate.
- **Estimated daily values / short windows.** Balance-history marks are estimates; annualizing a sub-year window overstates forward figures. Report Calmar and annualized return with that caveat.

---

## 7. Manual CSV schemas for the script

`scripts/risk_metrics.py` reads plain CSVs (standard library only, no pandas):

**NAV series** (`--nav`): headers `date,total_value`, one row per trading day, ascending or any order (the script sorts).
```
date,total_value
2026-01-02,101250.00
2026-01-03,100980.00
```

**Cash flows** (`--flows`, optional): headers `date,amount`, deposits positive, withdrawals negative.
```
date,amount
2026-02-17,5000.00
2026-03-04,-1200.00
```

**Trade log** (`--trades`): headers `type,status,pnl,capital` at minimum (extra columns ignored). `status` open-values and win detection are configurable via flags; run `python scripts/risk_metrics.py trades --help`.
```
type,status,pnl,capital
CSP,closed,320.00,20000
CC,closed,-1850.00,41000
```
