# Research packet: Munger, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Munger (`MUNGER`)

## Election facts (2019 → 2024)
- Winner 2019: RAJIV RANJAN SINGH ALIAS LALAN SINGH
- Winner 2024: RAJIV RANJAN SINGH ALIAS LALAN SINGH
- Party 2019: JDU
- Party 2024: JDU
- Winner changed: False
- BJP vote share 2019: None
- BJP vote share 2024: None
- INC vote share 2019: 34.8197
- INC vote share 2024: 0.0
- BJP swing: None
- INC swing: -34.8197
- Margin 2019: 16.2059
- Margin 2024: 7.0996
- Margin change: -9.1064
- Turnout 2019: 28.0061
- Turnout 2024: 26.81
- Turnout change: -1.1961

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
- priority_rank: 104

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 4.7816
- improved_sanitation_pct_nfhs5: 7.0711
- lpg_pct_nfhs5: 1.0102
- mobile_phone_pct_nfhs5: 0.0
- urban_pct_nfhs5: 0.0
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: MUNGER→Munger (NFHS-4 proxy); PATNA→Patna (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: RAJIV RANJAN SINGH ALIAS LALAN SINGH
- winner_party_2024: JDU
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Munger was retained by JDU in 2024. INC vote share changed by -34.8 points compared with 2019. The 2024 margin was 7.1%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Munger was retained by JDU in 2024. INC vote share changed by -34.8 percentage points versus 2019. The winning margin moved from 16.2% in 2019 to 7.1% in 2024. Turnout changed by -1.2 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Munger, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Munger may be analytically useful using priority reason (top_inc_loss), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
