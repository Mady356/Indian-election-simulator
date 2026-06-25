# Research packet: Sasaram, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Sasaram (`SASARAM`)

## Election facts (2019 → 2024)
- Winner 2019: CHHEDI PASWAN
- Winner 2024: MANOJ KUMAR
- Party 2019: BJP
- Party 2024: INC
- Winner changed: True
- BJP vote share 2019: 50.7618
- BJP vote share 2024: 45.0149
- INC vote share 2019: 33.7579
- INC vote share 2024: 46.7611
- BJP swing: -5.7469
- INC swing: 13.0031
- Margin 2019: None
- Margin 2024: 1.7462
- Margin change: None
- Turnout 2019: 27.6753
- Turnout 2024: 26.79
- Turnout change: -0.8853

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
- is_large_inc_gain: True
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 256

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 45.437
- improved_sanitation_pct_nfhs5: 29.705
- lpg_pct_nfhs5: 4.6452
- mobile_phone_pct_nfhs5: 2.6946
- urban_pct_nfhs5: 33.3454
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: KAIMUR (BHABUA)→Kaimur (Bhabua) (NFHS-4 proxy); ROHTAS→Rohtas (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: MANOJ KUMAR
- winner_party_2024: INC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Sasaram flipped from BJP to INC in 2024. BJP vote share changed by -5.7 points and INC vote share changed by +13.0 points compared with 2019. The 2024 margin was 1.7%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Sasaram flipped from BJP to INC between 2019 and 2024. BJP vote share changed by -5.7 percentage points versus 2019. INC vote share changed by +13.0 percentage points versus 2019. The 2024 winning margin was 1.7%. Turnout changed by -0.9 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Sasaram, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Sasaram may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
