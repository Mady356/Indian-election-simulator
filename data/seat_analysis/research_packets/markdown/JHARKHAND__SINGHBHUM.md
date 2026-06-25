# Research packet: Singhbhum, Jharkhand

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Jharkhand (`JHARKHAND`)
- Constituency: Singhbhum (`SINGHBHUM`)

## Election facts (2019 → 2024)
- Winner 2019: GEETA KORA
- Winner 2024: JOBA MAJHI
- Party 2019: INC
- Party 2024: JMM
- Winner changed: True
- BJP vote share 2019: 40.9016
- BJP vote share 2024: 34.911
- INC vote share 2019: 49.1073
- INC vote share 2024: 0.0
- BJP swing: -5.9907
- INC swing: -49.1073
- Margin 2019: 8.2057
- Margin 2024: 16.7132
- Margin change: 8.5075
- Turnout 2019: 34.0034
- Turnout 2024: 35.89
- Turnout change: 1.8866

## State context
- State seats: 14
- BJP seats 2019/2024: 11 / 8
- INC seats 2019/2024: 1 / 2
- State avg BJP swing: -6.86
- State avg INC swing: 4.88
- State demographic coverage: 78.57%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: True
- is_priority_seat: True
- priority_reason: seat_flip;top_inc_loss
- priority_rank: 60

## Demographic context
- data_quality_label: election_only
- nfhs5_coverage_share: None
- change_coverage_share: None
- change_quality_flag: None
- districts_used: N/A
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: JOBA MAJHI
- winner_party_2024: JMM
- data_quality_label: election_only
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Singhbhum flipped from INC to JMM in 2024. BJP vote share changed by -6.0 points and INC vote share changed by -49.1 points compared with 2019. The 2024 margin was 16.7%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Singhbhum flipped from INC to JMM between 2019 and 2024. BJP vote share changed by -6.0 percentage points versus 2019. INC vote share changed by -49.1 percentage points versus 2019. The winning margin moved from 8.2% in 2019 to 16.7% in 2024. Turnout changed by +1.9 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Singhbhum, Jharkhand using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Singhbhum may be analytically useful using priority reason (seat_flip;top_inc_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
