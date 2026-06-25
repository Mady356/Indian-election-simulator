# Research packet: Kairana, Uttar Pradesh

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Uttar Pradesh (`UTTAR PRADESH`)
- Constituency: Kairana (`KAIRANA`)

## Election facts (2019 → 2024)
- Winner 2019: Pradeep Kumar
- Winner 2024: IQRA CHOUDHARY
- Party 2019: BJP
- Party 2024: SP
- Winner changed: True
- BJP vote share 2019: 50.4393
- BJP vote share 2024: 42.4981
- INC vote share 2019: 6.1701
- INC vote share 2024: 0.0
- BJP swing: -7.9412
- INC swing: -6.1701
- Margin 2019: 8.1989
- Margin 2024: 6.4008
- Margin change: -1.7982
- Turnout 2019: 34.0169
- Turnout 2024: 30.56
- Turnout change: -3.4569

## State context
- State seats: 80
- BJP seats 2019/2024: 62 / 33
- INC seats 2019/2024: 1 / 6
- State avg BJP swing: -8.51
- State avg INC swing: 3.46
- State demographic coverage: 63.75%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 195

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 59.4832
- improved_sanitation_pct_nfhs5: 23.4865
- lpg_pct_nfhs5: 18.7787
- mobile_phone_pct_nfhs5: 8.7156
- bank_account_pct_nfhs5: 38.2894
- wealth_index_mean_nfhs5: -6160.4394
- urban_pct_nfhs5: 16.2289
- nfhs5_coverage_share: 0.8
- change_coverage_share: 0.8
- change_quality_flag: medium
- districts_used: MUZAFFARNAGAR→Muzaffarnagar; ALLAHABAD→Allahabad (NFHS-4 proxy); SITAPUR→Sitapur (NFHS-4 proxy)
- districts_missing: GHAZIPUR

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: IQRA CHOUDHARY
- winner_party_2024: SP
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: manual
- generated summary: Kairana flipped from BJP to SP in 2024. BJP vote share changed by -7.9 points and INC vote share changed by -6.2 points compared with 2019. The 2024 margin was 6.4%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Kairana flipped from BJP to SP between 2019 and 2024. BJP vote share changed by -7.9 percentage points versus 2019. INC vote share changed by -6.2 percentage points versus 2019. The winning margin moved from 8.2% in 2019 to 6.4% in 2024. Turnout changed by -3.5 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: True
- manual note present in `manual/notes/`

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Kairana, Uttar Pradesh using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Kairana may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
