# Reproduction Guide / 再現手順書

Step-by-step instructions to reproduce analysis outputs for:

**Administrative Diabetes Indicators Capture Distinct Stages of the Care Cascade**  
An Ecological Study of 335 Secondary Medical Areas in Japan

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
git clone https://github.com/haruki00430/administrative-diabetes-indicators-japan.git
cd administrative-diabetes-indicators-japan

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

Create the following folder under this repository's root and place the downloaded files there:

```
02_Data/raw/NDB_OpenData/No.11/
```

(`config/config.yaml` resolves this path relative to the script location; adjust `data.ndb_base` there if you use a different location.)

Required tables (see `config/config.yaml` for filenames):

- Specific health checkup: HbA1c and FPG by secondary medical area (age-sex strata)
- Medical claims: HbA1c test counts (D005), B001-20, B001-27 patients by area
- Prefecture-level aggregates for robustness analyses

Download: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177182.html

### 1-b. Population master (S5 sensitivity analysis)

For script `06_task_E_denominator_sensitivity.py`, place a prefecture x age-group population table (2023 estimates) at:

```
02_Data/raw/Statistics_Bureau/pop_2023_age_prefecture.csv
```

(or adjust `POP_DIR` in the script if using a different location). This table can be reconstructed from the Statistics Bureau of Japan's official population estimates (e-Stat, "人口推計"), filtered to prefecture x 5-year age group.

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

Submission DOCX (as of 2026-07-02, submitted to Annals of Epidemiology):  
`04_Manuscripts/11_v11_Administrative_Diabetes_Indicators_Care_Cascade_Annals.docx`  
`04_Manuscripts/11_v11_Supplement_Administrative_Diabetes_Indicators_Care_Cascade.docx`

Full submission package: `04_Manuscripts/submission_package_Ann-Epi/`

An early Quarto draft (working title, placeholder author fields) is kept for historical record only under `04_Manuscripts/archive/` and does not reflect the submitted version.

---

## Notes

- NDB cells with counts &lt; 10 are suppressed in source data; scripts treat these as missing.
- Clinical indicators use health-check participants per 1,000 as a proxy denominator in the main analysis; S5 tests population-based alternatives.
- Logs are written under `02_Data/interim/task_*.log` (gitignored).
