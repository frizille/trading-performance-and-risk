# trading-performance-and-risk

A portable, source-agnostic **Claude skill** for measuring and interpreting trading and portfolio risk. It turns a daily portfolio-value history and a trade log into two panels of metrics, each graded good / medium / poor in plain language.

## What it computes

- **NAV panel** (risk-adjusted): time-weighted return, annualized volatility, Sharpe, Sortino, Calmar, maximum drawdown.
- **Trade-quality panel**: win rate, expectancy, profit factor, average reward-to-risk — overall and by strategy type.
- **Concentration**: each position's share of the portfolio, against diversification limits.

The two panels answer different questions and stay separate by design: a trade log has no equity curve (so it can't produce risk-adjusted metrics), and buy-and-hold positions have no defined exit (so they don't belong in the trade-quality panel).

## Repository layout

```
SKILL.md                       # the skill: Configuration + workflow + report template
references/
  metric-definitions.md        # formulas, plain meaning, good/medium/poor bands
  computation-notes.md         # data sourcing, TWR method, trade-log schema, R by type
scripts/
  risk_metrics.py              # dependency-free calculator (stdlib only)
portfolio-risk-metrics.skill   # packaged, installable skill file
```

## Using it as a Claude skill

Point Claude (Claude Code, or an agent that loads skills from a repo) at this repository, or install the packaged `portfolio-risk-metrics.skill`. It triggers when you ask to measure, grade, or benchmark trading performance and risk.

**Configuration runs first.** The skill prompts for two things before computing:
1. A **portfolio data source** — the SnapTrade MCP server connected to your brokerage, or a manual export of daily account values plus cash flows.
2. Your **trade log** — a spreadsheet (Excel / CSV / Google Sheet) or other export with one row per trade.

## Using the calculator directly

The script needs only the Python standard library:

```bash
# risk-adjusted metrics from a daily value series (+ optional cash flows)
python scripts/risk_metrics.py nav --nav nav.csv --flows flows.csv --rf 0.04

# trade-quality metrics from a closed-trade log
python scripts/risk_metrics.py trades --trades trades.csv
```

CSV schemas are documented in `references/computation-notes.md` (section 7). Run either subcommand with `--help` for options.

## Note

Grading bands are general rules of thumb; what counts as "good" shifts with trading style, time window, and market conditions. The skill states its assumptions and data-quality caveats rather than hiding them.
