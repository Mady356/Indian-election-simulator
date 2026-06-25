# Research packet: Sultanpur, Uttar Pradesh

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Uttar Pradesh (`UTTAR PRADESH`)
- Constituency: Sultanpur (`SULTANPUR`)

## Election facts (2019 → 2024)
- Winner 2019: MANEKA SANJAI GANDHI
- Winner 2024: RAMBHUAL NISHAD
- Party 2019: BJP
- Party 2024: SP
- Winner changed: True
- BJP vote share 2019: 45.9051
- BJP vote share 2024: 38.8195
- INC vote share 2019: 4.1668
- INC vote share 2024: 0.0
- BJP swing: -7.0856
- INC swing: -4.1668
- Margin 2019: 1.4521
- Margin 2024: 4.1779
- Margin change: 2.7258
- Turnout 2019: 25.8673
- Turnout 2024: 23.95
- Turnout change: -1.9173

## State context
- State seats: 80
- BJP seats 2019/2024: 62 / 33
- INC seats 2019/2024: 1 / 6
- State avg BJP swing: -8.51
- State avg INC swing: 3.46
- State demographic coverage: 63.75%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: True
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 260

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 45.8755
- improved_sanitation_pct_nfhs5: 27.1028
- lpg_pct_nfhs5: 18.4033
- mobile_phone_pct_nfhs5: 11.7122
- bank_account_pct_nfhs5: 23.137
- wealth_index_mean_nfhs5: -39556.9075
- urban_pct_nfhs5: 25.1953
- nfhs5_coverage_share: 0.9999
- change_coverage_share: 0.9999
- change_quality_flag: medium
- districts_used: GORAKHPUR→Gorakhpur (NFHS-4 proxy); MORADABAD→Moradabad; SULTANPUR→Sultanpur
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: RAMBHUAL NISHAD
- winner_party_2024: SP
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: manual
- generated summary: Sultanpur flipped from BJP to SP in 2024. BJP vote share changed by -7.1 points and INC vote share changed by -4.2 points compared with 2019. The 2024 margin was 4.2%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Sultanpur flipped from BJP to SP between 2019 and 2024. BJP vote share changed by -7.1 percentage points versus 2019. INC vote share changed by -4.2 percentage points versus 2019. The winning margin moved from 1.5% in 2019 to 4.2% in 2024. Turnout changed by -1.9 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: True
- manual note present in `manual/notes/`

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Sultanpur, Uttar Pradesh using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Sultanpur may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
