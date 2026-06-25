# Research packet: Nawada, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Nawada (`NAWADA`)

## Election facts (2019 → 2024)
- Winner 2019: Chandan Singh
- Winner 2024: VIVEK THAKUR
- Party 2019: LJP
- Party 2024: BJP
- Winner changed: True
- BJP vote share 2019: 0.0
- BJP vote share 2024: 47.2034
- INC vote share 2019: None
- INC vote share 2024: None
- BJP swing: 47.2034
- INC swing: None
- Margin 2019: 15.7112
- Margin 2024: 7.7793
- Margin change: -7.9319
- Turnout 2019: 26.0921
- Turnout 2024: 20.43
- Turnout change: -5.6621

## State context
- State seats: 40
- BJP seats 2019/2024: 17 / 12
- INC seats 2019/2024: 1 / 3
- State avg BJP swing: -6.55
- State avg INC swing: 5.27
- State demographic coverage: 92.5%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: True
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip;top_bjp_gain
- priority_rank: 48

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 21.6173
- improved_sanitation_pct_nfhs5: 6.8757
- lpg_pct_nfhs5: 1.2196
- mobile_phone_pct_nfhs5: 0.2241
- urban_pct_nfhs5: 7.901
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: NAWADA→Nawada (NFHS-4 proxy); SHEIKHPURA→Sheikhpura (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: VIVEK THAKUR
- winner_party_2024: BJP
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Nawada flipped from LJP to BJP in 2024. BJP vote share changed by +47.2 points compared with 2019. The 2024 margin was 7.8%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Nawada flipped from LJP to BJP between 2019 and 2024. BJP vote share changed by +47.2 percentage points versus 2019. The winning margin moved from 15.7% in 2019 to 7.8% in 2024. Turnout changed by -5.7 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Nawada, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Nawada may be analytically useful using priority reason (seat_flip;top_bjp_gain), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
