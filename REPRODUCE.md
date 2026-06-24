# Reproduction Guide / 再現手順書

Step-by-step instructions to reproduce analysis outputs for:

**What Do Administrative Healthcare Counts Really Measure?**  
A Care-Cascade Interpretation of Diabetes Indicators Across 335 Secondary Medical Areas in Japan

---

## System Requirements

| Item | Requirement |
|------|-------------|
| Python | 3.10 or later |
| OS | Windows 10/11, macOS 12+, Ubuntu 20.04+ |
| RAM | 4 GB or more |

---

## Step 0: Clone and Environment

```bash
git clone https://github.com/haruki00430/NDB_XXX_triangulation_dm.git
cd NDB_XXX_triangulation_dm

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Step 1: Data Preparation

### 1-a. NDB Open Data No.11 (MHLW)

Place downloaded Excel files under the path in `config/config.yaml`:

```
../../02_Data/raw/NDB_OpenData/No.11/
```

When running from this repository alone, either:

- clone inside [NDB_Research_Hub](https://github.com/haruki00430/NDB_Research_Hub) and use the shared `02_Data/raw/` tree, or
- create `02_Data/raw/NDB_OpenData/No.11/` locally and update `config/config.yaml` paths.

Required tables (see `config/config.yaml` for filenames):

- Specific health checkup: HbA1c and FPG by secondary medical area (age-sex strata)
- Medical claims: HbA1c test counts (D005), B001-20, B001-27 patients by area
- Prefecture-level aggregates for robustness analyses

Download: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177182.html

### 1-b. Population master (S5 sensitivity analysis)

For script `06_task_E_denominator_sensitivity.py`, place:

```
../../02_Data/raw/Statistics_Bureau/pop_2023_age_prefecture.csv
```

(or adjust `POP_DIR` in the script if using a local copy).

---

## Step 2: Analysis Pipeline

Run from repository root:

```bash
python 03_Analysis/scripts/01_task_A_data_extraction.py
python 03_Analysis/scripts/02_task_A_codebook.py
python 03_Analysis/scripts/03_task_B_standardization.py
python 03_Analysis/scripts/04_task_C_pca_figures.py
python 03_Analysis/scripts/05_task_D_robustness.py
python 03_Analysis/scripts/06_task_E_denominator_sensitivity.py
```

### Expected outputs

| Script | Main outputs |
|--------|----------------|
| 01–02 | `02_Data/interim/A*.csv`, codebook tables |
| 03 | `02_Data/interim/B1_district_standardized.csv`, `B2_prefecture_standardized.csv` |
| 04 | `03_Analysis/results/figures/fig1–4*.png`, `C1_spearman_correlation.csv`, PCA tables |
| 05 | `03_Analysis/results/tables/D*.csv`, robustness figures |
| 06 | `03_Analysis/results/tables/S5_*.csv`, `fig_S5_denominator_sensitivity.png` |

Intermediate CSV files are excluded from Git and must be regenerated locally.

---

## Step 3: Manuscript (optional)

Quarto source: `04_Manuscripts/Manuscript_triangulation_dm.qmd`

Submission DOCX (as of 2026-06-23):  
`04_Manuscripts/01What_Do_Administrative_Healthcare_Counts_Really_Measure_manuscript_revised_20260623.docx`

---

## Notes

- NDB cells with counts &lt; 10 are suppressed in source data; scripts treat these as missing.
- Clinical indicators use health-check participants per 1,000 as a proxy denominator in the main analysis; S5 tests population-based alternatives.
- Logs are written under `02_Data/interim/task_*.log` (gitignored).
