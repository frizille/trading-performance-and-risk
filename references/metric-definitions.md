# Metric Definitions & Grading Bands

Plain meaning, formula, and good / medium / poor bands for every metric this skill reports. Bands are general rules of thumb — they shift with trading style, time window, and market conditions, so present them as guides, not laws.

The **illustrative benchmark** column describes what a strong, well-controlled discretionary track record can look like over a favorable half-year. It is an example for calibration only, not a target or a guarantee.

---

## The framing

Return says how far the account traveled. The risk metrics describe how rough the ride was. A strong record reaches a good return without large swings or deep drops. Most metrics below exist to measure the ride, because return alone hides it.

---

## NAV panel

### Time-weighted return (TWR)
- **Meaning:** how much the investments grew, in percent, with deposits and withdrawals removed so the figure reflects performance rather than funding.
- **Formula:** chain-link daily sub-period returns `r_t = (V_t − CF_t) / V_{t−1} − 1`, then `TWR = Π(1 + r_t) − 1`. `CF_t` is the external cash flow on day *t*.
- **Bands:** benchmark-relative, not absolute. Long-run broad-market average is ~10%/yr. Above ~10%/yr = good; ~10%/yr = average; near zero or negative = poor. A high return paired with a rough ride is not automatically good — the ratios below test that.
- **Illustrative benchmark:** ~+40% over six months in a strong run.

### Annualized volatility
- **Meaning:** how much the account value swings day to day, scaled to a year — the bumpiness of the ride.
- **Formula:** `stdev(daily returns) × √252`.
- **Bands (whole portfolio):** under 15% = low · 15–30% = medium · 30–50% = high · over ~50% = very high (behaves like a single volatile stock).

### Maximum drawdown
- **Meaning:** the worst peak-to-trough drop — the largest loss you would have felt buying the top and holding to the bottom.
- **Formula:** `min_t ( V_t / running_max(V) − 1 )` on the cash-flow-adjusted equity curve.
- **Bands (closer to zero is better):** under 10% = low · 10–25% = medium · 25–35% = high · over ~35% = severe.
- **Illustrative benchmark:** under −10%.

### Sharpe ratio
- **Meaning:** reward per unit of bumpiness — how much return you earned for the swings endured.
- **Formula:** `(mean daily return − rf_daily) / stdev(daily returns) × √252`.
- **Bands:** below 1 = weak · 1–2 = acceptable · 2–3 = good · above 3 = excellent.
- **Illustrative benchmark:** ~2.5 (good).

### Sortino ratio
- **Meaning:** like Sharpe but counts only downside swings — upside volatility is not penalized. Rewards records that avoid painful losses; usually higher than Sharpe.
- **Formula:** `(mean daily return − MAR) / downside_deviation × √252`, MAR = 0. `downside_deviation = √(mean(min(0, r_t − MAR)²))`.
- **Bands:** below 1 = weak · 1–3 = fair to good · above 3 = very good.
- **Illustrative benchmark:** ~6 (very strong — small, rare losing days).

### Calmar ratio
- **Meaning:** annual return per unit of worst pain.
- **Formula:** `annualized return ÷ |maximum drawdown|`.
- **Bands:** below 1 = weak · 1–3 = acceptable · 3–5 = good · above 5 = excellent. Unstable on windows under ~1 year — read loosely.
- **Illustrative benchmark:** ~15 (driven mostly by a very small drawdown).

---

## Trade-quality panel

### Win rate
- **Meaning:** share of closed trades that made money.
- **Formula:** `winners / closed trades` (exclude scratches).
- **Bands:** NO universal good number — the most misread metric. Depends on style: a "let winners run" style often wins 40–55% and profits; a premium-collection style can win 85–90% and still lose money if the rare losses are large. Always read alongside reward-to-risk.
- **Illustrative benchmark:** ~54% (for a directional style).

### Reward-to-risk (R:R)
- **Meaning:** average winner size vs average loser size.
- **Formula (realized):** `average winning trade / |average losing trade|`.
- **Interplay:** above 1 (winners bigger) means you can win under half your trades and still profit; below 1 needs a very high win rate to survive.
- **Bands:** above 1.5 = healthy for a let-winners-run style · ~1 = neutral · below 1 = only safe with a very high win rate.
- **Illustrative benchmark:** ~1.8 : 1.

### Profit factor
- **Meaning:** total money won ÷ total money lost.
- **Formula:** `gross profit / |gross loss|`.
- **Bands:** below 1 = losing · 1–1.5 = marginal · 1.5–2 = good · above 2 = very good.
- **Illustrative benchmark:** ~1.8 (good).

### Expectancy
- **Meaning:** the average result of a single trade.
- **Formula:** `mean(P&L per closed trade)` — or, in normalized form, mean of `P&L / R` (R-multiples) or `P&L / capital` (ROC).
- **Bands:** the firm rule is that it must be positive. Size depends on the denominator, so compare to the account's own history rather than a fixed line.
- **Illustrative benchmark:** ~+0.6% per trade.

---

## Concentration (position risk)
- **Meaning:** how much of the portfolio sits in one position. Concentration does not appear in return — it shows up as higher volatility and deeper drawdowns.
- **Formula:** `position value / total portfolio value`.
- **Bands (one position as a share of NAV):** under 5–10% = low · 10–20% = medium · over 20% = high · over 30% = very concentrated. If the user has explicit diversification limits, grade against those instead.

---

## Quick grading table

| Metric | Good | Medium | Poor |
| --- | --- | --- | --- |
| TWR (annualized) | above ~10%/yr | ~10%/yr | near 0 / negative |
| Volatility (annual) | under 15% | 15–30% | over 30% |
| Max drawdown | under 10% | 10–25% | over 25% |
| Sharpe | above 2 | 1–2 | below 1 |
| Sortino | above 3 | 1–3 | below 1 |
| Calmar | above 5 | 1–5 | below 1 |
| Win rate | read with R:R — no universal band | | |
| Reward-to-risk | above 1.5 | ~1 | below 1 |
| Profit factor | above 2 | 1–2 | below 1 |
| Expectancy | positive | near zero | negative |
| Concentration (one name) | under 10% | 10–20% | over 20% |
