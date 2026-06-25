# Research packet: Alathur, Kerala

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Kerala (`KERALA`)
- Constituency: Alathur (`ALATHUR`)

## Election facts (2019 → 2024)
- Winner 2019: RAMYA HARIDAS
- Winner 2024: K.RADHAKRISHNAN
- Party 2019: INC
- Party 2024: CPIM
- Winner changed: True
- BJP vote share 2019: 0.0
- BJP vote share 2024: 18.9697
- INC vote share 2019: 52.3994
- INC vote share 2024: 38.6323
- BJP swing: 18.9697
- INC swing: -13.7671
- Margin 2019: 15.6043
- Margin 2024: 2.0268
- Margin change: -13.5776
- Turnout 2019: 42.1391
- Turnout 2024: 30.1
- Turnout change: -12.0391

## State context
- State seats: 20
- BJP seats 2019/2024: 0 / 1
- INC seats 2019/2024: 15 / 14
- State avg BJP swing: 4.14
- State avg INC swing: -2.74
- State demographic coverage: 85.0%

## Rank / context flags
- is_flipped_seat: True
- is_close_2024: True
- is_large_bjp_gain: True
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: True
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 123

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 75.0
- improved_sanitation_pct_nfhs5: 50.0
- lpg_pct_nfhs5: 0.0
- mobile_phone_pct_nfhs5: 25.0
- bank_account_pct_nfhs5: 50.0
- wealth_index_mean_nfhs5: 5489.5
- urban_pct_nfhs5: 0.0
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: low
- districts_used: Thrissur→Thrissur
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: K.RADHAKRISHNAN
- winner_party_2024: CPIM
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Alathur flipped from INC to CPIM in 2024. BJP vote share changed by +19.0 points and INC vote share changed by -13.8 points compared with 2019. The 2024 margin was 2.0%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Alathur flipped from INC to CPIM between 2019 and 2024. BJP vote share changed by +19.0 percentage points versus 2019. INC vote share changed by -13.8 percentage points versus 2019. The winning margin moved from 15.6% in 2019 to 2.0% in 2024. Turnout changed by -12.0 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Alathur, Kerala using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Alathur may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
