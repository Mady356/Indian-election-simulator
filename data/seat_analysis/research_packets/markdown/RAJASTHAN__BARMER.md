# Research packet: BARMER, Rajasthan

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Rajasthan (`RAJASTHAN`)
- Constituency: BARMER (`BARMER`)

## Election facts (2019 → 2024)
- Winner 2019: KAILASH CHOUDHARY
- Winner 2024: UMMEDA RAM BENIWAL
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 59.5193
- BJP vote share 2024: 16.986
- INC vote share 2019: 36.7523
- INC vote share 2024: 41.7449
- BJP swing: -42.5333
- INC swing: 4.9926
- Margin 2019: 22.767
- Margin 2024: 7.0007
- Margin change: -15.7662
- Turnout 2019: 43.6077
- Turnout 2024: 31.91
- Turnout change: -11.6977

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
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;top_bjp_loss
- priority_rank: 26

## Demographic context
- data_quality_label: election_only
- nfhs5_coverage_share: None
- change_coverage_share: None
- change_quality_flag: None
- districts_used: N/A
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: UMMEDA RAM BENIWAL
- winner_party_2024: INC
- data_quality_label: election_only
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: BARMER flipped from BJP to INC in 2024. BJP vote share changed by -42.5 points and INC vote share changed by +5.0 points compared with 2019. The 2024 margin was 7.0%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates BARMER flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -42.5 percentage points versus 2019. INC vote share changed by +5.0 percentage points versus 2019. The winning margin moved from 22.8% in 2019 to 7.0% in 2024. Turnout changed by -11.7 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for BARMER, Rajasthan using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why BARMER may be analytically useful using priority reason (seat_flip;top_bjp_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
