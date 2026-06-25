# Research packet: Sheohar, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Sheohar (`SHEOHAR`)

## Election facts (2019 → 2024)
- Winner 2019: RAMA DEVI
- Winner 2024: LOVELY ANAND
- Party 2019: BJP
- Party 2024: JDU
- Winner changed: True
- BJP vote share 2019: 60.5916
- BJP vote share 2024: 0.0
- INC vote share 2019: None
- INC vote share 2024: None
- BJP swing: -60.5916
- INC swing: None
- Margin 2019: 33.8815
- Margin 2024: 2.7608
- Margin change: -31.1207
- Turnout 2019: 36.0973
- Turnout 2024: 25.98
- Turnout change: -10.1173

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
- is_large_bjp_loss: True
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;top_bjp_loss
- priority_rank: 57

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 85.075
- improved_sanitation_pct_nfhs5: 62.4956
- lpg_pct_nfhs5: 28.0855
- mobile_phone_pct_nfhs5: 36.8144
- bank_account_pct_nfhs5: 66.8062
- wealth_index_mean_nfhs5: 20032.8563
- urban_pct_nfhs5: 33.193
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: PURVI CHAMPARAN→Purba Champaran; SITAMARHI→Sitamarhi; SHEOHAR→Sheohar
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: LOVELY ANAND
- winner_party_2024: JDU
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Sheohar flipped from BJP to JDU in 2024. BJP vote share changed by -60.6 points compared with 2019. The 2024 margin was 2.8%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Sheohar flipped from BJP to JDU between 2019 and 2024. BJP vote share changed by -60.6 percentage points versus 2019. The winning margin moved from 33.9% in 2019 to 2.8% in 2024. Turnout changed by -10.1 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Sheohar, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Sheohar may be analytically useful using priority reason (seat_flip;top_bjp_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
