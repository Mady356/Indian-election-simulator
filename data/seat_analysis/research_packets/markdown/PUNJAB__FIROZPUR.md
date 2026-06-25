# Research packet: Firozpur, Punjab

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Punjab (`PUNJAB`)
- Constituency: Firozpur (`FIROZPUR`)

## Election facts (2019 → 2024)
- Winner 2019: SUKHBIR SINGH BADAL
- Winner 2024: SHER SINGH GHUBAYA
- Party 2019: SAD
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 0.0
- BJP vote share 2024: 22.673
- INC vote share 2019: 37.0789
- INC vote share 2024: 23.6977
- BJP swing: 22.673
- INC swing: -13.3812
- Margin 2019: 16.9662
- Margin 2024: 0.2881
- Margin change: -16.6781
- Turnout 2019: 39.1386
- Turnout 2024: 15.92
- Turnout change: -23.2186

## State context
- State seats: 13
- BJP seats 2019/2024: 2 / 0
- INC seats 2019/2024: 8 / 7
- State avg BJP swing: 8.29
- State avg INC swing: -13.88
- State demographic coverage: 84.62%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: True
- is_large_bjp_gain: True
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: True
- is_priority_seat: True
- priority_reason: seat_flip;closest_2024
- priority_rank: 16

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 96.5626
- improved_sanitation_pct_nfhs5: 57.8504
- lpg_pct_nfhs5: 35.9905
- mobile_phone_pct_nfhs5: 19.0703
- urban_pct_nfhs5: 34.006
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: FIROZPUR→Firozpur (NFHS-4 proxy); MUKTSAR→Muktsar (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SHER SINGH GHUBAYA
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Firozpur flipped from SAD to INC in 2024. BJP vote share changed by +22.7 points and INC vote share changed by -13.4 points compared with 2019. The 2024 margin was 0.3%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Firozpur flipped from SAD to INC between 2019 and 2024. BJP vote share changed by +22.7 percentage points versus 2019. INC vote share changed by -13.4 percentage points versus 2019. The winning margin moved from 17.0% in 2019 to 0.3% in 2024. Turnout changed by -23.2 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Firozpur, Punjab using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Firozpur may be analytically useful using priority reason (seat_flip;closest_2024), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
