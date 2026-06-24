# What Do Administrative Healthcare Counts Really Measure?

**A Care-Cascade Interpretation of Diabetes Indicators Across 335 Secondary Medical Areas in Japan**

**行政医療カウントは何を測っているのか？**  
日本335二次医療圏における糖尿病関連指標のケアカスケード解釈

---

## Overview / 概要

### English

This repository contains analysis code for a nationwide ecological study examining whether five diabetes-related administrative indicators from Japan's NDB Open Data converge on a single regional construct or occupy distinct positions along the care cascade (screening, testing, complication management).

**Key finding**: HbA1c elevation from health checkups and B001-20 complication management claims were essentially uncorrelated at the secondary-medical-area level (Spearman ρ ≈ −0.07). PCA separated screening/testing indicators (PC1) from management claims (PC2). Proxy-denominator sensitivity analyses supported that this pattern was not an artifact of the shared checkup-participant denominator.

**Study design**: Cross-sectional ecological study | N = 335 secondary medical areas (251 complete cases for PCA) | NDB Open Data No.11 (FY2024 claims; FY2023 checkups)

**Manuscript**: Saito H, Ohira T. What Do Administrative Healthcare Counts Really Measure? A Care-Cascade Interpretation of Diabetes Indicators Across 335 Secondary Medical Areas in Japan. *(In preparation, 2026)*

### 日本語

本リポジトリは、NDBオープンデータの糖尿病関連5指標が単一の地域指標として収束するか、ケアカスケード上の異なる段階（スクリーニング・検査・合併症管理）を反映するかを検証した全国生態学研究の解析コードを公開するものです。

**主要結果**: 健診由来のHbA1c高値率とB001-20（合併症管理料）患者数は二次医療圏レベルでほぼ無相関（ρ ≈ −0.07）。PCAではPC1がスクリーニング・検査、PC2が合併症管理指標を分離。代理分母感度分析（S5）でもこのパターンは健診受診者という共通分母のアーティファクトではないことが支持されました。

---

## Data Sources / データソース

| Source | Variables | 説明 |
|---|---|---|
| NDB Open Data No.11 (MHLW) | HbA1c/FPG checkup rates, HbA1c tests, B001-20, B001-27 | 健診・レセプト集計（FY2023健診 / FY2024レセプト） |
| National Census 2020 (Statistics Bureau) | Reference population (40–74 years) | 直接標準化の基準人口 |
| Population estimates 2023 (Statistics Bureau) | Prefecture population by age | S5感度分析の代替分母 |

> **Note**: NDB raw Excel files are not included in this repository. Download from: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177182.html  
> Population master CSV used by S5 is shared via the parent NDB Research Hub (`02_Data/raw/Statistics_Bureau/`) or official Statistics Bureau releases.

---

## Repository Structure / リポジトリ構造

```
NDB_XXX_care_cascade_dm/
├── config/
│   └── config.yaml                 # 指標定義・データパス
├── 02_Data/
│   └── interim/                    # 中間CSV（.gitignore; スクリプトで再生成）
├── 03_Analysis/
│   ├── scripts/
│   │   ├── 01_task_A_data_extraction.py
│   │   ├── 02_task_A_codebook.py
│   │   ├── 03_task_B_standardization.py
│   │   ├── 04_task_C_pca_figures.py
│   │   ├── 05_task_D_robustness.py
│   │   └── 06_task_E_denominator_sensitivity.py   # S5 proxy-denominator sensitivity
│   └── results/
│       ├── figures/                # 論文用図（PNG）
│       └── tables/                 # 結果表（CSV; .gitignore）
├── 04_Manuscripts/
│   ├── 01What_Do_..._manuscript_revised_20260623.docx
│   ├── Manuscript_care_cascade_dm.qmd
│   ├── references.bib
│   └── vancouver.csl
└── 00_Docs/                        # 実施報告書・作業サマリー
```

---

## Reproduction / 再現手順

詳細は [REPRODUCE.md](REPRODUCE.md) を参照してください。

```bash
git clone https://github.com/haruki00430/NDB_XXX_care_cascade_dm.git
cd NDB_XXX_care_cascade_dm
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

解析スクリプトは `03_Analysis/scripts/` を 01 → 06 の順に実行します。NDB No.11 生データは `config/config.yaml` のパス（Hub 共通 `02_Data/raw/NDB_OpenData/No.11/`）に配置してください。

---

## Citation / 引用

**Manuscript** (in preparation):

> Saito H, Ohira T. What Do Administrative Healthcare Counts Really Measure? A Care-Cascade Interpretation of Diabetes Indicators Across 335 Secondary Medical Areas in Japan.

**Code repository**:

> https://github.com/haruki00430/NDB_XXX_care_cascade_dm

---

## Ethics / 倫理事項

This study used publicly available aggregate data only. Individual informed consent was not required, and institutional ethics review was not applicable in accordance with Japanese ethical guidelines for epidemiological research.

---

## License / ライセンス

Analysis code is released under the [MIT License](LICENSE). NDB Open Data is provided by MHLW Japan and is not redistributable from this repository.
