# Research packet: SIKAR, Rajasthan

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Rajasthan (`RAJASTHAN`)
- Constituency: SIKAR (`SIKAR`)

## Election facts (2019 → 2024)
- Winner 2019: Sumedhanand Saraswati
- Winner 2024: AMRARAM
- Party 2019: BJP
- Party 2024: CPIM
- Winner changed: True
- BJP vote share 2019: 58.1855
- BJP vote share 2024: 45.0783
- INC vote share 2019: 35.7919
- INC vote share 2024: 0.0
- BJP swing: -13.1072
- INC swing: -35.7919
- Margin 2019: 22.3936
- Margin 2024: 5.6037
- Margin change: -16.7899
- Turnout 2019: 37.8184
- Turnout 2024: 29.53
- Turnout change: -8.2884

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
- is_large_inc_loss: True
- is_priority_seat: True
- priority_reason: seat_flip;top_inc_loss
- priority_rank: 54

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 80.7243
- improved_sanitation_pct_nfhs5: 40.3621
- lpg_pct_nfhs5: 21.0864
- mobile_phone_pct_nfhs5: 21.0864
- bank_account_pct_nfhs5: 38.5514
- wealth_index_mean_nfhs5: -38478.2559
- urban_pct_nfhs5: 42.1729
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: SIKAR→Sikar
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: AMRARAM
- winner_party_2024: CPIM
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: SIKAR flipped from BJP to CPIM in 2024. BJP vote share changed by -13.1 points and INC vote share changed by -35.8 points compared with 2019. The 2024 margin was 5.6%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates SIKAR flipped from BJP to CPIM between 2019 and 2024. BJP vote share changed by -13.1 percentage points versus 2019. INC vote share changed by -35.8 percentage points versus 2019. The winning margin moved from 22.4% in 2019 to 5.6% in 2024. Turnout changed by -8.3 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for SIKAR, Rajasthan using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why SIKAR may be analytically useful using priority reason (seat_flip;top_inc_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
