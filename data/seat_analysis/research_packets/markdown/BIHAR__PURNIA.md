# Research packet: Purnia, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Purnia (`PURNIA`)

## Election facts (2019 → 2024)
- Winner 2019: SANTOSH KUMAR
- Winner 2024: RAJESH RANJAN ALIAS PAPPU YADAV
- Party 2019: JDU
- Party 2024: IND
- Winner changed: True
- BJP vote share 2019: None
- BJP vote share 2024: None
- INC vote share 2019: 32.0175
- INC vote share 2024: 0.0
- BJP swing: None
- INC swing: -32.0175
- Margin 2019: 22.8314
- Margin 2024: 1.9942
- Margin change: -20.8373
- Turnout 2019: 35.8534
- Turnout 2024: 29.95
- Turnout change: -5.9034

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
- is_large_inc_loss: True
- is_priority_seat: True
- priority_reason: seat_flip;top_inc_loss
- priority_rank: 51

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 100.0
- improved_sanitation_pct_nfhs5: 100.0
- lpg_pct_nfhs5: 46.0916
- mobile_phone_pct_nfhs5: 100.0
- bank_account_pct_nfhs5: 100.0
- wealth_index_mean_nfhs5: 66870.7565
- urban_pct_nfhs5: 46.0916
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: PURNIA→Purnia
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: RAJESH RANJAN ALIAS PAPPU YADAV
- winner_party_2024: IND
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Purnia flipped from JDU to IND in 2024. INC vote share changed by -32.0 points compared with 2019. The 2024 margin was 2.0%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Purnia flipped from JDU to IND between 2019 and 2024. INC vote share changed by -32.0 percentage points versus 2019. The winning margin moved from 22.8% in 2019 to 2.0% in 2024. Turnout changed by -5.9 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Purnia, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Purnia may be analytically useful using priority reason (seat_flip;top_inc_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
