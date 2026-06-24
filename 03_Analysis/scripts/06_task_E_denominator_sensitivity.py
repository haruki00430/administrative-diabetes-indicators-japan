# -*- coding: utf-8 -*-
"""
タスクE（感度分析 S5）：代理分母変更感度分析
計画書 §5 追加感度分析（コメント指摘課題1への対応）

【目的】
臨床3指標（HbA1c検査・B001-20・B001-27）は現在「健診受診者数（hba1c_total_n）」を
代理分母としている。この共通分母が Spearman 相関構造に人工的なパターンを
生んでいないかを検証する。

【感度分析シナリオ】
S_main  : 現行（1,000健診受診者あたり） ← 比較ベース
S5a     : log1p 変換した実数カウント（二次医療圏）
          ※ log変換でスケールを揃えつつ、分母の影響を除去
S5b     : 都道府県レベル・65歳以上人口あたり（e-Stat/統計局 FY2023 推計）
S5c     : 都道府県レベル・全人口あたり（統計局 FY2023 推計）
S5d     : 都道府県レベル・40-74歳人口あたり（特定健診対象年齢・統計局 FY2023 推計）

【判定基準】
  - Spearman ρ の変化が ±0.10 未満 → 頑健（stable）
  - PC1/PC2 の最大ローディング指標が変わらない → PC 構造が維持される

出力:
  03_Analysis/results/tables/S5a_district_correlation_logcount.csv
  03_Analysis/results/tables/S5b_prefecture_correlation_per65plus.csv
  03_Analysis/results/tables/S5_pca_loadings_comparison.csv
  03_Analysis/results/tables/S5_stability_summary.csv
  03_Analysis/results/figures/fig_S5_denominator_sensitivity.png
"""

import sys
from pathlib import Path
import logging
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=FutureWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
INTERIM_DIR = PROJECT_DIR / "02_Data" / "interim"
FIG_DIR = PROJECT_DIR / "03_Analysis" / "results" / "figures"
TABLE_DIR = PROJECT_DIR / "03_Analysis" / "results" / "tables"
POP_DIR = (PROJECT_DIR.parent.parent
           / "02_Data" / "raw" / "Statistics_Bureau")
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(INTERIM_DIR / "task_E_denominator_sensitivity.log",
                            encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 指標名の短縮ラベル
# ---------------------------------------------------------------------------
LABELS_MAIN = {
    "hba1c_std_rate_pct":       "HbA1c_elev",
    "fpg_std_rate_pct":         "FPG_abn",
    "hba1c_test_per1k_tested":  "HbA1c_test",
    "B001_20_per1k_tested":     "B001-20",
    "B001_27_per1k_tested":     "B001-27",
}
LABELS_LOG = {
    "hba1c_std_rate_pct":        "HbA1c_elev",
    "fpg_std_rate_pct":          "FPG_abn",
    "hba1c_test_log":            "HbA1c_test",
    "B001_20_log":               "B001-20",
    "B001_27_log":               "B001-27",
}
LABELS_PER65 = {
    "hba1c_std_rate_pct":        "HbA1c_elev",
    "fpg_std_rate_pct":          "FPG_abn",
    "hba1c_test_per65k":         "HbA1c_test",
    "B001_20_per65k":            "B001-20",
    "B001_27_per65k":            "B001-27",
}
LABELS_PERTOT = {
    "hba1c_std_rate_pct":        "HbA1c_elev",
    "fpg_std_rate_pct":          "FPG_abn",
    "hba1c_test_per100k":        "HbA1c_test",
    "B001_20_per100k":           "B001-20",
    "B001_27_per100k":           "B001-27",
}
LABELS_PER4074 = {
    "hba1c_std_rate_pct":        "HbA1c_elev",
    "fpg_std_rate_pct":          "FPG_abn",
    "hba1c_test_per4074k":       "HbA1c_test",
    "B001_20_per4074k":          "B001-20",
    "B001_27_per4074k":          "B001-27",
}

INDICATOR_ORDER = ["HbA1c_elev", "FPG_abn", "HbA1c_test", "B001-20", "B001-27"]


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def spearman_matrix(df: pd.DataFrame, cols: list[str],
                    labels: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = len(cols)
    rho = np.full((n, n), np.nan)
    pval = np.full((n, n), np.nan)
    for i, ci in enumerate(cols):
        for j, cj in enumerate(cols):
            mask = df[[ci, cj]].notna().all(axis=1)
            if mask.sum() >= 10:
                r, p = stats.spearmanr(df.loc[mask, ci], df.loc[mask, cj])
                rho[i, j] = round(r, 4)
                pval[i, j] = round(p, 4)
    idx = [labels[c] for c in cols]
    return (pd.DataFrame(rho, index=idx, columns=idx),
            pd.DataFrame(pval, index=idx, columns=idx))


def run_pca(df: pd.DataFrame, cols: list[str],
            labels: dict, label: str) -> dict:
    sub = df[cols].dropna()
    n_valid = len(sub)
    scaler = StandardScaler()
    Z = scaler.fit_transform(sub)
    pca = PCA(n_components=min(3, len(cols)))
    pca.fit(Z)
    loading_cols = [labels[c] for c in cols]
    loadings = pd.DataFrame(
        pca.components_.T,
        index=loading_cols,
        columns=[f"PC{i+1}" for i in range(pca.n_components_)]
    )
    var_exp = pca.explained_variance_ratio_ * 100
    logger.info(f"[{label}] PCA n={n_valid}  "
                f"PC1={var_exp[0]:.1f}%  PC2={var_exp[1]:.1f}%")
    return {
        "loadings": loadings,
        "var_exp": var_exp,
        "n": n_valid,
        "label": label,
    }


# ---------------------------------------------------------------------------
# S_main: 現行（健診受診者あたり）二次医療圏
# ---------------------------------------------------------------------------

def load_main_district() -> pd.DataFrame:
    df = pd.read_csv(INTERIM_DIR / "B1_district_standardized.csv",
                     encoding="utf-8-sig")
    df["district_code"] = df["district_code"].astype(str).str.zfill(4)
    df = df[
        ~df["pref_name"].astype(str).str.contains("判別不可", na=True) &
        ~df["district_name"].astype(str).str.contains("判別不可", na=True)
    ].copy()
    df = df.drop_duplicates("district_code", keep="first").reset_index(drop=True)
    logger.info(f"S_main district loaded: {len(df)} 圏")
    return df


# ---------------------------------------------------------------------------
# S5a: log1p 変換した実数カウント（二次医療圏）
# ---------------------------------------------------------------------------

def build_logcount_district(df: pd.DataFrame) -> pd.DataFrame:
    """
    臨床3指標を log1p(実数カウント) に変換。
    スクリーニング2指標（HbA1c高値率・FPG異常率）は直接標準化済みのため変換不要。
    log変換によりスケールを揃えつつ、健診受診者数という共通分母の影響を排除する。
    """
    d = df.copy()
    for col, new_col in [
        ("hba1c_test_count", "hba1c_test_log"),
        ("B001_20_patients",  "B001_20_log"),
        ("B001_27_patients",  "B001_27_log"),
    ]:
        d[new_col] = np.log1p(d[col])
        # 元の生値が 0 や NaN の場合は NaN に戻す（秘匿値保持）
        d.loc[d[col].isna(), new_col] = np.nan
    return d


# ---------------------------------------------------------------------------
# S5b/c: 都道府県レベル・人口あたり
# ---------------------------------------------------------------------------

def load_pop_prefecture() -> pd.DataFrame:
    """
    統計局 令和5年（2023年）人口推計 都道府県別・年齢階級別 から
    65歳以上人口（pop_65plus）、40-74歳人口（pop_40_74）、
    全年齢合計（pop_total）を取得。
    """
    pop_age_path = POP_DIR / "pop_2023_age_prefecture.csv"
    df_age = pd.read_csv(pop_age_path, encoding="utf-8-sig")
    logger.info(f"年齢別人口 shape: {df_age.shape}, cols: {list(df_age.columns)}")

    # 65歳以上の合計
    age65_groups = ["65-69歳", "70-74歳", "75-79歳", "80-84歳", "85歳以上"]
    df_65 = (df_age[df_age["age_group"].isin(age65_groups)]
             .groupby("prefecture")["population"].sum()
             .reset_index()
             .rename(columns={"population": "pop_65plus"}))

    # 40-74歳（特定健診対象年齢）
    age4074_groups = [
        "40-44歳", "45-49歳", "50-54歳", "55-59歳",
        "60-64歳", "65-69歳", "70-74歳",
    ]
    df_4074 = (df_age[df_age["age_group"].isin(age4074_groups)]
               .groupby("prefecture")["population"].sum()
               .reset_index()
               .rename(columns={"population": "pop_40_74"}))

    # 全年齢合計
    df_tot = (df_age.groupby("prefecture")["population"].sum()
              .reset_index()
              .rename(columns={"population": "pop_total"}))

    pop = df_65.merge(df_4074, on="prefecture", how="outer")
    pop = pop.merge(df_tot, on="prefecture", how="outer")
    logger.info(f"都道府県人口データ: {len(pop)} 件")
    return pop


def build_pref_alt_denom(pref_df: pd.DataFrame, pop_df: pd.DataFrame) -> pd.DataFrame:
    """
    B2 都道府県データに人口分母を追加し、代替レート列を生成。
    マージキー: pref_name（都道府県名）
    """
    merged = pref_df.merge(pop_df, left_on="pref_name", right_on="prefecture",
                           how="left")
    na_cnt = merged["pop_65plus"].isna().sum()
    if na_cnt > 0:
        logger.warning(f"都道府県マージ 未照合: {na_cnt} 件 → 確認が必要")

    # 65歳以上人口あたり（per 1,000）
    for col, new_col in [
        ("hba1c_test_count", "hba1c_test_per65k"),
        ("B001_20_patients",  "B001_20_per65k"),
        ("B001_27_patients",  "B001_27_per65k"),
    ]:
        if col in merged.columns:
            denom65 = merged["pop_65plus"].replace(0, np.nan) / 1000
            merged[new_col] = (merged[col] / denom65).round(4)

    # 40-74歳人口あたり（per 1,000）
    for col, new_col in [
        ("hba1c_test_count", "hba1c_test_per4074k"),
        ("B001_20_patients",  "B001_20_per4074k"),
        ("B001_27_patients",  "B001_27_per4074k"),
    ]:
        if col in merged.columns:
            denom4074 = merged["pop_40_74"].replace(0, np.nan) / 1000
            merged[new_col] = (merged[col] / denom4074).round(4)

    # 全人口あたり（per 100,000）
    for col, new_col in [
        ("hba1c_test_count", "hba1c_test_per100k"),
        ("B001_20_patients",  "B001_20_per100k"),
        ("B001_27_patients",  "B001_27_per100k"),
    ]:
        if col in merged.columns:
            denom_tot = merged["pop_total"].replace(0, np.nan) / 100000
            merged[new_col] = (merged[col] / denom_tot).round(4)

    logger.info(f"都道府県 代替分母構築完了: {len(merged)} 件")
    return merged


# ---------------------------------------------------------------------------
# 安定性比較
# ---------------------------------------------------------------------------

def compare_stability(rho_main: pd.DataFrame,
                      rho_alt: pd.DataFrame,
                      threshold: float = 0.10) -> pd.DataFrame:
    """
    2つの相関行列の対応セルを比較し、差の絶対値が threshold 未満なら stable と判定。
    下三角のみ評価。
    """
    inds = rho_main.index.tolist()
    records = []
    n = len(inds)
    for i in range(n):
        for j in range(i + 1, n):
            r_m = rho_main.iloc[i, j]
            r_a = rho_alt.iloc[i, j] if i < len(rho_alt) and j < len(rho_alt) else np.nan
            diff = abs(r_m - r_a) if not (np.isnan(r_m) or np.isnan(r_a)) else np.nan
            stable = "stable" if (not np.isnan(diff) and diff < threshold) else (
                "unstable" if not np.isnan(diff) else "n/a")
            records.append({
                "pair": f"{inds[i]} × {inds[j]}",
                "rho_main": r_m,
                "rho_alt": r_a,
                "abs_diff": round(diff, 4) if not np.isnan(diff) else np.nan,
                "stable": stable,
            })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 図: PCA ローディング比較（横並び）
# ---------------------------------------------------------------------------

def plot_loadings_comparison(pca_results: list[dict],
                             out_path: Path):
    """
    各感度分析シナリオの PC1/PC2 ローディングを横並びで表示する棒グラフ。
    """
    n_scen = len(pca_results)
    fig, axes = plt.subplots(n_scen, 2, figsize=(10, 3.5 * n_scen),
                             constrained_layout=True)
    if n_scen == 1:
        axes = [axes]

    colors_pc1 = "#2196F3"
    colors_pc2 = "#FF7043"

    for row, res in enumerate(pca_results):
        ld = res["loadings"]
        ve = res["var_exp"]
        label = res["label"]
        indicators = INDICATOR_ORDER

        for col_idx, (pc, color) in enumerate(
            [("PC1", colors_pc1), ("PC2", colors_pc2)]
        ):
            ax = axes[row][col_idx]
            vals = [ld.loc[ind, pc] if ind in ld.index else 0 for ind in indicators]
            bars = ax.barh(indicators, vals, color=[
                color if abs(v) == max(abs(x) for x in vals) else "#BDBDBD"
                for v in vals
            ], edgecolor="white", linewidth=0.5)
            ax.axvline(0, color="black", linewidth=0.7)
            ax.set_xlim(-1, 1)
            ax.set_xlabel("Loading")
            pct = ve[int(pc[2]) - 1]
            ax.set_title(f"{label}  {pc} ({pct:.1f}%)", fontsize=9)
            ax.tick_params(labelsize=8)

    fig.suptitle("Denominator Sensitivity: PCA Loadings (PC1, PC2)", fontsize=11)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"図保存: {out_path}")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main():
    logger.info("=" * 60)
    logger.info("タスクE：代理分母感度分析（S5） 開始")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. 二次医療圏データロード
    # ------------------------------------------------------------------
    dist = load_main_district()

    # ------------------------------------------------------------------
    # 2. S_main：現行 (per 1,000 health-check participants)
    # ------------------------------------------------------------------
    cols_main = list(LABELS_MAIN.keys())
    rho_main, pval_main = spearman_matrix(dist, cols_main, LABELS_MAIN)
    pca_main = run_pca(dist, cols_main, LABELS_MAIN, "S_main (per 1k tested)")
    rho_main.to_csv(TABLE_DIR / "S5_main_correlation.csv", encoding="utf-8-sig")
    logger.info(f"S_main 相関行列:\n{rho_main.round(3).to_string()}")

    # ------------------------------------------------------------------
    # 3. S5a：log1p 実数カウント（二次医療圏）
    # ------------------------------------------------------------------
    dist_log = build_logcount_district(dist)
    cols_log = list(LABELS_LOG.keys())
    rho_log, pval_log = spearman_matrix(dist_log, cols_log, LABELS_LOG)
    pca_log = run_pca(dist_log, cols_log, LABELS_LOG,
                      "S5a (log-count, district)")
    rho_log.to_csv(TABLE_DIR / "S5a_district_correlation_logcount.csv",
                   encoding="utf-8-sig")
    logger.info(f"S5a log相関行列:\n{rho_log.round(3).to_string()}")

    stab_5a = compare_stability(rho_main, rho_log)
    stab_5a["scenario"] = "S5a_logcount_vs_main"

    # ------------------------------------------------------------------
    # 4. 都道府県データロード・人口分母追加
    # ------------------------------------------------------------------
    pref = pd.read_csv(INTERIM_DIR / "B2_prefecture_standardized.csv",
                       encoding="utf-8-sig")
    logger.info(f"B2 都道府県データ: {len(pref)} 件, cols: {list(pref.columns)[:10]}")

    pop = load_pop_prefecture()
    pref_alt = build_pref_alt_denom(pref, pop)

    # 都道府県版 S_main 相関（比較ベース: per 1k tested）
    cols_pref_main = [
        "hba1c_std_rate_pct", "fpg_std_rate_pct",
        "hba1c_test_per1k_tested", "B001_20_per1k_tested",
        "B001_27_per1k_tested",
    ]
    valid_pref_main = [c for c in cols_pref_main if c in pref_alt.columns]
    rho_pref_main = None
    if len(valid_pref_main) == len(cols_pref_main):
        rho_pref_main, _ = spearman_matrix(
            pref_alt, cols_pref_main, LABELS_MAIN
        )
    else:
        logger.warning("都道府県 main 比較用カラムが不足")

    # ------------------------------------------------------------------
    # 5. S5b：都道府県・65歳以上人口あたり
    # ------------------------------------------------------------------
    cols_per65 = list(LABELS_PER65.keys())
    valid_cols_65 = [c for c in cols_per65 if c in pref_alt.columns]
    if len(valid_cols_65) == len(cols_per65):
        rho_65, pval_65 = spearman_matrix(pref_alt, cols_per65, LABELS_PER65)
        pca_65 = run_pca(pref_alt, cols_per65, LABELS_PER65,
                         "S5b (per 65+ pop, pref)")
        rho_65.to_csv(TABLE_DIR / "S5b_prefecture_correlation_per65plus.csv",
                      encoding="utf-8-sig")
        logger.info(f"S5b 65+人口相関行列:\n{rho_65.round(3).to_string()}")

        if rho_pref_main is not None:
            stab_5b = compare_stability(rho_pref_main, rho_65)
            stab_5b["scenario"] = "S5b_per65plus_vs_pref_main"
        else:
            stab_5b = pd.DataFrame()
    else:
        pca_65 = None
        stab_5b = pd.DataFrame()
        logger.warning(f"S5b: カラム不足 {valid_cols_65}")

    # ------------------------------------------------------------------
    # 6. S5c：都道府県・全人口あたり
    # ------------------------------------------------------------------
    cols_pertot = list(LABELS_PERTOT.keys())
    valid_cols_tot = [c for c in cols_pertot if c in pref_alt.columns]
    if len(valid_cols_tot) == len(cols_pertot):
        rho_tot, pval_tot = spearman_matrix(pref_alt, cols_pertot, LABELS_PERTOT)
        pca_tot = run_pca(pref_alt, cols_pertot, LABELS_PERTOT,
                          "S5c (per total pop, pref)")
        rho_tot.to_csv(TABLE_DIR / "S5c_prefecture_correlation_pertotal.csv",
                       encoding="utf-8-sig")
        logger.info(f"S5c 全人口相関行列:\n{rho_tot.round(3).to_string()}")

        if rho_pref_main is not None:
            stab_5c = compare_stability(rho_pref_main, rho_tot)
            stab_5c["scenario"] = "S5c_pertotal_vs_pref_main"
        else:
            stab_5c = pd.DataFrame()
    else:
        pca_tot = None
        stab_5c = pd.DataFrame()
        logger.warning(f"S5c: カラム不足 {valid_cols_tot}")

    # ------------------------------------------------------------------
    # 6b. S5d：都道府県・40-74歳人口あたり
    # ------------------------------------------------------------------
    cols_per4074 = list(LABELS_PER4074.keys())
    valid_cols_4074 = [c for c in cols_per4074 if c in pref_alt.columns]
    if len(valid_cols_4074) == len(cols_per4074):
        rho_4074, pval_4074 = spearman_matrix(
            pref_alt, cols_per4074, LABELS_PER4074
        )
        pca_4074 = run_pca(
            pref_alt, cols_per4074, LABELS_PER4074,
            "S5d (per 40-74 pop, pref)",
        )
        rho_4074.to_csv(
            TABLE_DIR / "S5d_prefecture_correlation_per4074.csv",
            encoding="utf-8-sig",
        )
        logger.info(f"S5d 40-74歳人口相関行列:\n{rho_4074.round(3).to_string()}")

        if rho_pref_main is not None:
            stab_5d = compare_stability(rho_pref_main, rho_4074)
            stab_5d["scenario"] = "S5d_per4074_vs_pref_main"
        else:
            stab_5d = pd.DataFrame()
    else:
        pca_4074 = None
        stab_5d = pd.DataFrame()
        logger.warning(f"S5d: カラム不足 {valid_cols_4074}")

    # ------------------------------------------------------------------
    # 7. PCA ローディング比較テーブル
    # ------------------------------------------------------------------
    pca_results = [r for r in [pca_main, pca_log, pca_65, pca_tot, pca_4074]
                   if r is not None]

    loading_rows = []
    for res in pca_results:
        ld = res["loadings"]
        ve = res["var_exp"]
        for ind in INDICATOR_ORDER:
            row = {"scenario": res["label"],
                   "indicator": ind,
                   "n": res["n"]}
            for pc in ["PC1", "PC2", "PC3"]:
                if pc in ld.columns and ind in ld.index:
                    row[pc] = round(ld.loc[ind, pc], 4)
                else:
                    row[pc] = np.nan
            loading_rows.append(row)
    loading_tbl = pd.DataFrame(loading_rows)
    loading_tbl.to_csv(TABLE_DIR / "S5_pca_loadings_comparison.csv",
                       index=False, encoding="utf-8-sig")
    logger.info(f"PCAローディング比較テーブル保存")

    # ------------------------------------------------------------------
    # 8. 安定性サマリー
    # ------------------------------------------------------------------
    all_stab = pd.concat([df for df in [stab_5a, stab_5b, stab_5c, stab_5d]
                          if not df.empty], ignore_index=True)
    all_stab.to_csv(TABLE_DIR / "S5_stability_summary.csv",
                    index=False, encoding="utf-8-sig")

    n_stable = (all_stab["stable"] == "stable").sum()
    n_total = (all_stab["stable"] != "n/a").sum()
    logger.info(f"安定性サマリー: {n_stable}/{n_total} ペアが安定 "
                f"(|Δρ| < 0.10)")

    # ------------------------------------------------------------------
    # 9. 図作成
    # ------------------------------------------------------------------
    out_fig = FIG_DIR / "fig_S5_denominator_sensitivity.png"
    plot_loadings_comparison(pca_results, out_fig)

    # ------------------------------------------------------------------
    # 10. 最終レポート出力
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("S5 代理分母感度分析 結果サマリー")
    logger.info("=" * 60)

    logger.info("\n▼ S_main vs S5a（二次医療圏：per1k tested vs log-count）")
    logger.info(stab_5a[["pair", "rho_main", "rho_alt", "abs_diff", "stable"]]
                .to_string(index=False))

    if not stab_5b.empty:
        logger.info("\n▼ S_main vs S5b（都道府県：per1k tested vs per 65+人口）")
        logger.info(stab_5b[["pair", "rho_main", "rho_alt", "abs_diff", "stable"]]
                    .to_string(index=False))

    if not stab_5c.empty:
        logger.info("\n▼ S_main vs S5c（都道府県：per1k tested vs per 全人口）")
        logger.info(stab_5c[["pair", "rho_main", "rho_alt", "abs_diff", "stable"]]
                    .to_string(index=False))

    if not stab_5d.empty:
        logger.info("\n▼ S_main vs S5d（都道府県：per1k tested vs per 40-74歳人口）")
        logger.info(stab_5d[["pair", "rho_main", "rho_alt", "abs_diff", "stable"]]
                    .to_string(index=False))

    logger.info("\n▼ PC1/PC2 最大ローディング指標（シナリオ横断）")
    for res in pca_results:
        ld = res["loadings"]
        ve = res["var_exp"]
        pc1_top = ld["PC1"].abs().idxmax() if "PC1" in ld.columns else "—"
        pc2_top = ld["PC2"].abs().idxmax() if "PC2" in ld.columns else "—"
        logger.info(f"  {res['label']}: PC1→{pc1_top} ({ve[0]:.1f}%),  "
                    f"PC2→{pc2_top} ({ve[1]:.1f}%)")

    logger.info("\n出力ファイル:")
    for f in sorted(TABLE_DIR.glob("S5*.csv")):
        logger.info(f"  {f.name}")
    logger.info(f"  {out_fig.name}")
    logger.info("=" * 60)
    logger.info("タスクE 完了")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
