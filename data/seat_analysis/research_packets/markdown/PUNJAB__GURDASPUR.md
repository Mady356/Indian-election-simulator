# Research packet: Gurdaspur, Punjab

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Punjab (`PUNJAB`)
- Constituency: Gurdaspur (`GURDASPUR`)

## Election facts (2019 → 2024)
- Winner 2019: SUNNY DEOL
- Winner 2024: SUKHJINDER SINGH RANDHAWA
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 50.6138
- BJP vote share 2024: 26.0879
- INC vote share 2019: 43.1439
- INC vote share 2024: 33.7757
- BJP swing: -24.5259
- INC swing: -9.3682
- Margin 2019: 7.4699
- Margin 2024: 7.6878
- Margin change: 0.2179
- Turnout 2019: 35.0232
- Turnout 2024: 22.37
- Turnout change: -12.6532

## State context
- State seats: 13
- BJP seats 2019/2024: 2 / 0
- INC seats 2019/2024: 8 / 7
- State avg BJP swing: 8.29
- State avg INC swing: -13.88
- State demographic coverage: 84.62%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: True
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;top_bjp_loss
- priority_rank: 36

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 95.5169
- improved_sanitation_pct_nfhs5: 55.1693
- lpg_pct_nfhs5: 36.5555
- mobile_phone_pct_nfhs5: 9.5606
- bank_account_pct_nfhs5: 46.6454
- wealth_index_mean_nfhs5: -8296.8619
- urban_pct_nfhs5: 19.3048
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: GURDASPUR→Gurdaspur
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SUKHJINDER SINGH RANDHAWA
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Gurdaspur flipped from BJP to INC in 2024. BJP vote share changed by -24.5 points and INC vote share changed by -9.4 points compared with 2019. The 2024 margin was 7.7%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Gurdaspur flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -24.5 percentage points versus 2019. INC vote share changed by -9.4 percentage points versus 2019. The winning margin moved from 7.5% in 2019 to 7.7% in 2024. Turnout changed by -12.7 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Gurdaspur, Punjab using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Gurdaspur may be analytically useful using priority reason (seat_flip;top_bjp_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
