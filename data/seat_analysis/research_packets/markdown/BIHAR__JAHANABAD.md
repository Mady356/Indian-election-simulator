# Research packet: Jahanabad, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Jahanabad (`JAHANABAD`)

## Election facts (2019 → 2024)
- Winner 2019: CHANDESHWAR PRASAD
- Winner 2024: SURENDRA PRASAD YADAV
- Party 2019: JDU
- Party 2024: RJD
- Winner changed: True
- BJP vote share 2019: None
- BJP vote share 2024: None
- INC vote share 2019: None
- INC vote share 2024: None
- BJP swing: None
- INC swing: None
- Margin 2019: 0.213
- Margin 2024: 15.4091
- Margin change: 15.1961
- Turnout 2019: 21.1265
- Turnout 2024: 26.39
- Turnout change: 5.2635

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
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: True
- priority_reason: seat_flip
- priority_rank: 188

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 7.2071
- improved_sanitation_pct_nfhs5: 9.8145
- lpg_pct_nfhs5: 2.8886
- mobile_phone_pct_nfhs5: 0.446
- urban_pct_nfhs5: 10.7289
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: JAHANABAD→Jehanabad (NFHS-4 proxy); ARWAL→Arwal (NFHS-4 proxy); GAYA→Gaya (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SURENDRA PRASAD YADAV
- winner_party_2024: RJD
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Jahanabad flipped from JDU to RJD in 2024. Vote-share swing data are limited for this seat. The 2024 margin was 15.4%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Jahanabad flipped from JDU to RJD between 2019 and 2024. The winning margin moved from 0.2% in 2019 to 15.4% in 2024. Turnout changed by +5.3 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Jahanabad, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Jahanabad may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
