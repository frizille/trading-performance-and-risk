---
name: portfolio-risk-metrics
description: Compute and interpret portfolio risk and performance metrics — time-weighted return, volatility, Sharpe, Sortino, Calmar, maximum drawdown, win rate, profit factor, expectancy, reward-to-risk, and position concentration — from a brokerage data source and a trade log, then grade each result as good, medium, or poor. Use this skill whenever the user wants to measure, interpret, or benchmark trading or investment performance and risk — for example asking how risky a portfolio is, what their Sharpe or drawdown or win rate is, to grade a track record, to analyze a trade log, or whether they are in the right risk zone — even if no specific metric is named. Always run the Configuration steps first (connect the data source and obtain the trade log) before computing anything.
---

# Portfolio Risk & Performance Metrics

This skill turns a portfolio's daily value history and a trade log into two panels of metrics and a plain-English grade for each. It is source-agnostic: data can come from a connected brokerage (via the SnapTrade MCP server) or from user-provided files.

The metrics split into two families that answer different questions and need different inputs:

- **NAV panel** (risk-adjusted / path metrics): time-weighted return, annualized volatility, Sharpe, Sortino, Calmar, maximum drawdown. Needs a **daily portfolio-value series** plus **dated cash flows**.
- **Trade-quality panel**: win rate, expectancy, profit factor, average reward-to-risk. Needs a **closed-trade log**.

Keep them separate. A trade log cannot produce risk-adjusted metrics (it has no equity curve), and buy-and-hold positions do not belong in the trade-quality panel (they have no defined exit). Mixing them is the most common error this skill exists to prevent.

---

## Configuration — do this first, before any computation

Confirm both prerequisites with the user at the outset. Do not compute anything until each is resolved or explicitly waived.

### 1. Portfolio data source (for the NAV panel + concentration)

Ask the user:

> "To measure risk-adjusted return and drawdown, I need your daily portfolio value history. The cleanest source is the **SnapTrade MCP server** connected to your brokerage. Is SnapTrade already connected? If not, you can connect it in your connector/integration settings — or, if you'd rather not, give me an export of daily account values plus any deposits/withdrawals."

Then:
- **Check the available tools** for a SnapTrade connector (tool names beginning `Snaptrade:` or similar — e.g. account balance history, portfolio summary, activities). If present, use it.
- **If not present**, prompt the user to connect the SnapTrade MCP server, or to provide a daily-value file. Do not fabricate or estimate a value series.
- Accept a manual alternative: a CSV of `date, total_value` plus a CSV of `date, amount` cash flows. See `references/computation-notes.md` for the schemas.

### 2. Trade log (for the trade-quality panel)

Ask the user:

> "For win rate, expectancy, profit factor, and reward-to-risk, I need your **trade log** — a spreadsheet (Excel, CSV, or Google Sheet) or any export with one row per trade. It should include open/close dates, instrument type, contracts/size, premium or price in and out, net P&L, and (ideally) the capital committed per trade."

Then:
- Accept a spreadsheet, CSV, Google Sheet, or a broker transaction export. If the trade detail lives on a specific tab, ask which one.
- Confirm the column mapping against the schema in `references/computation-notes.md` before trusting it. Flag anything missing rather than guessing.

Only after both are settled, proceed to the workflow.

---

## Workflow

1. **Configuration** (above) — data source + trade log.
2. **NAV panel.** Assemble the daily portfolio-value series and the dated cash flows. Compute a time-weighted return (cash flows neutralized), annualized volatility, Sharpe, Sortino, Calmar, and maximum drawdown. Use `scripts/risk_metrics.py nav` for the arithmetic. See `references/computation-notes.md` for sourcing and the cash-flow method.
3. **Trade-quality panel.** Ingest the closed-trade log. Compute win rate, expectancy, profit factor, average winner/loser, and reward-to-risk — overall and per strategy type. Assign each trade its risk unit (R) per `references/computation-notes.md`. Use `scripts/risk_metrics.py trades`.
4. **Concentration.** From current positions, report each holding's share of NAV and flag any that breach the user's diversification limits (ask for their limits; a common default ladder is 20 / 25 / 35% of NAV).
5. **Grade and report.** For every metric, attach a good / medium / poor reading from `references/metric-definitions.md`, and write the report using the template below.

---

## Locked conventions (override only on user request)

- **Return:** daily time-weighted (TWR); report both the period figure and, cautiously, an annualized one.
- **Annualization:** daily metrics × √252.
- **Sharpe:** excess over a short risk-free rate (e.g. 3-month T-bill); note that when volatility is very high the rate barely moves the result.
- **Sortino:** minimum acceptable return (MAR) = 0%.
- **Maximum drawdown:** largest peak-to-trough on the daily (cash-flow-adjusted) equity curve.
- **Calmar:** annualized return ÷ |max drawdown|; treat as unstable on windows under ~1 year.
- **Trade panel:** closed trades only; exact-$0 P&L is a scratch and is excluded; buy-and-hold positions excluded.

---

## Report structure

Use this template:

```
# Portfolio Risk & Performance — [date]
Scope: [accounts / window / what's included and excluded]

## NAV / risk-adjusted panel
| Metric | Value | Reading (good/medium/poor) |
(TWR, annualized vol, Sharpe, Sortino, Calmar, max drawdown)

## Trade-quality panel (closed trades)
| Bucket | n | Win% | Expectancy | Profit factor | Avg R:R | Total P&L |
(overall + by strategy type)

## Concentration
| Position | % of NAV | vs limit | Unrealized P&L |

## Read
- 2–4 plain sentences: where the risk lives, what's healthy, what's outside range.

## Data notes
- Cash-flow adjustments, excluded accounts, estimated values, missing inputs, and any metric that could not be computed and why.
```

Keep the tone factual. State assumptions and any data-quality issues plainly rather than papering over them.

---

## Reference files

- `references/metric-definitions.md` — every metric: plain meaning, formula, and good / medium / poor bands, with an illustrative strong-track-record benchmark. Read this to grade results and explain them.
- `references/computation-notes.md` — data sourcing (SnapTrade fields and the manual-file schemas), the time-weighted-return and cash-flow method, the trade-log schema, risk-unit (R) definitions by trade type, the share-position risk lenses, and common data-hygiene traps. Read this before ingesting data.
- `scripts/risk_metrics.py` — dependency-free (Python standard library only) calculator with two subcommands, `nav` and `trades`. Run `python scripts/risk_metrics.py --help`.
