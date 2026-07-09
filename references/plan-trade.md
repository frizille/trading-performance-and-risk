# Pre-Trade Risk Planner (`plan-trade`)

Forward-looking sizing for one prospective trade. The goal is a single honest number — the loss you will actually take if you are wrong, defined *before* entry — plus how that loss sits against the whole account. This is not a recommendation to place the trade.

## 1. Parse the command

The user invokes `plan-trade <ticker> [strike] [strategy] [exp ...] [other]`. Parse whatever is present.

Example: `plan-trade NBIS $240 CC exp 7/17` → ticker **NBIS**, strike **$240**, strategy **covered call**, expiry **7/17**. Missing pieces (contracts, cost basis, credit, stop) are gathered in step 3.

## 2. Confirm the strategy

If strategy is absent or ambiguous, ask the user to choose one:

- **CC** — covered call
- **CSP** — cash-secured put
- **LC** — long call
- **LP** — long put
- **Buy-and-hold** — long shares, no fixed exit date
- **Swing trade** — short-term directional (shares or option) with a planned stop and target
- **0DTE** — options expiring the same day

## 3. Gather strategy-specific inputs and compute R

Ask only for what was not already provided. Premium is per share, so multiply by 100 × contracts. "Defined risk (R)" is the loss you have pre-committed to take.

| Strategy | Inputs to collect | Defined risk R | Breakeven | Max profit |
| --- | --- | --- | --- | --- |
| **CSP** | strike, expiry, contracts, credit received, underlying price, exit rule (default: close at 2× credit) | (exit multiple − 1) × credit × 100 × ct  — default = 1× credit × 100 × ct. Collateral = strike × 100 × ct | strike − credit | credit × 100 × ct |
| **CC** | call strike, expiry, contracts (= shares ÷ 100), share cost basis, credit received, **stock stop** (price you'd exit the shares) | max(0, cost basis − stop) × 100 × ct. Risk is the *stock*, not the call | cost basis − credit (on the shares) | (strike − cost basis + credit) × 100 × ct if called away |
| **LC** | strike, expiry, contracts, debit paid, underlying price, optional target | debit × 100 × ct (max loss = premium) | strike + debit | unbounded; if target given, (target − strike − debit) × 100 × ct |
| **LP** | strike, expiry, contracts, debit paid, underlying price, optional target | debit × 100 × ct | strike − debit | (strike − debit) × 100 × ct (stock → 0) |
| **Buy-and-hold** | shares, entry price, downside floor (stop / bear-case value / moving average), optional target | (entry − floor) × shares | n/a | open-ended; if target given, (target − entry) × shares |
| **Swing trade** | instrument (shares or option), entry, **stop**, target, size, horizon | shares: (entry − stop) × shares · long option: debit × 100 × ct · defined-risk spread: (width − credit) × 100 × ct | per instrument | (target − entry) × shares, or the option payoff |
| **0DTE** | exact structure (long option / debit spread / credit spread / short naked), strike(s), debit or credit, contracts, **hard stop** | long option or debit spread: debit × 100 × ct · credit spread: (width − credit) × 100 × ct · **short naked: no defined max — require a stop and flag as high-risk** | per structure | per structure |

**Notes on the trickier ones:**
- **CC** — if the user has no stock stop, fall back to the structural downside (cost basis − credit) × 100 × ct and label it plainly as long-stock risk (an uncapped covered call's real risk is the stock going down, not the call).
- **CSP** — the strike-to-zero max loss is (strike − credit) × 100 × ct; report it as the tail case, but use the managed R (from the exit rule) as the working risk.
- **0DTE** — same-day expiry leaves no time to recover, so a hard stop or a defined-risk structure is essential; treat 0DTE risk as elevated regardless of the computed number, and refuse to report a finite R for a short naked leg without a stop.

## 4. Establish account context

- **Total account value (NAV)** — from the connected data source if available, otherwise ask.
- **Current exposure to this underlying** (existing shares + options) — from positions if available, otherwise ask. Needed for the concentration-after-trade check.

## 5. Compute, grade, and report

Convert R to a percent of NAV and grade it against the position-sizing rule (roughly 0.5–2% of the account per trade). Compute reward-to-risk, capital / buying power required, and what the position becomes as a share of NAV after the trade.

### Output template

```
plan-trade — [TICKER] [strike] [strategy] exp [date]

Inputs:        [the collected values]
Defined risk (R):   $[amount]   ([how R was defined])
Breakeven:     [price]
Max profit:    $[amount or "open-ended"]
Reward:risk:   [X : 1]
R as % of account:  [X%]   (rule 0.5–2% → good / over)
Capital / buying power:  $[amount]
Concentration after trade:  [X% of NAV]   (vs limit)
Flags:         [undefined risk / no stop set / earnings before expiry / concentration breach / none]

Read: [1–2 plain sentences on whether the size and defined loss are sensible]
```

Close every plan-trade with a one-line reminder: **this sizes and defines the risk; it does not judge whether the trade is a good idea.**
