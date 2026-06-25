# Research packet: Banaskantha, Gujarat

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Gujarat (`GUJARAT`)
- Constituency: Banaskantha (`BANASKANTHA`)

## Election facts (2019 → 2024)
- Winner 2019: PARBATBHAI SAVABHAI PATEL
- Winner 2024: GENIBEN NAGAJI THAKOR
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 61.6205
- BJP vote share 2024: 46.6223
- INC vote share 2019: 28.2023
- INC vote share 2024: 48.8321
- BJP swing: -14.9983
- INC swing: 20.6299
- Margin 2019: 33.4182
- Margin 2024: 2.2099
- Margin change: -31.2083
- Turnout 2019: 40.0091
- Turnout 2024: 34.22
- Turnout change: -5.7891

## State context
- State seats: 25
- BJP seats 2019/2024: 25 / 24
- INC seats 2019/2024: 0 / 1
- State avg BJP swing: 0.36
- State avg INC swing: -1.54
- State demographic coverage: 84.0%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: True
- is_large_bjp_gain: False
- is_large_bjp_loss: True
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 140

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 100.0
- improved_sanitation_pct_nfhs5: 91.7609
- lpg_pct_nfhs5: 58.8043
- mobile_phone_pct_nfhs5: 63.5217
- bank_account_pct_nfhs5: 58.8043
- wealth_index_mean_nfhs5: 49311.3807
- urban_pct_nfhs5: 17.6085
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: KACHCHH→Kachchh
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: GENIBEN NAGAJI THAKOR
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Banaskantha flipped from BJP to INC in 2024. BJP vote share changed by -15.0 points and INC vote share changed by +20.6 points compared with 2019. The 2024 margin was 2.2%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Banaskantha flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -15.0 percentage points versus 2019. INC vote share changed by +20.6 percentage points versus 2019. The winning margin moved from 33.4% in 2019 to 2.2% in 2024. Turnout changed by -5.8 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Banaskantha, Gujarat using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Banaskantha may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
