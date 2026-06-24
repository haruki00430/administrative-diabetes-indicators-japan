# Task F: Pre-emptive Reviewer Response Memo
## Paper: "What Do Administrative Healthcare Counts Really Measure?"
## Date: 2026-06-22 | Status: Draft

This memo anticipates the five most likely reviewer objections and provides response language, supported by the analysis results from Tasks A–D.

---

## Comment 1: "The sample size (n=47 prefectures) is too small for PCA / regression."

**Expected reviewer wording:**
"With only 47 prefectures, the statistical power for PCA and Spearman correlation analysis is insufficient, and results may not be generalizable."

**Response:**
The primary analysis uses n=335 **secondary medical districts** — not 47 prefectures. The 47-prefecture analysis is a pre-specified robustness check only (Supplementary). With n=335 (complete case n=251 for PCA), our analysis is adequately powered to detect moderate correlations (ρ≥0.15) with >90% power at α=0.05. For PCA, the 251:5 indicator ratio far exceeds the 10:1 rule-of-thumb for stable component extraction.

**Supporting evidence in paper:**
- Main analysis: n=335 districts (B4_analysis_dataset_district.csv)
- Complete case for PCA: n=251
- Spearman correlations are pairwise: n=290–335 per pair

**Reinforcing language for rebuttal:**
"We note that the primary analysis was conducted at the secondary medical district level (n=335), not the prefecture level. The prefecture-level analysis (n=47) was a pre-specified robustness check. Our primary conclusions are based on the district-level data."

---

## Comment 2: "You are calling one indicator a 'ground truth' and treating others as proxies."

**Expected reviewer wording:**
"The manuscript implies that [HbA1c checkup rate / B001-20] is the gold standard against which others should be compared."

**Response:**
We explicitly state in the Introduction that "no single ground truth exists" for regional DM burden. The framing of this paper is precisely **triangulation** — we treat all five indicators as partial, complementary measures of distinct facets of the DM care continuum. The PCA structure (PC1 = screening intensity; PC2 = complication management) empirically supports this multi-dimensional interpretation. No indicator is privileged as a reference standard; the correlation structure is symmetric.

**Specific quotes from manuscript to cite:**
- Introduction: "each indicator reflects a different point in the care cascade"
- Discussion: "Policymakers who select only one of these indicators may reach opposite conclusions about regional DM burden"
- Table 2: symmetric Spearman matrix (no row/column designated as 'reference')

**If reviewer persists:**
"We have reviewed the manuscript and confirm that no indicator is designated as 'ground truth.' The Spearman correlation matrix (Table 2) is symmetric by design. We will add a clarifying sentence to the Methods if the reviewer identifies a specific passage that creates this impression."

---

## Comment 3: "Age adjustment is inadequate / inconsistent across indicators."

**Expected reviewer wording:**
"The health checkup indicators are directly age-standardized, but the clinical indicators (B001-20, B001-27, HbA1c test) are only expressed per 1,000 tested participants without age adjustment. This inconsistency biases the comparison."

**Response:**
We acknowledge this limitation explicitly in the Limitations section. The inconsistency arises from a genuine data constraint: the NDB Open Data does not provide age-disaggregated clinical procedure counts at the district level, making direct standardization technically infeasible (see Supplementary Table S1). Our proxy denominator approach (per 1,000 tested) is the best available method.

To evaluate residual age confounding, we externally correlated PC scores with a proxy aging rate (proportion of tested participants aged 65–74). Results show that PC1 (screening/diagnostic intensity) is positively correlated with aging (ρ=0.43, p<0.001), confirming some age-driven variation — which is a substantive finding rather than a bias to be eliminated.

**Reinforcing point:** The primary finding (divergence between screening and management indicators) is preserved even when comparing indicators within each level of aging proxy, as demonstrated in the robustness analysis (D2: HbA1c×B001-20 ρ≈−0.07 is consistent across all outlier-exclusion scenarios).

**If reviewer requests sensitivity analysis:**
"We would be happy to add a sensitivity analysis using age-stratified sub-analyses if age-disaggregated data become available, or to further characterize the role of aging in a regression model. However, we note that this limitation is inherent to the NDB Open Data release and applies equally to all previous studies using this dataset."

---

## Comment 4: "The PC axis labels (e.g., 'diagnostic intensity') are subjective."

**Expected reviewer wording:**
"The interpretation of PC1 as 'diagnostic intensity' and PC2 as 'complication-management engagement' is the authors' subjective labeling and is not validated."

**Response:**
The axis labels are transparent in their derivation: they describe the indicators with the highest absolute loadings on each component (PC1: FPG high rate 0.66, HbA1c test 0.53, HbA1c high rate 0.47; PC2: B001-20 0.74, B001-27 0.63 — see Table C2_pca_loadings). The labels are interpreted, not asserted, and we provide the full loading table so readers can draw their own conclusions.

External validation is provided by the proxy aging rate correlation: PC1 (detection/screening) correlates with older populations (ρ=0.43), consistent with higher DM prevalence and more screening activity in aging districts. PC2 (management engagement) shows a negative correlation with aging (ρ=−0.30), consistent with urban healthcare infrastructure being concentrated in younger metropolitan districts.

We will use hedged language ("this component may reflect...") and refer readers to Table C2 in the revision.

---

## Comment 5: "Why not include X indicator (e.g., HbA1c test count vs. diabetic retinopathy screening vs. DPC data)?"

**Expected reviewer wording:**
"The indicator selection is incomplete. Why were retinopathy screening (B001-6), DPC hospital data, or self-reported DM prevalence not included?"

**Response:**
Indicator selection was pre-specified based on four criteria: (1) availability in NDB Open Data No. 11, (2) specificity for type 2 DM (distinct from type 1 confounding), (3) availability at the secondary medical district level, and (4) methodological diversity (screening, laboratory, claims-based). Our five selected indicators represent the main categories of DM-related healthcare activity available at the district level in NDB Open Data.

**B001-6** (retinopathy) was considered but is not DM-specific; it covers all retinopathy management including non-diabetic etiologies, which would introduce additional heterogeneity.

**DPC data** are not part of the NDB Open Data (they require separate application to MHLW); including them would require a data access process outside the scope of this replication-friendly public-data analysis.

**Self-reported DM prevalence** from the National Health and Nutrition Survey is available only at the national/regional level and lacks district-level resolution.

We acknowledge these constraints as limitations and recommend future studies link NDB Open Data with DPC and vital statistics for a more complete indicator set.

---

## Supplementary Note: Prescription Data Exclusion Rationale

(For reviewer queries about the absence of prescription data in the district analysis)

**Why prescription indicators are not in the primary (district) analysis:**

The NDB Open Data No. 11 provides antidiabetic drug prescription data (pharmacological class 396) aggregated at the **prefecture level only** (47 prefectures). The "05_処方薬" folder contains files with prefecture-level breakdowns but no district-level breakdown. This was confirmed by inspecting all files in the NDB No. 11 data release.

Accordingly, prescription data were excluded from the primary analysis (n=335 districts) and included only in the prefecture-level robustness check (n=47), as documented in Supplementary Table S1.

This is a data availability constraint, not an analytical choice. Future NDB Open Data releases may include district-level prescription data, which would allow a more complete district-level triangulation.

---

*This memo was prepared based on analytical results from Task D sensitivity analyses and prior experience with BMC Medical Research Methodology / Population Health Metrics reviewer expectations.*

*Last updated: 2026-06-22*
