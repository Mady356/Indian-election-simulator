# Research packet: Buxar, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Buxar (`BUXAR`)

## Election facts (2019 → 2024)
- Winner 2019: Ashwini Kumar Choubey
- Winner 2024: SUDHAKAR SINGH
- Party 2019: BJP
- Party 2024: RJD
- Winner changed: True
- BJP vote share 2019: 47.9351
- BJP vote share 2024: 38.021
- INC vote share 2019: None
- INC vote share 2024: None
- BJP swing: -9.9141
- INC swing: None
- Margin 2019: 11.9175
- Margin 2024: 2.8024
- Margin change: -9.1151
- Turnout 2019: 25.8588
- Turnout 2024: 22.66
- Turnout change: -3.1988

## State context
- State seats: 40
- BJP seats 2019/2024: 17 / 12
- INC seats 2019/2024: 1 / 3
- State avg BJP swing: -6.55
- State avg INC swing: 5.27
- State demographic coverage: 92.5%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: True
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 153

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 15.9773
- improved_sanitation_pct_nfhs5: 11.0166
- lpg_pct_nfhs5: 1.8225
- mobile_phone_pct_nfhs5: 1.1722
- urban_pct_nfhs5: 11.1163
- nfhs5_coverage_share: 1.0001
- change_coverage_share: 1.0001
- change_quality_flag: medium
- districts_used: BUXAR→Buxar (NFHS-4 proxy); KAIMUR (BHABUA)→Kaimur (Bhabua) (NFHS-4 proxy); ROHTAS→Rohtas (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SUDHAKAR SINGH
- winner_party_2024: RJD
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Buxar flipped from BJP to RJD in 2024. BJP vote share changed by -9.9 points compared with 2019. The 2024 margin was 2.8%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Buxar flipped from BJP to RJD between 2019 and 2024. BJP vote share changed by -9.9 percentage points versus 2019. The winning margin moved from 11.9% in 2019 to 2.8% in 2024. Turnout changed by -3.2 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Buxar, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Buxar may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
