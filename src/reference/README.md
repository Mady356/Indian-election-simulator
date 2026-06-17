# Delimitation reference crosswalks

Canonical **Lok Sabha → Assembly → District** mappings parsed from the 2008 Delimitation Order PDF:

`data/raw/ls-as-mapping/DelimitationofParliamentaryAssemblyConstituenciesOrder-2008(English).pdf`

These outputs are **separate** from the name-based `district_constituency_crosswalk.csv` built earlier in `build_district_constituency_crosswalk.py`.

## Pipeline

Run in order from the project root (with venv active):

```bash
python -m src.reference.extract_delimitation_order
python -m src.reference.build_ls_ac_crosswalk
python -m src.reference.build_ls_district_crosswalk_from_delimitation
python -m src.reference.debug_delimitation_ac_join
```

### Step 1 — Extract PDF text

`extract_delimitation_order.py` uses system `pdftotext -layout` (one row per page).

| Output | Description |
|--------|-------------|
| `data/reference/delimitation_raw_text.csv` | Raw page text (572 pages) |

### Step 2 — Parse Table A & Table B

`build_ls_ac_crosswalk.py` parses:

- **Table A** — Assembly constituency → District (by state schedule)
- **Table B** — Lok Sabha constituency → Assembly segments

| Output | Description |
|--------|-------------|
| `data/reference/assembly_constituency_district_crosswalk.csv` | AC → district |
| `data/reference/lok_sabha_assembly_crosswalk.csv` | LS → AC segments |
| `data/reference/manual_review/delimitation_low_confidence_*.csv` | Rows needing manual review |

Expected coverage: ~4,120 assembly seats, ~543 Lok Sabha seats across states/UTs.

**Special cases:**

- **Jammu & Kashmir** — parliamentary seats in Schedule XII; assembly ACs appear in **Annexure I** at the end of the PDF (partial coverage).
- **Manipur / Nagaland** — small states with non-standard Table B layouts; may require manual fixes.

### Step 3 — Join LS → District

`build_ls_district_crosswalk_from_delimitation.py` joins Table B assembly segments to Table A districts by `(state, assembly_no)` with a name fallback.

| Output | Description |
|--------|-------------|
| `data/reference/lok_sabha_district_crosswalk_delimitation.csv` | LS–AC–district rows |
| `data/reference/lok_sabha_district_summary_delimitation.csv` | Segment counts & shares per LS–district |
| `data/reference/manual_review/unmatched_ls_ac_join_diagnostics.csv` | Detailed join failure diagnostics |
| `data/reference/assembly_constituency_district_crosswalk_normalized.csv` | Table A with normalized name columns |
| `data/reference/lok_sabha_assembly_crosswalk_normalized.csv` | Table B with normalized name columns |

Run `python -m src.reference.debug_delimitation_ac_join` to regenerate diagnostics
and normalized copies without touching raw parsed crosswalks.

## Join matching strategy

The district crosswalk uses layered matching (in order):

1. **by_number** — `(state, assembly_no)` exact match
2. **by_exact_name** — normalized short name match
3. **by_substring / by_prefix** — unique match in Table A extent text
4. **by_fuzzy_name** — rapidfuzz/difflib score ≥ 92, unique best hit
5. **unmatched** — flagged for manual review

Delhi Table A rows omit district names; joins assign district `"Delhi"`.

## Important caveats

1. **Not GIS-based.** `district_segment_share` in the summary file is the fraction of *assembly segments* listed for a Lok Sabha seat that fall in each district. It is **not** population-weighted and does not use polygon overlap. Multi-district seats are common; treat secondary districts accordingly.

2. **Parse confidence.** Table B uses several PDF layout conventions (dash vs dot numbering, em-dashes, wrapped constituency names). Rows marked `parse_confidence=low` or `mapping_confidence=low` should be reviewed before production use.

3. **2008 boundaries.** District names and seat numbers reflect the 2008 delimitation. Post-2014 district reorganisations (e.g. Telangana, new districts) are not captured in the delimitation schedule itself — see `ap_telangana_bifurcation.py` for NFHS join routing.

4. **Do not overwrite** `data/reference/district_constituency_crosswalk.csv` — that file comes from a different name-matching pipeline.

## Delimitation → Census district aliases

The delimitation order uses district spellings that often differ from Census 2011 / NFHS labels (e.g. `RANGAREDDI` vs `RANGAREDDY`, `KAIMUR (BHABUA)` vs census `KAIMUR (BHABUA)`).

Build after `lok_sabha_district_summary_delimitation.csv` and census demographics exist:

```bash
python -m src.reference.build_delimitation_census_district_alias
```

| Output | Description |
|--------|-------------|
| `data/reference/delimitation_census_district_alias.csv` | Delimitation district → census district (+ NFHS-5 label when available) |
| `data/reference/manual_review/delimitation_district_alias_unmatched.csv` | Pairs that could not be mapped |

Matching uses normalized keys with parenthetical expansion (`WEST NIMAR (Khaorgone)` → `KHARGONE WEST NIMAR`), a curated alias table in `delimitation_district_aliases.py`, and fuzzy fallback. Delhi placeholder rows expand to all nine NCT census districts with `aggregate_share = 1/9`.

This table is consumed by the NFHS constituency demographic panel (`src/demographics/nfhs/district_alias.py`).

**AP/Telangana bifurcation (2014):** Delimitation districts under schedule "Andhra Pradesh" that lie in Telangana (`RANGAREDDI`, `HYDERABAD`, etc.) map to census `ANDHRA PRADESH` but use `nfhs4_state=Andhra Pradesh` and `nfhs5_state=Telangana`. Logic lives in `src/reference/ap_telangana_bifurcation.py`.

## Dependencies

- `pdftotext` and `pdfinfo` (Poppler) on `PATH`
- Python packages: `pandas`, project `src.config`
