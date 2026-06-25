# Research packet: Jorhat, Assam

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Assam (`ASSAM`)
- Constituency: Jorhat (`JORHAT`)

## Election facts (2019 → 2024)
- Winner 2019: TOPON KUMAR GOGOI
- Winner 2024: GAURAV GOGOI
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 51.3522
- BJP vote share 2024: 43.6598
- INC vote share 2019: 43.5397
- INC vote share 2024: 54.0391
- BJP swing: -7.6923
- INC swing: 10.4994
- Margin 2019: 7.8125
- Margin 2024: 10.3793
- Margin change: 2.5669
- Turnout 2019: 39.8003
- Turnout 2024: 43.38
- Turnout change: 3.5797

## State context
- State seats: 14
- BJP seats 2019/2024: 9 / 9
- INC seats 2019/2024: 3 / 3
- State avg BJP swing: 1.62
- State avg INC swing: 0.37
- State demographic coverage: 57.14%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 193

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 10.782
- improved_sanitation_pct_nfhs5: 53.4565
- lpg_pct_nfhs5: 7.188
- mobile_phone_pct_nfhs5: 4.3128
- urban_pct_nfhs5: 15.0948
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: SIBSAGAR→Sivasagar (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: GAURAV GOGOI
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Jorhat flipped from BJP to INC in 2024. BJP vote share changed by -7.7 points and INC vote share changed by +10.5 points compared with 2019. The 2024 margin was 10.4%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Jorhat flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -7.7 percentage points versus 2019. INC vote share changed by +10.5 percentage points versus 2019. The winning margin moved from 7.8% in 2019 to 10.4% in 2024. Turnout changed by +3.6 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Jorhat, Assam using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Jorhat may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
