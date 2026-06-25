# Research packet: HISAR, Haryana

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Haryana (`HARYANA`)
- Constituency: HISAR (`HISAR`)

## Election facts (2019 → 2024)
- Winner 2019: BRIJENDRA SINGH
- Winner 2024: JAI PARKASH (J P) S/O HARIKESH
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 51.1319
- BJP vote share 2024: 43.1851
- INC vote share 2019: 15.6262
- INC vote share 2024: 48.5833
- BJP swing: -7.9467
- INC swing: 32.9571
- Margin 2019: 26.6189
- Margin 2024: 5.3982
- Margin change: -21.2207
- Turnout 2019: 36.9704
- Turnout 2024: 31.7
- Turnout change: -5.2704

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
- is_large_bjp_loss: False
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 181

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 77.3906
- improved_sanitation_pct_nfhs5: 19.6125
- lpg_pct_nfhs5: 12.3107
- mobile_phone_pct_nfhs5: 7.4582
- urban_pct_nfhs5: 45.5426
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: HISAR→Hisar (NFHS-4 proxy); JIND→Jind (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: JAI PARKASH (J P) S/O HARIKESH
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: HISAR flipped from BJP to INC in 2024. BJP vote share changed by -7.9 points and INC vote share changed by +33.0 points compared with 2019. The 2024 margin was 5.4%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates HISAR flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -7.9 percentage points versus 2019. INC vote share changed by +33.0 percentage points versus 2019. The winning margin moved from 26.6% in 2019 to 5.4% in 2024. Turnout changed by -5.3 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for HISAR, Haryana using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why HISAR may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
