# Research packet: Supaul, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Supaul (`SUPAUL`)

## Election facts (2019 → 2024)
- Winner 2019: Dileshwar Kamait
- Winner 2024: DILESHWAR KAMAIT
- Party 2019: JDU
- Party 2024: JDU
- Winner changed: False
- BJP vote share 2019: None
- BJP vote share 2024: None
- INC vote share 2019: 29.7554
- INC vote share 2024: 0.0
- BJP swing: None
- INC swing: -29.7554
- Margin 2019: 24.0234
- Margin 2024: 13.7926
- Margin change: -10.2308
- Turnout 2019: 35.3348
- Turnout 2024: 30.85
- Turnout change: -4.4848

## State context
- State seats: 40
- BJP seats 2019/2024: 17 / 12
- INC seats 2019/2024: 1 / 3
- State avg BJP swing: -6.55
- State avg INC swing: 5.27
- State demographic coverage: 92.5%

## Rank / context flags
- is_flipped_seat: False
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: True
- is_priority_seat: True
- priority_reason: top_inc_loss
- priority_rank: 114

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 61.8078
- improved_sanitation_pct_nfhs5: 25.4615
- lpg_pct_nfhs5: 0.0
- mobile_phone_pct_nfhs5: 0.0
- bank_account_pct_nfhs5: 38.1922
- wealth_index_mean_nfhs5: -44104.885
- urban_pct_nfhs5: 10.8848
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: SUPAUL→Supaul
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: DILESHWAR KAMAIT
- winner_party_2024: JDU
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Supaul was retained by JDU in 2024. INC vote share changed by -29.8 points compared with 2019. The 2024 margin was 13.8%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Supaul was retained by JDU in 2024. INC vote share changed by -29.8 percentage points versus 2019. The winning margin moved from 24.0% in 2019 to 13.8% in 2024. Turnout changed by -4.5 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Supaul, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Supaul may be analytically useful using priority reason (top_inc_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
