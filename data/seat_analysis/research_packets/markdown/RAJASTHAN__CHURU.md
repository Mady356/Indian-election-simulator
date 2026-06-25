# Research packet: CHURU, Rajasthan

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Rajasthan (`RAJASTHAN`)
- Constituency: CHURU (`CHURU`)

## Election facts (2019 → 2024)
- Winner 2019: RAHUL KASWAN
- Winner 2024: RAHUL KASWAN
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 59.6948
- BJP vote share 2024: 46.0096
- INC vote share 2019: 34.5219
- INC vote share 2024: 51.1153
- BJP swing: -13.6852
- INC swing: 16.5933
- Margin 2019: 25.1729
- Margin 2024: 5.1056
- Margin change: -20.0673
- Turnout 2019: 39.2748
- Turnout 2024: 32.77
- Turnout change: -6.5048

## State context
- State seats: 25
- BJP seats 2019/2024: 24 / 14
- INC seats 2019/2024: 0 / 8
- State avg BJP swing: -8.68
- State avg INC swing: 4.08
- State demographic coverage: 44.0%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: True
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 155

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 80.0
- improved_sanitation_pct_nfhs5: 20.0
- lpg_pct_nfhs5: 0.0
- mobile_phone_pct_nfhs5: 0.0
- bank_account_pct_nfhs5: 20.0
- wealth_index_mean_nfhs5: -64227.4
- urban_pct_nfhs5: 0.0
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: HANUMANGARH→Hanumangarh
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: RAHUL KASWAN
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: CHURU flipped from BJP to INC in 2024. BJP vote share changed by -13.7 points and INC vote share changed by +16.6 points compared with 2019. The 2024 margin was 5.1%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates CHURU flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -13.7 percentage points versus 2019. INC vote share changed by +16.6 percentage points versus 2019. The winning margin moved from 25.2% in 2019 to 5.1% in 2024. Turnout changed by -6.5 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for CHURU, Rajasthan using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why CHURU may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
