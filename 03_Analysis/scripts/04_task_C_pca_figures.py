# -*- coding: utf-8 -*-
"""
タスクC：相関行列・PCA・図表作成
計画書 §5 Step 2・タスクC の要件を満たす

【手法】
1. Spearman相関行列（5指標 × 5指標）→ Fig.1 ヒートマップ
2. PCA（z-score標準化、3成分）→ Fig.2 バイプロット（PC1 vs PC2）
3. 散布図マトリックス（主要ペア）→ Fig.3
4. PC軸と外的変数の相関 → Table.2（軸命名の根拠）

【欠損値の扱い】
5指標のうち B001-20・B001-27 は秘匿によりNaN有り。
PCAはComplete Case（全5指標が揃っている圏のみ）で実施。
相関行列は各ペアごとにpairwiseで算出。

【外的変数（軸命名根拠）】
- aged65_ratio_tested: 健診受診者中 65-69歳+70-74歳の割合（代理高齢化率）
  二次医療圏別 HbA1c 健診ファイルの年齢階級列から算出。
- NDB No.11 には B001-2（救急管理）等の「医療資源」指標も別途取得可能だが、
  今回は手元データのみで完結させる。

出力:
  03_Analysis/results/figures/fig1_correlation_heatmap.png
  03_Analysis/results/figures/fig2_pca_biplot.png
  03_Analysis/results/figures/fig3_scatter_matrix.png
  03_Analysis/results/figures/fig4_cross_year.png  (都道府県版 5+1指標)
  03_Analysis/results/tables/Table2_pc_external_correlation.csv
  03_Analysis/results/tables/C1_spearman_correlation.csv
  02_Data/interim/C0_pca_dataset.csv  (PCA使用データ詳細)
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
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as pe

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=FutureWarning)

# Prefecture name → English abbreviation mapping (ISO-style romaji)
PREF_EN = {
    "北海道": "Hokkaido", "青森県": "Aomori", "岩手県": "Iwate", "宮城県": "Miyagi",
    "秋田県": "Akita", "山形県": "Yamagata", "福島県": "Fukushima", "茨城県": "Ibaraki",
    "栃木県": "Tochigi", "群馬県": "Gunma", "埼玉県": "Saitama", "千葉県": "Chiba",
    "東京都": "Tokyo", "神奈川県": "Kanagawa", "新潟県": "Niigata", "富山県": "Toyama",
    "石川県": "Ishikawa", "福井県": "Fukui", "山梨県": "Yamanashi", "長野県": "Nagano",
    "岐阜県": "Gifu", "静岡県": "Shizuoka", "愛知県": "Aichi", "三重県": "Mie",
    "滋賀県": "Shiga", "京都府": "Kyoto", "大阪府": "Osaka", "兵庫県": "Hyogo",
    "奈良県": "Nara", "和歌山県": "Wakayama", "鳥取県": "Tottori", "島根県": "Shimane",
    "岡山県": "Okayama", "広島県": "Hiroshima", "山口県": "Yamaguchi", "徳島県": "Tokushima",
    "香川県": "Kagawa", "愛媛県": "Ehime", "高知県": "Kochi", "福岡県": "Fukuoka",
    "佐賀県": "Saga", "長崎県": "Nagasaki", "熊本県": "Kumamoto", "大分県": "Oita",
    "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima", "沖縄県": "Okinawa",
}

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
NDB_BASE = PROJECT_DIR.parent.parent / "02_Data" / "raw" / "NDB_OpenData" / "No.11"
INTERIM_DIR = PROJECT_DIR / "02_Data" / "interim"
FIG_DIR = PROJECT_DIR / "03_Analysis" / "results" / "figures"
TABLE_DIR = PROJECT_DIR / "03_Analysis" / "results" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(INTERIM_DIR / "task_C_pca.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# 指標の短いラベル（図表用）
INDICATOR_LABELS = {
    "hba1c_std_rate_pct":       "HbA1c\nhigh rate\n(checkup %)",
    "fpg_std_rate_pct":         "FPG\nhigh rate\n(checkup %)",
    "hba1c_test_per1k_tested":  "HbA1c\ntest count\n(/1k tested)",
    "B001_20_per1k_tested":     "B001-20\nDM complication\n(/1k tested)",
    "B001_27_per1k_tested":     "B001-27\nDialysis prev.\n(/1k tested)",
}
INDICATOR_SHORT = {
    "hba1c_std_rate_pct":       "HbA1c_hr",
    "fpg_std_rate_pct":         "FPG_hr",
    "hba1c_test_per1k_tested":  "HbA1c_test",
    "B001_20_per1k_tested":     "B001_20",
    "B001_27_per1k_tested":     "B001_27",
}
INDICATORS = list(INDICATOR_LABELS.keys())

# ===================================================================
# 外的変数：代理高齢化率の算出
# ===================================================================

def compute_proxy_aging_rate(ndb_base: Path) -> pd.DataFrame:
    """
    二次医療圏別 健診受診者の65-74歳比率を「代理高齢化率」として算出。
    HbA1c 健診ファイルの年齢階級列（65-69歳、70-74歳 男女計）を使用。
    """
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "HbA1C　二次医療圏別性年齢階級別分布.xlsx")
    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    df_raw.columns = [
        "pref_name", "district_code", "district_name", "hba1c_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]
    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    df_raw["district_code"] = df_raw["district_code"].ffill()
    df_raw["district_name"] = df_raw["district_name"].ffill()
    df_raw = df_raw[~df_raw["pref_name"].astype(str).str.contains("判別不可", na=True)]
    df_raw = df_raw[~df_raw["district_name"].astype(str).str.contains("判別不可", na=True)]

    def clean_n(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip().translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        if s in ("-", "‐", "－", ""):
            return np.nan
        try:
            return float(s.replace(",", ""))
        except ValueError:
            return np.nan

    for col in ["m_6569", "m_7074", "m_total", "f_6569", "f_7074", "f_total"]:
        df_raw[col] = df_raw[col].apply(clean_n)

    records = []
    for (pref, dcode, dname), grp in df_raw.groupby(
        ["pref_name", "district_code", "district_name"], sort=False
    ):
        code_str = str(int(float(str(dcode)))) if str(dcode) not in ("", "nan") else ""
        code_str = code_str.zfill(4) if code_str.isdigit() else code_str

        total_n = grp["m_total"].sum(skipna=True) + grp["f_total"].sum(skipna=True)
        aged_n = (grp["m_6569"].sum(skipna=True) + grp["f_6569"].sum(skipna=True) +
                  grp["m_7074"].sum(skipna=True) + grp["f_7074"].sum(skipna=True))
        proxy_aging = (aged_n / total_n * 100) if total_n > 0 else np.nan
        records.append({"district_code": code_str, "proxy_aging_pct": round(proxy_aging, 4)})

    result = pd.DataFrame(records).drop_duplicates("district_code", keep="first")
    logger.info(f"代理高齢化率算出: {len(result)} 圏, 平均 {result['proxy_aging_pct'].mean():.2f}%")
    return result


# ===================================================================
# Fig.1: Spearman相関ヒートマップ
# ===================================================================

def plot_correlation_heatmap(df: pd.DataFrame, save_path: Path) -> pd.DataFrame:
    n_ind = len(INDICATORS)
    corr_mat = np.full((n_ind, n_ind), np.nan)
    pval_mat = np.full((n_ind, n_ind), np.nan)

    for i, vi in enumerate(INDICATORS):
        for j, vj in enumerate(INDICATORS):
            mask = df[[vi, vj]].notna().all(axis=1)
            n = mask.sum()
            if n >= 10:
                r, p = stats.spearmanr(df.loc[mask, vi], df.loc[mask, vj])
                corr_mat[i, j] = r
                pval_mat[i, j] = p
            else:
                corr_mat[i, j] = np.nan

    short_labels = [INDICATOR_SHORT[k] for k in INDICATORS]
    long_labels = [INDICATOR_LABELS[k] for k in INDICATORS]

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(corr_mat, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Spearman ρ", shrink=0.8)

    ax.set_xticks(range(n_ind))
    ax.set_yticks(range(n_ind))
    ax.set_xticklabels(long_labels, fontsize=8, ha="right", rotation=45)
    ax.set_yticklabels(long_labels, fontsize=8)

    for i in range(n_ind):
        for j in range(n_ind):
            if not np.isnan(corr_mat[i, j]):
                sig = ""
                if pval_mat[i, j] < 0.001:
                    sig = "***"
                elif pval_mat[i, j] < 0.01:
                    sig = "**"
                elif pval_mat[i, j] < 0.05:
                    sig = "*"
                txt = f"{corr_mat[i, j]:.2f}{sig}"
                color = "white" if abs(corr_mat[i, j]) > 0.6 else "black"
                ax.text(j, i, txt, ha="center", va="center", fontsize=8, color=color)

    ax.set_title(
        "Figure 1. Spearman Correlation Matrix of Five Diabetes Indicators\n"
        "(Secondary Medical Districts, NDB No.11, n varies by indicator)",
        fontsize=10, pad=12,
    )
    ax.text(0.01, -0.18,
            "***p<0.001  **p<0.01  *p<0.05 | B001-20: diabetes complication mgmt; "
            "B001-27: dialysis prevention guidance",
            transform=ax.transAxes, fontsize=7, color="gray")

    plt.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Fig.1 保存: {save_path}")

    # CSV出力
    df_corr = pd.DataFrame(corr_mat, index=short_labels, columns=short_labels).round(4)
    return df_corr


# ===================================================================
# Fig.2: PCA バイプロット
# ===================================================================

def run_pca_and_biplot(df_full: pd.DataFrame, save_path: Path, aging_df: pd.DataFrame = None):
    df_cc = df_full[INDICATORS + ["district_code", "district_name", "pref_name"]].dropna(
        subset=INDICATORS
    ).copy()
    logger.info(f"PCA complete case: {len(df_cc)} 圏 / 全 {len(df_full)} 圏")

    X = df_cc[INDICATORS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=min(3, len(INDICATORS)), random_state=42)
    scores = pca.fit_transform(X_scaled)
    loadings = pca.components_.T

    ev = pca.explained_variance_ratio_
    logger.info(f"  PC1 寄与率: {ev[0]*100:.1f}%, PC2: {ev[1]*100:.1f}%, "
                f"PC3: {ev[2]*100:.1f}% | 累積2: {(ev[0]+ev[1])*100:.1f}%")

    # 外的変数との相関
    if aging_df is not None:
        ext = df_cc.merge(aging_df, on="district_code", how="left")
        ext["PC1"] = scores[:, 0]
        ext["PC2"] = scores[:, 1]
        if len(scores) > 2:
            ext["PC3"] = scores[:, 2]
        aging_vals = ext["proxy_aging_pct"].values
        valid = ~np.isnan(aging_vals)
        if valid.sum() >= 10:
            for pc_idx, pc_label in enumerate(["PC1", "PC2", "PC3"][:len(ev)]):
                r, p = stats.spearmanr(scores[valid, pc_idx], aging_vals[valid])
                logger.info(f"  {pc_label} × 代理高齢化率: ρ={r:.3f}, p={p:.4f}")

    # --- バイプロット描画 ---
    fig, ax = plt.subplots(figsize=(9, 7))

    sc = ax.scatter(
        scores[:, 0], scores[:, 1],
        alpha=0.4, s=18, c="steelblue", linewidths=0, zorder=2,
    )

    short_keys = list(INDICATOR_SHORT.values())
    arrow_scale = 3.0
    for i, (lx, ly) in enumerate(loadings[:, :2]):
        ax.annotate(
            "", xy=(lx * arrow_scale, ly * arrow_scale), xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color="crimson", lw=2),
        )
        ax.text(lx * arrow_scale * 1.12, ly * arrow_scale * 1.12,
                short_keys[i], fontsize=9, color="crimson",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))

    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.axvline(0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel(f"PC1 ({ev[0]*100:.1f}% variance)", fontsize=10)
    ax.set_ylabel(f"PC2 ({ev[1]*100:.1f}% variance)", fontsize=10)
    ax.set_title(
        f"Figure 2. PCA Biplot of Five Diabetes Indicators\n"
        f"(n={len(df_cc)} secondary medical districts; cumulative variance PC1+PC2: "
        f"{(ev[0]+ev[1])*100:.1f}%)",
        fontsize=10,
    )
    ax.text(0.02, 0.02,
            "Arrows: variable loadings; Points: district scores\n"
            "HbA1c_hr=HbA1c high rate; FPG_hr=FPG high rate; "
            "HbA1c_test=HbA1c test count;\nB001_20=DM complication mgmt; B001_27=dialysis prev.",
            transform=ax.transAxes, fontsize=7, color="gray",
            verticalalignment="bottom")

    plt.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Fig.2 保存: {save_path}")

    return pca, scaler, scores, loadings, df_cc, ev


# ===================================================================
# Fig.3: 散布図マトリックス（主要ペア）
# ===================================================================

def plot_scatter_matrix(df: pd.DataFrame, save_path: Path):
    key_pairs = [
        ("hba1c_std_rate_pct", "fpg_std_rate_pct"),
        ("hba1c_std_rate_pct", "hba1c_test_per1k_tested"),
        ("hba1c_std_rate_pct", "B001_20_per1k_tested"),
        ("fpg_std_rate_pct",   "B001_20_per1k_tested"),
        ("B001_20_per1k_tested", "B001_27_per1k_tested"),
        ("hba1c_test_per1k_tested", "B001_27_per1k_tested"),
    ]
    x_labels = {
        "hba1c_std_rate_pct":      "HbA1c high rate (%, std.)",
        "fpg_std_rate_pct":        "FPG high rate (%, std.)",
        "hba1c_test_per1k_tested": "HbA1c test count (/1k tested)",
        "B001_20_per1k_tested":    "B001-20 (/1k tested)",
        "B001_27_per1k_tested":    "B001-27 (/1k tested)",
    }

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    axes = axes.flatten()

    for ax, (xi, yi) in zip(axes, key_pairs):
        mask = df[[xi, yi]].notna().all(axis=1)
        x = df.loc[mask, xi].values
        y = df.loc[mask, yi].values
        n = len(x)

        ax.scatter(x, y, alpha=0.35, s=15, c="steelblue", linewidths=0)

        if n >= 10:
            m, b, r, p, _ = stats.linregress(x, y)
            xfit = np.linspace(x.min(), x.max(), 100)
            ax.plot(xfit, m * xfit + b, color="crimson", lw=1.5)
            rho, rho_p = stats.spearmanr(x, y)
            sig = "***" if rho_p < 0.001 else ("**" if rho_p < 0.01 else ("*" if rho_p < 0.05 else ""))
            ax.set_title(f"ρ={rho:.2f}{sig}, n={n}", fontsize=9)

        ax.set_xlabel(x_labels.get(xi, xi), fontsize=8)
        ax.set_ylabel(x_labels.get(yi, yi), fontsize=8)
        ax.tick_params(labelsize=7)

    fig.suptitle(
        "Figure 3. Scatter Plots for Key Indicator Pairs\n"
        "(Secondary medical districts, NDB No.11; red line = OLS regression)",
        fontsize=11, y=1.01,
    )
    plt.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Fig.3 保存: {save_path}")


# ===================================================================
# Fig.4: 都道府県レベル 6指標比較（頑健性補足図）
# ===================================================================

def plot_prefecture_comparison(pref_df: pd.DataFrame, save_path: Path):
    pref_indicators = [
        "hba1c_std_rate_pct", "fpg_std_rate_pct",
        "hba1c_test_per1k_tested", "B001_20_per1k_tested",
        "B001_27_per1k_tested", "antidiabetic_drug_per1k_tested",
    ]
    labels = [
        "HbA1c\nhigh rate\n(checkup %)",
        "FPG\nhigh rate\n(checkup %)",
        "HbA1c\ntest count\n(/1k tested)",
        "B001-20\n(/1k tested)",
        "B001-27\n(/1k tested)",
        "Antidiabetic\ndrug\n(/1k tested)",
    ]

    avail = [c for c in pref_indicators if c in pref_df.columns]
    avail_labels = [labels[pref_indicators.index(c)] for c in avail]
    n = len(avail)

    if n < 2:
        logger.warning("都道府県データが不足 → Fig.4 スキップ")
        return

    pref_sub = pref_df[avail].dropna(how="all")
    pref_scaled = (pref_sub - pref_sub.mean()) / pref_sub.std()

    raw_names = pref_df.loc[pref_sub.index, "pref_name"] if "pref_name" in pref_df.columns else pref_sub.index
    pref_names = [PREF_EN.get(str(n), str(n)) for n in raw_names]

    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(pref_sub))
    width = 0.14
    colors = plt.cm.tab10(np.linspace(0, 0.9, n))

    for i, (col, lbl, color) in enumerate(zip(avail, avail_labels, colors)):
        vals = pref_scaled[col].values
        offset = (i - n / 2 + 0.5) * width
        ax.bar(x + offset, vals, width=width * 0.9, label=lbl.replace("\n", " "),
               color=color, alpha=0.75)

    ax.set_xticks(x)
    ax.set_xticklabels(pref_names, rotation=90, fontsize=6)
    ax.set_ylabel("Z-score (standardized)", fontsize=9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title(
        "Figure 4. Prefecture-level Z-scores of Six Diabetes Indicators\n"
        "(Robustness check; antidiabetic drug data available at prefecture level only)",
        fontsize=10,
    )
    ax.legend(loc="upper right", fontsize=7, ncol=3, framealpha=0.7)
    plt.tight_layout()
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Fig.4 保存: {save_path}")


# ===================================================================
# Table.2: PC軸と外的変数の相関
# ===================================================================

def compute_pc_external_correlations(
    pca, scaler, X_raw, df_cc: pd.DataFrame,
    aging_df: pd.DataFrame, save_path: Path
) -> pd.DataFrame:
    X_scaled = scaler.transform(X_raw)
    scores = pca.transform(X_scaled)
    n_pc = scores.shape[1]

    ext = df_cc.copy()
    for i in range(n_pc):
        ext[f"PC{i+1}"] = scores[:, i]

    ext = ext.merge(aging_df, on="district_code", how="left")
    ext_vars = [c for c in ["proxy_aging_pct"] if c in ext.columns]

    rows = []
    for ev_col in ext_vars:
        for pc_i in range(n_pc):
            pc_col = f"PC{pc_i+1}"
            mask = ext[[pc_col, ev_col]].notna().all(axis=1)
            n = mask.sum()
            if n >= 10:
                rho, p = stats.spearmanr(ext.loc[mask, pc_col], ext.loc[mask, ev_col])
            else:
                rho, p = np.nan, np.nan
            rows.append({
                "External_Variable": ev_col,
                f"PC{pc_i+1}_rho": round(rho, 4) if not np.isnan(rho) else np.nan,
                f"PC{pc_i+1}_p": round(p, 4) if not np.isnan(p) else np.nan,
                "n": n,
            })

    # ピボット
    table_rows = []
    for ev_col in ext_vars:
        row = {"External_Variable": ev_col}
        for pc_i in range(n_pc):
            subset = [r for r in rows if r["External_Variable"] == ev_col]
            if subset:
                rho_key = f"PC{pc_i+1}_rho"
                p_key = f"PC{pc_i+1}_p"
                if rho_key in subset[0]:
                    row[rho_key] = subset[0][rho_key]
                    row[p_key] = subset[0][p_key]
        table_rows.append(row)

    # PC軸ごとにまとめる
    result_rows = []
    for pc_i in range(n_pc):
        pc_col = f"PC{pc_i+1}"
        ev_ratio = pca.explained_variance_ratio_[pc_i]
        for ev_col in ext_vars:
            mask = ext[[pc_col, ev_col]].notna().all(axis=1)
            n = mask.sum()
            if n >= 10:
                rho, p = stats.spearmanr(ext.loc[mask, pc_col], ext.loc[mask, ev_col])
            else:
                rho, p = np.nan, np.nan
            result_rows.append({
                "PC": pc_col,
                "Explained_Variance": f"{ev_ratio*100:.1f}%",
                "External_Variable": ev_col,
                "Spearman_rho": round(rho, 4) if not np.isnan(rho) else np.nan,
                "p_value": round(p, 4) if not np.isnan(p) else np.nan,
                "n_valid": n,
                "Interpretation": (
                    "High aging burden districts have higher PC score" if (not np.isnan(rho) and rho > 0) else
                    "High aging burden districts have lower PC score" if (not np.isnan(rho) and rho < 0) else
                    "No significant association"
                ),
            })

    df_table = pd.DataFrame(result_rows)
    df_table.to_csv(save_path, index=False, encoding="utf-8-sig")
    logger.info(f"Table.2 保存: {save_path}")
    return df_table


# ===================================================================
# メイン実行
# ===================================================================

def main():
    logger.info("=" * 55)
    logger.info("タスクC：相関行列・PCA・図表作成 開始")
    logger.info("=" * 55)

    # データ読み込み
    df = pd.read_csv(INTERIM_DIR / "B4_analysis_dataset_district.csv", encoding="utf-8-sig")
    df["district_code"] = df["district_code"].astype(str).str.zfill(4)
    logger.info(f"解析データ読み込み: {len(df)} 圏, 列: {list(df.columns)}")

    pref_df = pd.read_csv(INTERIM_DIR / "B2_prefecture_standardized.csv", encoding="utf-8-sig")
    logger.info(f"都道府県データ: {len(pref_df)} 件")

    # 外的変数：代理高齢化率
    aging_df = compute_proxy_aging_rate(NDB_BASE)

    # --- Fig.1: 相関ヒートマップ ---
    corr_df = plot_correlation_heatmap(df, FIG_DIR / "fig1_correlation_heatmap.png")
    corr_df.to_csv(TABLE_DIR / "C1_spearman_correlation.csv", encoding="utf-8-sig")
    logger.info("Spearman相関行列:")
    logger.info(f"\n{corr_df.to_string()}")

    # --- Fig.2: PCA バイプロット ---
    pca, scaler, scores, loadings, df_cc, ev = run_pca_and_biplot(
        df, FIG_DIR / "fig2_pca_biplot.png", aging_df
    )

    # PCA ローディング詳細出力
    short_keys = list(INDICATOR_SHORT.values())
    df_loadings = pd.DataFrame(
        loadings[:, :3], index=short_keys,
        columns=[f"PC{i+1}_loading" for i in range(min(3, len(ev)))]
    ).round(4)
    df_loadings.to_csv(TABLE_DIR / "C2_pca_loadings.csv", encoding="utf-8-sig")
    logger.info(f"PCA loadings:\n{df_loadings.to_string()}")

    # PCA スコア保存
    df_scores = df_cc[["district_code", "district_name", "pref_name"]].copy()
    for i in range(len(ev)):
        df_scores[f"PC{i+1}"] = scores[:, i].round(4)
    df_scores.to_csv(INTERIM_DIR / "C0_pca_dataset.csv", index=False, encoding="utf-8-sig")

    # --- Fig.3: 散布図マトリックス ---
    plot_scatter_matrix(df, FIG_DIR / "fig3_scatter_matrix.png")

    # --- Fig.4: 都道府県比較 ---
    plot_prefecture_comparison(pref_df, FIG_DIR / "fig4_cross_year.png")

    # --- Table.2: PC × 外的変数相関 ---
    X_cc = df_cc[INDICATORS].values
    table2 = compute_pc_external_correlations(
        pca, scaler, X_cc, df_cc, aging_df,
        TABLE_DIR / "Table2_pc_external_correlation.csv"
    )
    logger.info(f"Table.2:\n{table2.to_string()}")

    # --- PCA 要約 ---
    logger.info("\n" + "=" * 55)
    logger.info("【PCA 結果サマリー】")
    logger.info(f"  PC1: {ev[0]*100:.1f}% variance")
    logger.info(f"  PC2: {ev[1]*100:.1f}% variance")
    if len(ev) > 2:
        logger.info(f"  PC3: {ev[2]*100:.1f}% variance")
    logger.info(f"  累積 PC1+PC2: {(ev[0]+ev[1])*100:.1f}%")

    logger.info("\n【PC1 上位ローディング】")
    pc1 = df_loadings["PC1_loading"].abs().sort_values(ascending=False)
    for k, v in pc1.items():
        logger.info(f"  {k}: {df_loadings.loc[k, 'PC1_loading']:.3f}")

    logger.info("\n【PC2 上位ローディング】")
    pc2 = df_loadings["PC2_loading"].abs().sort_values(ascending=False)
    for k, v in pc2.items():
        logger.info(f"  {k}: {df_loadings.loc[k, 'PC2_loading']:.3f}")

    logger.info("=" * 55)
    logger.info("タスクC 完了")
    logger.info("=" * 55)


if __name__ == "__main__":
    main()
