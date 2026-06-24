# -*- coding: utf-8 -*-
"""
タスクD：頑健性解析・感度分析
計画書 §5 Step 3・タスクD の要件を満たす

【実施項目】
D1. 解析単位の比較: 二次医療圏 vs 都道府県
    - 両単位で同一の相関行列を算出し比較
    - 級内相関（ICC）計算は省略（設計外）

D2. 外れ値除外感度分析
    - 都市部（東京都・大阪府）・特殊地域（沖縄県）を除外
    - 感度は「除外前後で相関係数の変化が±0.1未満」を頑健とみなす

D3. 指標代替感度分析（都道府県のみ）
    - 処方薬量（antidiabetic_drug）を6番目の指標として追加
    - 処方薬との Spearman 相関でカバレッジを評価

D4. MAUP（改変可能面積単位問題）の記述的評価
    - 圏レベルと県レベルの相関係数を比較し、スケール依存性を確認

出力:
  03_Analysis/results/tables/D1_district_vs_prefecture_correlation.csv
  03_Analysis/results/tables/D2_outlier_sensitivity.csv
  03_Analysis/results/tables/D3_drug_indicator_coverage.csv
  03_Analysis/results/tables/D4_maup_comparison.csv
  03_Analysis/results/figures/fig_D1_robustness_comparison.png
"""

import sys
from pathlib import Path
import logging
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=FutureWarning)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
INTERIM_DIR = PROJECT_DIR / "02_Data" / "interim"
FIG_DIR = PROJECT_DIR / "03_Analysis" / "results" / "figures"
TABLE_DIR = PROJECT_DIR / "03_Analysis" / "results" / "tables"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(INTERIM_DIR / "task_D_robustness.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

INDICATORS_DIST = [
    "hba1c_std_rate_pct", "fpg_std_rate_pct",
    "hba1c_test_per1k_tested", "B001_20_per1k_tested", "B001_27_per1k_tested",
]
INDICATORS_PREF = INDICATORS_DIST + ["antidiabetic_drug_per1k_tested"]

SHORT = {
    "hba1c_std_rate_pct":          "HbA1c_hr",
    "fpg_std_rate_pct":            "FPG_hr",
    "hba1c_test_per1k_tested":     "HbA1c_test",
    "B001_20_per1k_tested":        "B001_20",
    "B001_27_per1k_tested":        "B001_27",
    "antidiabetic_drug_per1k_tested": "Drug",
}
OUTLIER_PREFS = ["東京都", "大阪府", "沖縄県"]


def spearman_matrix(df: pd.DataFrame, indicators: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = len(indicators)
    rho_mat = np.full((n, n), np.nan)
    p_mat = np.full((n, n), np.nan)
    for i, vi in enumerate(indicators):
        for j, vj in enumerate(indicators):
            mask = df[[vi, vj]].notna().all(axis=1)
            if mask.sum() >= 10:
                r, p = stats.spearmanr(df.loc[mask, vi], df.loc[mask, vj])
                rho_mat[i, j] = round(r, 4)
                p_mat[i, j] = round(p, 4)
    short = [SHORT[k] for k in indicators]
    return (
        pd.DataFrame(rho_mat, index=short, columns=short),
        pd.DataFrame(p_mat, index=short, columns=short),
    )


def sig_stars(p):
    if np.isnan(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


# ===================================================================
# D1: 圏レベル vs 県レベルの相関行列比較
# ===================================================================

def d1_district_vs_prefecture(dist_df, pref_df):
    logger.info("D1: 二次医療圏 vs 都道府県 相関行列比較")

    rho_dist, p_dist = spearman_matrix(dist_df, INDICATORS_DIST)
    rho_pref, p_pref = spearman_matrix(pref_df, INDICATORS_DIST)

    # 差の計算（上三角のみ）
    diff = rho_pref - rho_dist
    n = len(INDICATORS_DIST)
    rows = []
    for i in range(n):
        for j in range(i + 1, n):
            ind_pair = f"{SHORT[INDICATORS_DIST[i]]} × {SHORT[INDICATORS_DIST[j]]}"
            rho_d = rho_dist.iloc[i, j]
            rho_p = rho_pref.iloc[i, j]
            d = rho_p - rho_d if not (np.isnan(rho_d) or np.isnan(rho_p)) else np.nan
            robust = "YES" if (not np.isnan(d) and abs(d) < 0.15) else "NO"
            rows.append({
                "Indicator_Pair": ind_pair,
                "Rho_District": rho_d,
                "P_District": p_dist.iloc[i, j],
                "Sig_District": sig_stars(p_dist.iloc[i, j]),
                "Rho_Prefecture": rho_p,
                "P_Prefecture": p_pref.iloc[i, j],
                "Sig_Prefecture": sig_stars(p_pref.iloc[i, j]),
                "Delta_Rho": round(d, 4) if not np.isnan(d) else np.nan,
                "Robust_Delta<0.15": robust,
                "n_District": dist_df[[INDICATORS_DIST[i], INDICATORS_DIST[j]]].notna().all(axis=1).sum(),
                "n_Prefecture": pref_df[[INDICATORS_DIST[i], INDICATORS_DIST[j]]].notna().all(axis=1).sum(),
            })

    df_out = pd.DataFrame(rows)
    save_path = TABLE_DIR / "D1_district_vs_prefecture_correlation.csv"
    df_out.to_csv(save_path, index=False, encoding="utf-8-sig")

    n_robust = (df_out["Robust_Delta<0.15"] == "YES").sum()
    n_total = len(df_out)
    logger.info(f"  圏 vs 県 比較: {n_robust}/{n_total} ペアで |Δρ| < 0.15 → 頑健と判定")
    logger.info(f"  保存: {save_path}")
    return df_out


# ===================================================================
# D2: 外れ値除外 感度分析
# ===================================================================

def d2_outlier_sensitivity(dist_df, pref_df):
    logger.info("D2: 外れ値除外 感度分析（東京都・大阪府・沖縄県）")

    scenarios = {
        "Full sample": dist_df,
        "Excl. Tokyo": dist_df[dist_df["pref_name"] != "東京都"],
        "Excl. Osaka":  dist_df[dist_df["pref_name"] != "大阪府"],
        "Excl. Okinawa": dist_df[dist_df["pref_name"] != "沖縄県"],
        "Excl. Tokyo+Osaka+Okinawa": dist_df[~dist_df["pref_name"].isin(OUTLIER_PREFS)],
    }

    # 最重要ペアの感度チェック
    key_pairs = [
        ("hba1c_std_rate_pct", "fpg_std_rate_pct"),
        ("hba1c_std_rate_pct", "B001_20_per1k_tested"),
        ("B001_20_per1k_tested", "B001_27_per1k_tested"),
        ("fpg_std_rate_pct", "hba1c_test_per1k_tested"),
    ]

    rows = []
    for scenario_name, df_s in scenarios.items():
        for xi, yi in key_pairs:
            mask = df_s[[xi, yi]].notna().all(axis=1)
            n = mask.sum()
            if n >= 10:
                rho, p = stats.spearmanr(df_s.loc[mask, xi], df_s.loc[mask, yi])
            else:
                rho, p = np.nan, np.nan
            rows.append({
                "Scenario": scenario_name,
                "n": n,
                "Pair": f"{SHORT[xi]} × {SHORT[yi]}",
                "Spearman_rho": round(rho, 4) if not np.isnan(rho) else np.nan,
                "p_value": round(p, 4) if not np.isnan(p) else np.nan,
                "Sig": sig_stars(p),
            })

    df_out = pd.DataFrame(rows)
    save_path = TABLE_DIR / "D2_outlier_sensitivity.csv"
    df_out.to_csv(save_path, index=False, encoding="utf-8-sig")

    # 感度チェック：全シナリオで有意かどうか
    for pair_name in df_out["Pair"].unique():
        sub = df_out[df_out["Pair"] == pair_name]
        n_sig = (sub["Sig"].isin(["*", "**", "***"])).sum()
        logger.info(f"  {pair_name}: {n_sig}/{len(sub)} シナリオで有意")

    logger.info(f"  保存: {save_path}")
    return df_out


# ===================================================================
# D3: 処方薬指標追加（都道府県レベル）
# ===================================================================

def d3_drug_indicator(pref_df):
    logger.info("D3: 処方薬指標の追加（都道府県レベル限定）")

    avail = [c for c in INDICATORS_PREF if c in pref_df.columns]
    rho_mat, p_mat = spearman_matrix(pref_df, avail)

    # 処方薬と他5指標の相関のみ抽出
    if "Drug" in rho_mat.columns:
        drug_corr = rho_mat["Drug"].drop("Drug").reset_index()
        drug_corr.columns = ["Indicator", "Rho_with_Drug"]
        drug_p = p_mat["Drug"].drop("Drug").reset_index()
        drug_p.columns = ["Indicator", "P_with_Drug"]
        drug_result = drug_corr.merge(drug_p, on="Indicator")
        drug_result["Sig"] = drug_result["P_with_Drug"].apply(sig_stars)
        drug_result["n"] = pref_df[["antidiabetic_drug_per1k_tested"]].notna().sum().values[0]
    else:
        drug_result = pd.DataFrame({"note": ["antidiabetic_drug_per1k_tested not available"]})

    save_path = TABLE_DIR / "D3_drug_indicator_coverage.csv"
    drug_result.to_csv(save_path, index=False, encoding="utf-8-sig")
    logger.info(f"  処方薬指標との相関:\n{drug_result.to_string()}")
    logger.info(f"  保存: {save_path}")
    return drug_result


# ===================================================================
# D4: MAUP 比較表（スケール依存性の記述的評価）
# ===================================================================

def d4_maup_summary(dist_df, pref_df, d1_result):
    logger.info("D4: MAUP スケール依存性サマリー")

    rows = []
    for _, row in d1_result.iterrows():
        direction_consistent = (
            not np.isnan(row["Rho_District"]) and not np.isnan(row["Rho_Prefecture"]) and
            np.sign(row["Rho_District"]) == np.sign(row["Rho_Prefecture"])
        )
        rows.append({
            "Indicator_Pair": row["Indicator_Pair"],
            "Rho_Secondary_District": row["Rho_District"],
            "Rho_Prefecture": row["Rho_Prefecture"],
            "Delta_Rho_Pref_minus_Dist": row["Delta_Rho"],
            "Direction_Consistent": "YES" if direction_consistent else "NO",
            "Robust": row["Robust_Delta<0.15"],
            "MAUP_Risk": (
                "Low" if row.get("Robust_Delta<0.15") == "YES" and direction_consistent else
                "Moderate" if direction_consistent else "High"
            ),
        })

    df_out = pd.DataFrame(rows)
    save_path = TABLE_DIR / "D4_maup_comparison.csv"
    df_out.to_csv(save_path, index=False, encoding="utf-8-sig")

    low = (df_out["MAUP_Risk"] == "Low").sum()
    mod = (df_out["MAUP_Risk"] == "Moderate").sum()
    high = (df_out["MAUP_Risk"] == "High").sum()
    logger.info(f"  MAUP リスク評価: Low={low}, Moderate={mod}, High={high}")
    logger.info(f"  保存: {save_path}")
    return df_out


# ===================================================================
# Figure D1: 頑健性比較チャート
# ===================================================================

def plot_robustness_comparison(d1_result: pd.DataFrame, d2_result: pd.DataFrame, save_path: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- 左パネル: 圏 vs 県 ρ比較 ---
    pairs = d1_result["Indicator_Pair"].tolist()
    rho_d = d1_result["Rho_District"].values
    rho_p = d1_result["Rho_Prefecture"].values
    y = np.arange(len(pairs))

    ax1.barh(y - 0.2, rho_d, height=0.35, label="Secondary district (n=335)", color="steelblue", alpha=0.75)
    ax1.barh(y + 0.2, rho_p, height=0.35, label="Prefecture (n=47)", color="coral", alpha=0.75)
    ax1.set_yticks(y)
    ax1.set_yticklabels(pairs, fontsize=8)
    ax1.set_xlabel("Spearman ρ", fontsize=9)
    ax1.axvline(0, color="black", lw=0.8)
    ax1.set_title("D1. District vs. Prefecture\nCorrelation Comparison", fontsize=10)
    ax1.legend(fontsize=8, loc="lower right")
    ax1.set_xlim(-0.6, 0.8)

    # --- 右パネル: 外れ値除外感度 ---
    key_pair = "HbA1c_hr × B001_20"
    sub = d2_result[d2_result["Pair"] == key_pair].copy()
    if len(sub) == 0:
        sub = d2_result[d2_result["Pair"] == d2_result["Pair"].iloc[0]].copy()

    scenarios = sub["Scenario"].tolist()
    rhos = sub["Spearman_rho"].values
    ax2.barh(range(len(scenarios)), rhos, color="steelblue", alpha=0.75)
    ax2.set_yticks(range(len(scenarios)))
    ax2.set_yticklabels(scenarios, fontsize=8)
    ax2.set_xlabel("Spearman ρ", fontsize=9)
    ax2.axvline(0, color="black", lw=0.8)
    ax2.set_title(
        f"D2. Outlier Sensitivity\n(Pair: {sub['Pair'].iloc[0] if len(sub) > 0 else 'N/A'})",
        fontsize=10,
    )

    fig.suptitle(
        "Figure D1. Robustness Checks: Spatial Scale and Outlier Sensitivity",
        fontsize=11, y=1.02,
    )
    plt.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Figure D1 保存: {save_path}")


# ===================================================================
# メイン実行
# ===================================================================

def main():
    logger.info("=" * 55)
    logger.info("タスクD：頑健性解析・感度分析 開始")
    logger.info("=" * 55)

    dist_df = pd.read_csv(INTERIM_DIR / "B4_analysis_dataset_district.csv", encoding="utf-8-sig")
    dist_df["district_code"] = dist_df["district_code"].astype(str).str.zfill(4)
    logger.info(f"二次医療圏データ: {len(dist_df)} 圏")

    pref_df = pd.read_csv(INTERIM_DIR / "B2_prefecture_standardized.csv", encoding="utf-8-sig")
    logger.info(f"都道府県データ: {len(pref_df)} 件")

    # D1
    d1_result = d1_district_vs_prefecture(dist_df, pref_df)

    # D2
    d2_result = d2_outlier_sensitivity(dist_df, pref_df)

    # D3
    d3_result = d3_drug_indicator(pref_df)

    # D4
    d4_result = d4_maup_summary(dist_df, pref_df, d1_result)

    # Figure
    plot_robustness_comparison(d1_result, d2_result, FIG_DIR / "fig_D1_robustness_comparison.png")

    # サマリー出力
    logger.info("\n" + "=" * 55)
    logger.info("【タスクD 総合サマリー】")
    logger.info(f"D1 - 頑健ペア (|Δρ|<0.15): "
                f"{(d1_result['Robust_Delta<0.15'] == 'YES').sum()}/{len(d1_result)}")
    logger.info(f"D4 - MAUP Low risk: {(d4_result['MAUP_Risk'] == 'Low').sum()}/{len(d4_result)}")

    # D2 感度サマリー
    for pair_name in d2_result["Pair"].unique():
        sub = d2_result[d2_result["Pair"] == pair_name]
        n_sig = sub["Sig"].isin(["*", "**", "***"]).sum()
        n_total = len(sub)
        logger.info(f"D2 - {pair_name}: {n_sig}/{n_total} シナリオで有意")

    logger.info("=" * 55)
    logger.info("タスクD 完了")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
