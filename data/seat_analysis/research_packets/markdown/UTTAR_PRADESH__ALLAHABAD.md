# Research packet: Allahabad, Uttar Pradesh

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Uttar Pradesh (`UTTAR PRADESH`)
- Constituency: Allahabad (`ALLAHABAD`)

## Election facts (2019 → 2024)
- Winner 2019: Rita Bahuguna Joshi
- Winner 2024: UJJWAL RAMAN SINGH
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 55.6156
- BJP vote share 2024: 42.5924
- INC vote share 2019: 3.594
- INC vote share 2024: 48.801
- BJP swing: -13.0232
- INC swing: 45.2069
- Margin 2019: 20.727
- Margin 2024: 6.2086
- Margin change: -14.5185
- Turnout 2019: 28.8116
- Turnout 2024: 25.28
- Turnout change: -3.5316

## State context
- State seats: 80
- BJP seats 2019/2024: 62 / 33
- INC seats 2019/2024: 1 / 6
- State avg BJP swing: -8.51
- State avg INC swing: 3.46
- State demographic coverage: 63.75%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: True
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;top_inc_gain
- priority_rank: 23

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 34.4627
- improved_sanitation_pct_nfhs5: 0.6544
- lpg_pct_nfhs5: 0.0
- mobile_phone_pct_nfhs5: 0.6572
- urban_pct_nfhs5: 0.0
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: ALLAHABAD→Allahabad (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: UJJWAL RAMAN SINGH
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Allahabad flipped from BJP to INC in 2024. BJP vote share changed by -13.0 points and INC vote share changed by +45.2 points compared with 2019. The 2024 margin was 6.2%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Allahabad flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -13.0 percentage points versus 2019. INC vote share changed by +45.2 percentage points versus 2019. The winning margin moved from 20.7% in 2019 to 6.2% in 2024. Turnout changed by -3.5 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Allahabad, Uttar Pradesh using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Allahabad may be analytically useful using priority reason (seat_flip;top_inc_gain), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
