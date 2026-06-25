# Research packet: SIRSA, Haryana

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Haryana (`HARYANA`)
- Constituency: SIRSA (`SIRSA`)

## Election facts (2019 → 2024)
- Winner 2019: Sunita Duggal
- Winner 2024: SELJA
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 52.162
- BJP vote share 2024: 34.3507
- INC vote share 2019: 29.5317
- INC vote share 2024: 54.1714
- BJP swing: -17.8112
- INC swing: 24.6397
- Margin 2019: 22.6302
- Margin 2024: 19.8207
- Margin change: -2.8096
- Turnout 2019: 39.6125
- Turnout 2024: 37.8
- Turnout change: -1.8125

## State context
- State seats: 10
- BJP seats 2019/2024: 10 / 5
- INC seats 2019/2024: 0 / 5
- State avg BJP swing: -11.94
- State avg INC swing: 15.1
- State demographic coverage: 80.0%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: True
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;top_bjp_loss
- priority_rank: 55

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 81.7015
- improved_sanitation_pct_nfhs5: 16.8248
- lpg_pct_nfhs5: 17.2615
- mobile_phone_pct_nfhs5: 5.8258
- urban_pct_nfhs5: 11.6523
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: SIRSA→Sirsa (NFHS-4 proxy); FATEHABAD→Fatehabad (NFHS-4 proxy); JIND→Jind (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SELJA
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: SIRSA flipped from BJP to INC in 2024. BJP vote share changed by -17.8 points and INC vote share changed by +24.6 points compared with 2019. The 2024 margin was 19.8%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates SIRSA flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -17.8 percentage points versus 2019. INC vote share changed by +24.6 percentage points versus 2019. The winning margin moved from 22.6% in 2019 to 19.8% in 2024. Turnout changed by -1.8 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for SIRSA, Haryana using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why SIRSA may be analytically useful using priority reason (seat_flip;top_bjp_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
