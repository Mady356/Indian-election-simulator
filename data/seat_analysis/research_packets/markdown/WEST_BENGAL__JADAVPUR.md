# Research packet: Jadavpur, West Bengal

_Generated 2026-06-22. Evidence-backed prompts only; no invented local facts._

## Identity
- State: West Bengal (`WEST BENGAL`)
- Constituency: Jadavpur (`JADAVPUR`)

## Election facts (2019 → 2024)
- Winner 2019: MIMI CHAKRABORTY
- Winner 2024: SAYANI GHOSH
- Party 2019: AITC
- Party 2024: AITC
- Winner changed: False
- BJP vote share 2019: 27.3669
- BJP vote share 2024: 29.3454
- INC vote share 2019: None
- INC vote share 2024: None
- BJP swing: 1.9785
- INC swing: None
- Margin 2019: 20.547
- Margin 2024: 16.4826
- Margin change: -4.0645
- Turnout 2019: 37.8936
- Turnout 2024: 35.29
- Turnout change: -2.6036

## State context
- State seats: 42
- BJP seats 2019/2024: 18 / 12
- INC seats 2019/2024: 2 / 1
- State avg BJP swing: -1.48
- State avg INC swing: -0.85
- State demographic coverage: 64.29%

## Rank / context flags
- is_flipped_seat: False
- is_close_2024: False
- is_large_bjp_gain: False
- is_large_bjp_loss: False
- is_large_inc_gain: False
- is_large_inc_loss: False
- is_priority_seat: False
- priority_reason: None
- priority_rank: None

## Demographic context
- data_quality_label: high
- electricity_pct_nfhs5: 33.5936
- improved_sanitation_pct_nfhs5: 15.8842
- lpg_pct_nfhs5: 1.7634
- mobile_phone_pct_nfhs5: 0.8802
- urban_pct_nfhs5: 0.0
- nfhs5_coverage_share: 1.0
- change_coverage_share: 1.0
- change_quality_flag: medium
- districts_used: SOUTH 24 PARGANAS→South Twenty Four Parganas (NFHS-4 proxy)
- districts_missing: N/A

## Simulation context
- simulation_completeness: full_party_shares
- winner_2024: SAYANI GHOSH
- winner_party_2024: AITC
- data_quality_label: high
- projection_confidence_hint: high

## Existing analysis
- analysis_source: manual
- generated summary: Jadavpur was retained by AITC in 2024. BJP vote share changed by +2.0 points compared with 2019. The 2024 margin was 16.5%. This is a descriptive election profile, not a causal explanation.
- generated movement: Available data indicates Jadavpur was retained by AITC in 2024. BJP vote share changed by +2.0 percentage points versus 2019. The winning margin moved from 20.5% in 2019 to 16.5% in 2024. Turnout changed by -2.6 percentage points between 2019 and 2024. This section describes observed election movement only and is not a causal explanation.
- has manual markdown: True
- manual note present in `manual/notes/`

## Writing prompts

- **what_happened_prompt**: Describe observed 2019→2024 election movement for Jadavpur, West Bengal using winner, vote-share, margin, and turnout fields only.
- **why_it_mattered_prompt**: Explain why Jadavpur may be analytically useful using priority reason (none), contest closeness, swings, and state context.
- **factors_prompt**: List only cautious factors such as candidate profile, alliance arithmetic, state-level swing, turnout movement, or limited demographic coverage.
- **demographic_prompt**: Summarise available NFHS-linked indicators and district mapping. If unavailable, state that the profile remains election-only.
- **what_to_watch_prompt**: Use forward-looking but non-predictive language about seat stability, swing consolidation, and coverage improvements.
- **caveat_prompt**: State that local causal explanations require further source review.
