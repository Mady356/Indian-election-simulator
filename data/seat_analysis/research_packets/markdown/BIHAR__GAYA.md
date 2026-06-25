# Research packet: Gaya, Bihar

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: Bihar (`BIHAR`)
- Constituency: Gaya (`GAYA`)

## Election facts (2019 → 2024)
- Winner 2019: Vijay Kumar
- Winner 2024: JITAN RAM MANJHI
- Party 2019: JDU
- Party 2024: HAMS
- Winner changed: True
- BJP vote share 2019: None
- BJP vote share 2024: None
- INC vote share 2019: None
- INC vote share 2024: None
- BJP swing: None
- INC swing: None
- Margin 2019: None
- Margin 2024: 10.565
- Margin change: None
- Turnout 2019: 27.3969
- Turnout 2024: 27.18
- Turnout change: -0.2169

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
- priority_rank: 178

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 12.818
- improved_sanitation_pct_nfhs5: 8.2439
- lpg_pct_nfhs5: 0.0
- mobile_phone_pct_nfhs5: 0.0
- urban_pct_nfhs5: 17.3934
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: GAYA→Gaya (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: JITAN RAM MANJHI
- winner_party_2024: HAMS
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: generated
- generated summary: Gaya flipped from JDU to HAMS in 2024. Vote-share swing data are limited for this seat. The 2024 margin was 10.6%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Gaya flipped from JDU to HAMS between 2019 and 2024. The 2024 winning margin was 10.6%. Turnout changed by -0.2 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: False

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Gaya, Bihar using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Gaya may be analytically useful using priority reason (seat_flip), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
