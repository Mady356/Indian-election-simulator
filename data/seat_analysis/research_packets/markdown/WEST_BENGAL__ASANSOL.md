# Research packet: Asansol, West Bengal

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: West Bengal (`WEST BENGAL`)
- Constituency: Asansol (`ASANSOL`)

## Election facts (2019 → 2024)
- Winner 2019: BABUL SUPRIYO
- Winner 2024: SHATRUGHAN PRASAD SINHA
- Party 2019: BJP
- Party 2024: AITC
- Winner changed: True
- BJP vote share 2019: 51.1558
- BJP vote share 2024: 41.9565
- INC vote share 2019: 1.6992
- INC vote share 2024: 0.0
- BJP swing: -9.1993
- INC swing: -1.6992
- Margin 2019: 15.9625
- Margin 2024: 4.5764
- Margin change: -11.3861
- Turnout 2019: 39.1975
- Turnout 2024: 34.18
- Turnout change: -5.0175

## State context
- State seats: 42
- BJP seats 2019/2024: 18 / 12
- INC seats 2019/2024: 2 / 1
- State avg BJP swing: -1.48
- State avg INC swing: -0.85
- State demographic coverage: 64.29%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: True
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;major_constituency
- priority_rank: 80

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 17.9103
- improved_sanitation_pct_nfhs5: 38.0516
- lpg_pct_nfhs5: 5.7201
- mobile_phone_pct_nfhs5: 1.0733
- urban_pct_nfhs5: 8.5868
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: BARDHAMAN→Barddhaman (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SHATRUGHAN PRASAD SINHA
- winner_party_2024: AITC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: mixed
- generated summary: Asansol flipped from BJP to AITC in 2024. BJP vote share changed by -9.2 points and INC vote share changed by -1.7 points compared with 2019. The 2024 margin was 4.6%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Asansol flipped from BJP to AITC between 2019 and 2024. BJP vote share changed by -9.2 percentage points versus 2019. INC vote share changed by -1.7 percentage points versus 2019. The winning margin moved from 16.0% in 2019 to 4.6% in 2024. Turnout changed by -5.0 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Asansol, West Bengal using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Asansol may be analytically useful using priority reason (seat_flip;major_constituency), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
