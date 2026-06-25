# Research packet: Tamluk, West Bengal

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: West Bengal (`WEST BENGAL`)
- Constituency: Tamluk (`TAMLUK`)

## Election facts (2019 → 2024)
- Winner 2019: Adhikari Dibyendu
- Winner 2024: ABHIJIT GANGOPADHYAY
- Party 2019: AITC
- Party 2024: BJP
- Winner changed: True
- BJP vote share 2019: 36.9352
- BJP vote share 2024: 48.537
- INC vote share 2019: 1.1062
- INC vote share 2024: 0.0
- BJP swing: 11.6018
- INC swing: -1.1062
- Margin 2019: 13.1466
- Margin 2024: 4.9282
- Margin change: -8.2184
- Turnout 2019: 42.7483
- Turnout 2024: 41.31
- Turnout change: -1.4383

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
- is_large_bjp_gain: True
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 262

## Demographic context
- data_quality_label: election_only
- nfhs5_coverage_share: 0.0
- change_coverage_share: 0.0
- change_quality_flag: medium
- districts_used: N/A
- districts_missing: PURBO MEDINIPUR

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: ABHIJIT GANGOPADHYAY
- winner_party_2024: BJP
- data_quality_label: election_only
- projection_confidence_hint: high

## Existing analysis
- analysis_source: manual
- generated summary: Tamluk flipped from AITC to BJP in 2024. BJP vote share changed by +11.6 points and INC vote share changed by -1.1 points compared with 2019. The 2024 margin was 4.9%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Tamluk flipped from AITC to BJP between 2019 and 2024. BJP vote share changed by +11.6 percentage points versus 2019. INC vote share changed by -1.1 percentage points versus 2019. The winning margin moved from 13.1% in 2019 to 4.9% in 2024. Turnout changed by -1.4 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: True
- manual note present in `manual/notes/`

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Tamluk, West Bengal using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Tamluk may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
