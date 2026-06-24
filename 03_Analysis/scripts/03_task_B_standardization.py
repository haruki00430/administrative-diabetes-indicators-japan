# -*- coding: utf-8 -*-
"""
タスクB：年齢標準化（直接法）
計画書 §4 Step 1・タスクB の要件を満たす

【年齢標準化の方針】
1. 特定健診指標（HbA1c高値率・FPG異常率）：
   直接法。健診受診者数を年齢区分（40-44, 45-49, ..., 70-74）別に集計し、
   2020年国勢調査の全国人口（40-74歳、5歳階級）を基準人口として直接標準化。

2. 臨床指標（B001-20患者数・B001-27患者数・D005 HbA1c算定回数）：
   NDB No.11の二次医療圏別ファイルには年齢別内訳が存在しない（集計値のみ）。
   直接法の適用には年齢別データが必要なため、代替として
   「特定健診受診者数（hba1c_total_n）」を代理分母として使用し、
   人口1,000人（受診者換算）あたりの率を算出する。
   ※この制約は Methods セクションに明記する。

【基準人口】
   令和2年（2020年）国勢調査 全国人口（40〜74歳、5歳階級別、男女計）
   出典: 総務省統計局 https://www.stat.go.jp/data/kokusei/2020/

出力:
  02_Data/interim/B1_district_standardized.csv  - 年齢標準化済み二次医療圏データ
  02_Data/interim/B2_prefecture_standardized.csv - 年齢標準化済み都道府県データ
  03_Analysis/results/tables/B3_standardization_comparison.csv - 標準化前後比較
"""

import sys
from pathlib import Path
import logging
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
NDB_BASE = PROJECT_DIR.parent.parent / "02_Data" / "raw" / "NDB_OpenData" / "No.11"
INTERIM_DIR = PROJECT_DIR / "02_Data" / "interim"
TABLE_DIR = PROJECT_DIR / "03_Analysis" / "results" / "tables"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(INTERIM_DIR / "task_B_standardization.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ===================================================================
# 基準人口（2020年国勢調査、全国、40-74歳、5歳階級別、男女計）
# 単位：人
# 出典: 総務省統計局 令和2年国勢調査 人口等基本集計
# ===================================================================
REFERENCE_POP = {
    "40-44": 7_671_000,
    "45-49": 9_302_000,
    "50-54": 8_262_000,
    "55-59": 7_566_000,
    "60-64": 7_680_000,
    "65-69": 9_063_000,
    "70-74": 9_095_000,
}
TOTAL_REF_POP = sum(REFERENCE_POP.values())
# 各年齢階級の重みを計算
AGE_WEIGHTS = {k: v / TOTAL_REF_POP for k, v in REFERENCE_POP.items()}

AGE_COL_MAP = {
    # 健診ファイルの列名 → 年齢階級
    "m_4044": "40-44", "f_4044": "40-44",
    "m_4549": "45-49", "f_4549": "45-49",
    "m_5054": "50-54", "f_5054": "50-54",
    "m_5559": "55-59", "f_5559": "55-59",
    "m_6064": "60-64", "f_6064": "60-64",
    "m_6569": "65-69", "f_6569": "65-69",
    "m_7074": "70-74", "f_7074": "70-74",
}


def clean_numeric(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if s in ("-", "‐", "－", ""):
        return np.nan
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return np.nan


# ===================================================================
# 直接標準化：特定健診 HbA1c 高値率
# ===================================================================

def standardize_hba1c_district(ndb_base: Path) -> pd.DataFrame:
    """
    特定健診 HbA1c の二次医療圏別・年齢階級別分布から直接標準化率を算出。

    年齢階級別高値率 = 高値（≥6.5%）人数_年齢計 / 受診者総数_年齢計
    直接標準化率 = Σ_age(rate_age × weight_age)
    """
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "HbA1C　二次医療圏別性年齢階級別分布.xlsx")
    logger.info(f"年齢標準化（HbA1c）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    df_raw.columns = [
        "pref_name", "district_code", "district_name", "hba1c_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]
    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    df_raw["district_code"] = df_raw["district_code"].ffill()
    df_raw["district_name"] = df_raw["district_name"].ffill()

    num_cols = [c for c in df_raw.columns if c.startswith(("m_", "f_")) and c not in ("m_total", "f_total")]
    num_cols += ["m_total", "f_total"]
    for col in num_cols:
        df_raw[col] = df_raw[col].apply(clean_numeric)

    HIGH_LEVELS = {"8.4以上", "8.0以上8.4未満", "6.5以上8.0未満"}
    df_raw["is_high"] = df_raw["hba1c_level"].isin(HIGH_LEVELS)

    age_groups = ["40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74"]

    # 年齢別の列ペア（男＋女の合計を使う）
    age_to_cols = {
        "40-44": ("m_4044", "f_4044"),
        "45-49": ("m_4549", "f_4549"),
        "50-54": ("m_5054", "f_5054"),
        "55-59": ("m_5559", "f_5559"),
        "60-64": ("m_6064", "f_6064"),
        "65-69": ("m_6569", "f_6569"),
        "70-74": ("m_7074", "f_7074"),
    }

    records = []
    for (pref, dcode, dname), grp in df_raw.groupby(
        ["pref_name", "district_code", "district_name"], sort=False
    ):
        # floatコード変換
        code_str = str(int(float(str(dcode)))) if str(dcode) not in ("", "nan") else ""
        code_str = code_str.zfill(4) if code_str.isdigit() else code_str

        # 年齢階級別標準化率の計算
        std_rate = 0.0
        any_valid = False
        crude_high_n = 0
        crude_total_n = 0

        for age in age_groups:
            mc, fc = age_to_cols[age]
            # 高値（is_high == True）の当該年齢人数
            high_m = grp.loc[grp["is_high"], mc].sum(skipna=True)
            high_f = grp.loc[grp["is_high"], fc].sum(skipna=True)
            # 全体（全レベル）の当該年齢人数
            total_m = grp[mc].sum(skipna=True)
            total_f = grp[fc].sum(skipna=True)

            high_n = high_m + high_f
            total_n = total_m + total_f
            crude_high_n += high_n
            crude_total_n += total_n

            if total_n > 0:
                age_rate = high_n / total_n
                std_rate += age_rate * AGE_WEIGHTS[age]
                any_valid = True

        crude_rate = (crude_high_n / crude_total_n * 100) if crude_total_n > 0 else np.nan
        std_rate_pct = std_rate * 100 if any_valid else np.nan

        records.append({
            "district_code": code_str,
            "district_name": str(dname),
            "pref_name": str(pref),
            "hba1c_crude_rate_pct": round(crude_rate, 4) if not np.isnan(crude_rate) else np.nan,
            "hba1c_std_rate_pct": round(std_rate_pct, 4) if not np.isnan(std_rate_pct) else np.nan,
            "hba1c_total_tested": crude_total_n,
        })

    result = pd.DataFrame(records)
    result = result[~result["district_name"].str.contains("判別不可|nan", na=True)].copy()
    logger.info(f"HbA1c 直接標準化完了: {len(result)} 圏")
    logger.info(f"  粗率   平均: {result['hba1c_crude_rate_pct'].mean():.3f} %")
    logger.info(f"  標準化率平均: {result['hba1c_std_rate_pct'].mean():.3f} %")
    return result


# ===================================================================
# 直接標準化：特定健診 FPG 高値率
# ===================================================================

def standardize_fpg_district(ndb_base: Path) -> pd.DataFrame:
    """特定健診 FPG の二次医療圏別直接標準化率"""
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "空腹時血糖　二次医療圏別性年齢階級別分布.xlsx")
    logger.info(f"年齢標準化（FPG）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    df_raw.columns = [
        "pref_name", "district_code", "district_name", "fpg_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]
    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    df_raw["district_code"] = df_raw["district_code"].ffill()
    df_raw["district_name"] = df_raw["district_name"].ffill()

    num_cols = [c for c in df_raw.columns if c.startswith(("m_", "f_"))]
    for col in num_cols:
        df_raw[col] = df_raw[col].apply(clean_numeric)

    HIGH_FPG = {"126以上", "110以上126未満"}
    df_raw["is_high"] = df_raw["fpg_level"].isin(HIGH_FPG)

    age_to_cols = {
        "40-44": ("m_4044", "f_4044"), "45-49": ("m_4549", "f_4549"),
        "50-54": ("m_5054", "f_5054"), "55-59": ("m_5559", "f_5559"),
        "60-64": ("m_6064", "f_6064"), "65-69": ("m_6569", "f_6569"),
        "70-74": ("m_7074", "f_7074"),
    }

    records = []
    for (pref, dcode, dname), grp in df_raw.groupby(
        ["pref_name", "district_code", "district_name"], sort=False
    ):
        code_str = str(int(float(str(dcode)))) if str(dcode) not in ("", "nan") else ""
        code_str = code_str.zfill(4) if code_str.isdigit() else code_str

        std_rate = 0.0
        any_valid = False
        crude_high_n = crude_total_n = 0

        for age in age_to_cols:
            mc, fc = age_to_cols[age]
            high_n = grp.loc[grp["is_high"], mc].sum(skipna=True) + grp.loc[grp["is_high"], fc].sum(skipna=True)
            total_n = grp[mc].sum(skipna=True) + grp[fc].sum(skipna=True)
            crude_high_n += high_n
            crude_total_n += total_n
            if total_n > 0:
                std_rate += (high_n / total_n) * AGE_WEIGHTS[age]
                any_valid = True

        crude_rate = (crude_high_n / crude_total_n * 100) if crude_total_n > 0 else np.nan
        std_rate_pct = std_rate * 100 if any_valid else np.nan

        records.append({
            "district_code": code_str,
            "fpg_crude_rate_pct": round(crude_rate, 4) if not np.isnan(crude_rate) else np.nan,
            "fpg_std_rate_pct": round(std_rate_pct, 4) if not np.isnan(std_rate_pct) else np.nan,
        })

    result = pd.DataFrame(records)
    logger.info(f"FPG 直接標準化完了: {len(result)} 圏")
    logger.info(f"  粗率   平均: {result['fpg_crude_rate_pct'].mean():.3f} %")
    logger.info(f"  標準化率平均: {result['fpg_std_rate_pct'].mean():.3f} %")
    return result


# ===================================================================
# 臨床指標の代理分母換算
# ===================================================================

def compute_clinical_rates(dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    B001-20, B001-27, D005 HbA1c検査 を
    特定健診受診者数（1,000人あたり）で割って率を算出。

    【注意・Methods記載事項】
    二次医療圏レベルの医科診療行為データには年齢別内訳が提供されていない。
    直接法の適用が技術的に不可能なため、特定健診受診者数を代理分母として使用する。
    これにより、異なる規模の医療圏間で比較可能な相対値が得られる。
    高齢化率の影響は PCA 解釈時に外的変数（aging_rate）との相関で評価する。
    """
    logger.info("臨床指標の代理分母換算")
    df = dist_df.copy()

    # 1,000受診者あたりの率（代理分母）
    denom = df["hba1c_total_n"].replace(0, np.nan)

    df["B001_20_per1k_tested"] = (df["B001_20_patients"] / denom * 1000).round(4)
    df["B001_27_per1k_tested"] = (df["B001_27_patients"] / denom * 1000).round(4)
    df["hba1c_test_per1k_tested"] = (df["hba1c_test_count"] / denom * 1000).round(4)

    logger.info(f"  B001-20/1000: mean={df['B001_20_per1k_tested'].mean():.3f}, "
                f"missing={df['B001_20_per1k_tested'].isna().sum()}")
    logger.info(f"  B001-27/1000: mean={df['B001_27_per1k_tested'].mean():.3f}, "
                f"missing={df['B001_27_per1k_tested'].isna().sum()}")
    logger.info(f"  HbA1c検査/1000: mean={df['hba1c_test_per1k_tested'].mean():.3f}, "
                f"missing={df['hba1c_test_per1k_tested'].isna().sum()}")

    return df


# ===================================================================
# 都道府県版（同様の処理）
# ===================================================================

def standardize_checkup_prefecture(ndb_base: Path) -> pd.DataFrame:
    """都道府県版 HbA1c・FPG 直接標準化"""
    records_hba1c = []
    records_fpg = []

    for fname, label, high_set, col_prefix in [
        ("HbA1C　都道府県別性年齢階級別分布.xlsx", "hba1c",
         {"8.4以上", "8.0以上8.4未満", "6.5以上8.0未満"}, "hba1c"),
        ("空腹時血糖　都道府県別性年齢階級別分布.xlsx", "fpg",
         {"126以上", "110以上126未満"}, "fpg"),
    ]:
        fp = ndb_base / "07_特定健診 検査" / "01_公費レセプトを含まないデータ" / fname
        df_raw = pd.read_excel(fp, header=None, skiprows=5)
        df_raw.columns = [
            "pref_name", "level",
            "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
            "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
        ]
        df_raw["pref_name"] = df_raw["pref_name"].ffill()
        for col in df_raw.columns[2:]:
            df_raw[col] = df_raw[col].apply(clean_numeric)

        df_raw["is_high"] = df_raw["level"].isin(high_set)
        age_to_cols = {
            "40-44": ("m_4044", "f_4044"), "45-49": ("m_4549", "f_4549"),
            "50-54": ("m_5054", "f_5054"), "55-59": ("m_5559", "f_5559"),
            "60-64": ("m_6064", "f_6064"), "65-69": ("m_6569", "f_6569"),
            "70-74": ("m_7074", "f_7074"),
        }

        for pref, grp in df_raw.groupby("pref_name", sort=False):
            if "判別不可" in str(pref):
                continue
            std_rate = crude_high = crude_total = 0
            for age, (mc, fc) in age_to_cols.items():
                hn = grp.loc[grp["is_high"], mc].sum(skipna=True) + grp.loc[grp["is_high"], fc].sum(skipna=True)
                tn = grp[mc].sum(skipna=True) + grp[fc].sum(skipna=True)
                crude_high += hn
                crude_total += tn
                if tn > 0:
                    std_rate += (hn / tn) * AGE_WEIGHTS[age]

            crude_r = (crude_high / crude_total * 100) if crude_total > 0 else np.nan
            std_r = std_rate * 100

            if col_prefix == "hba1c":
                records_hba1c.append({"pref_name": pref,
                                       "hba1c_crude_rate_pct": round(crude_r, 4) if not np.isnan(crude_r) else np.nan,
                                       "hba1c_std_rate_pct": round(std_r, 4),
                                       "hba1c_total_tested": crude_total})
            else:
                records_fpg.append({"pref_name": pref,
                                     "fpg_crude_rate_pct": round(crude_r, 4) if not np.isnan(crude_r) else np.nan,
                                     "fpg_std_rate_pct": round(std_r, 4)})

    df_hba1c = pd.DataFrame(records_hba1c)
    df_fpg = pd.DataFrame(records_fpg)
    merged = df_hba1c.merge(df_fpg, on="pref_name", how="outer")
    logger.info(f"都道府県 直接標準化完了: {len(merged)} 件")
    return merged


# ===================================================================
# メイン実行
# ===================================================================

def main():
    logger.info("========================================")
    logger.info("タスクB：年齢標準化 開始")
    logger.info(f"基準人口: 2020年国勢調査 40-74歳 全国人口 計 {TOTAL_REF_POP:,} 人")
    for age, w in AGE_WEIGHTS.items():
        logger.info(f"  {age}: {REFERENCE_POP[age]:,} 人 (重み {w:.4f})")
    logger.info("========================================")

    # --- 二次医療圏 ---
    # HbA1c・FPG 直接標準化
    hba1c_std = standardize_hba1c_district(NDB_BASE)
    fpg_std = standardize_fpg_district(NDB_BASE)

    # 直接標準化結果の重複除去（同一district_codeが複数ある場合は最初の行を保持）
    hba1c_std = hba1c_std.drop_duplicates("district_code", keep="first").reset_index(drop=True)
    fpg_std = fpg_std.drop_duplicates("district_code", keep="first").reset_index(drop=True)
    logger.info(f"HbA1c重複除去後: {len(hba1c_std)} 圏 / FPG重複除去後: {len(fpg_std)} 圏")

    # A1 ロード・クリーニング
    # 「判別不可」行を先に除外し、district_code の重複も解消する
    dist_raw = pd.read_csv(INTERIM_DIR / "A1_district_raw.csv", encoding="utf-8-sig")
    dist_raw["district_code"] = dist_raw["district_code"].astype(str).str.zfill(4)
    dist_raw = dist_raw[
        ~dist_raw["pref_name"].astype(str).str.contains("判別不可", na=True) &
        ~dist_raw["district_name"].astype(str).str.contains("判別不可", na=True)
    ].copy()
    dist_raw = dist_raw.drop_duplicates("district_code", keep="first").reset_index(drop=True)
    logger.info(f"A1 クリーニング後: {len(dist_raw)} 圏（判別不可・重複を除外）")

    # 健診標準化率をマージ
    dist = dist_raw.merge(
        hba1c_std[["district_code", "hba1c_crude_rate_pct", "hba1c_std_rate_pct"]],
        on="district_code", how="left"
    ).merge(
        fpg_std[["district_code", "fpg_crude_rate_pct", "fpg_std_rate_pct"]],
        on="district_code", how="left"
    )

    # 臨床指標 代理分母換算
    dist = compute_clinical_rates(dist)

    dist = dist.reset_index(drop=True)

    # 保存
    dist_out = INTERIM_DIR / "B1_district_standardized.csv"
    dist.to_csv(dist_out, index=False, encoding="utf-8-sig")
    logger.info(f"保存: {dist_out} ({len(dist)} 圏)")

    # --- 都道府県 ---
    pref_raw = pd.read_csv(INTERIM_DIR / "A2_prefecture_raw.csv", encoding="utf-8-sig")
    pref_std = standardize_checkup_prefecture(NDB_BASE)
    pref = pref_raw.merge(pref_std, on="pref_name", how="left")

    # 臨床指標 代理分母換算（都道府県）
    pref["hba1c_total_n_"] = pref["hba1c_total_n"]
    denom_p = pref["hba1c_total_n_"].replace(0, np.nan)
    pref["B001_20_per1k_tested"] = (pref["B001_20_patients"] / denom_p * 1000).round(4)
    pref["B001_27_per1k_tested"] = (pref["B001_27_patients"] / denom_p * 1000).round(4)
    pref["hba1c_test_per1k_tested"] = (pref["hba1c_test_count"] / denom_p * 1000).round(4)
    pref["antidiabetic_drug_per1k_tested"] = (pref["antidiabetic_drug_qty"] / denom_p * 1000).round(4)

    pref_out = INTERIM_DIR / "B2_prefecture_standardized.csv"
    pref.to_csv(pref_out, index=False, encoding="utf-8-sig")
    logger.info(f"保存: {pref_out} ({len(pref)} 件)")

    # --- 標準化前後比較テーブル ---
    comp = dist[["district_code", "district_name", "pref_name",
                  "hba1c_high_rate_pct", "hba1c_crude_rate_pct", "hba1c_std_rate_pct",
                  "fpg_high_rate_pct", "fpg_crude_rate_pct", "fpg_std_rate_pct"]].copy()
    comp_path = TABLE_DIR / "B3_standardization_comparison.csv"
    comp.to_csv(comp_path, index=False, encoding="utf-8-sig")
    logger.info(f"標準化前後比較: {comp_path}")

    # --- 最終解析用データセット（標準化済み5指標）---
    analysis_cols = [
        "district_code", "district_name", "pref_name",
        "hba1c_std_rate_pct",        # 特定健診HbA1c高値率（標準化）
        "fpg_std_rate_pct",           # 特定健診FPG異常率（標準化）
        "hba1c_test_per1k_tested",    # HbA1c検査算定（代理分母）
        "B001_20_per1k_tested",       # B001-20（代理分母）
        "B001_27_per1k_tested",       # B001-27（代理分母）
    ]
    analysis_df = dist[analysis_cols].dropna(
        subset=["hba1c_std_rate_pct", "fpg_std_rate_pct",
                "hba1c_test_per1k_tested"]
    ).copy()

    analysis_path = INTERIM_DIR / "B4_analysis_dataset_district.csv"
    analysis_df.to_csv(analysis_path, index=False, encoding="utf-8-sig")
    logger.info(f"解析用データセット（標準化済み）: {analysis_path}")
    logger.info(f"  有効圏数: {len(analysis_df)}")
    logger.info(f"  変数別欠損:\n{analysis_df[analysis_cols[3:]].isna().sum().to_string()}")

    logger.info("=" * 50)
    logger.info("タスクB 完了")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
