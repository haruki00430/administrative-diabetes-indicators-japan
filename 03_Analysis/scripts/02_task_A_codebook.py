# -*- coding: utf-8 -*-
"""
タスクA（後半）：コードブック作成・秘匿率集計
計画書 §2.2・§5 の要件を満たす

出力:
  02_Data/interim/A3_codebook.csv         - 各指標の定義・出典・単位・秘匿状況
  03_Analysis/results/tables/Table1_codebook.csv  - 論文 Table.1 の素
  02_Data/interim/A4_masking_rate.csv     - 地域別秘匿率表（付録用）
"""

import sys
from pathlib import Path
import logging
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
INTERIM_DIR = PROJECT_DIR / "02_Data" / "interim"
TABLE_DIR = PROJECT_DIR / "03_Analysis" / "results" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(INTERIM_DIR / "task_A_codebook.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ===================================================================
# コードブック定義（計画書 §2.2・§4 に基づく）
# ===================================================================

CODEBOOK = [
    {
        "indicator_id": "hba1c_high_rate_pct",
        "indicator_label_en": "HbA1c high rate (>=6.5%, among health checkup recipients)",
        "indicator_label_ja": "特定健診HbA1c高値率（≥6.5%）",
        "source": "NDB Open Data No.11, 特定健診 検査, HbA1C 二次医療圏別性年齢階級別分布.xlsx",
        "ndb_code": "—",
        "data_year": "FY2023（令和5年度、2023年4月〜2024年3月）",
        "unit": "%（受診者中の割合）",
        "denominator": "特定健診受診者総数（男女合計、40〜74歳）",
        "high_threshold": "≥6.5%（IFGカットオフ値に基づく、NGSP値）",
        "analysis_level": "二次医療圏・都道府県",
        "role_in_study": "診断・スクリーニング強度の代理指標",
        "limitations": "特定健診受診者（40〜74歳）に限定。受診率バイアスあり（健康意識の高い層が受けやすい）。",
    },
    {
        "indicator_id": "fpg_high_rate_pct",
        "indicator_label_en": "Fasting plasma glucose high rate (>=110 mg/dL, among health checkup recipients)",
        "indicator_label_ja": "特定健診空腹時血糖異常率（≥110 mg/dL）",
        "source": "NDB Open Data No.11, 特定健診 検査, 空腹時血糖 二次医療圏別性年齢階級別分布.xlsx",
        "ndb_code": "—",
        "data_year": "FY2023（令和5年度、2023年4月〜2024年3月）",
        "unit": "%（受診者中の割合）",
        "denominator": "特定健診受診者総数（男女合計、40〜74歳）",
        "high_threshold": "≥110 mg/dL（正常高値を含む耐糖能異常、空腹時）",
        "analysis_level": "二次医療圏・都道府県",
        "role_in_study": "診断・スクリーニング強度の代理指標（HbA1cと独立した経路）",
        "limitations": "空腹時血糖はHbA1cと異なる測定条件。随時血糖に切り替えた施設では欠損が生じる場合がある。",
    },
    {
        "indicator_id": "hba1c_test_count",
        "indicator_label_en": "HbA1c laboratory test count (medical claims)",
        "indicator_label_ja": "HbA1c検査算定回数（医療機関レセプト）",
        "source": "NDB Open Data No.11, 医科診療行為（算定回数）, D_検査, 二次医療圏別算定回数.xlsx",
        "ndb_code": "D005 / 診療行為コード: 160010010（ヘモグロビンA1c）",
        "data_year": "FY2024（令和6年度、2024年4月〜2025年3月）",
        "unit": "回（算定回数の生値）※タスクBで人口当たり率に変換",
        "denominator": "（後続：人口10万対に換算予定）",
        "high_threshold": "—",
        "analysis_level": "二次医療圏・都道府県",
        "role_in_study": "外来での糖尿病モニタリング・検査強度の代理指標",
        "limitations": "入院・外来の区別なく算定回数を集計。専門医集積地域で高くなりやすい。",
    },
    {
        "indicator_id": "B001_20_patients",
        "indicator_label_en": "Patients under B001-20 diabetes complication management fee",
        "indicator_label_ja": "B001-20糖尿病合併症管理料 患者数",
        "source": "NDB Open Data No.11, 医科診療行為（患者数）, B_医学管理等, 二次医療圏別患者数.xlsx",
        "ndb_code": "B001-20 / 診療行為コード: 113010010",
        "data_year": "FY2024（令和6年度、2024年4月〜2025年3月）",
        "unit": "人（患者数の生値）※タスクBで人口当たり率に変換",
        "denominator": "（後続：人口10万対に換算予定）",
        "high_threshold": "—",
        "analysis_level": "二次医療圏・都道府県",
        "role_in_study": "合併症（足病変・網膜症等）管理の強度・アクセスの代理指標",
        "limitations": "算定要件（指定施設のみ）があるため、実際の合併症有病率ではなく施設整備状況も反映する。",
    },
    {
        "indicator_id": "B001_27_patients",
        "indicator_label_en": "Patients under B001-27 diabetes dialysis prevention guidance fee",
        "indicator_label_ja": "B001-27糖尿病透析予防指導管理料 患者数",
        "source": "NDB Open Data No.11, 医科診療行為（患者数）, B_医学管理等, 二次医療圏別患者数.xlsx",
        "ndb_code": "B001-27 / 診療行為コード: 113013610",
        "data_year": "FY2024（令和6年度、2024年4月〜2025年3月）",
        "unit": "人（患者数の生値）※タスクBで人口当たり率に変換",
        "denominator": "（後続：人口10万対に換算予定）",
        "high_threshold": "—",
        "analysis_level": "二次医療圏・都道府県",
        "role_in_study": "腎症重症化予防介入の強度の代理指標（下流のアウトカム管理）",
        "limitations": "特定要件（eGFR低下患者等）を満たす場合のみ算定。重症腎症患者数の代理として読む際は注意が必要。",
    },
    {
        "indicator_id": "antidiabetic_drug_qty",
        "indicator_label_en": "Antidiabetic drug prescription quantity (outpatient dispensing, drug class 396)",
        "indicator_label_ja": "抗糖尿病薬（薬効分類396）院外処方数量",
        "source": "NDB Open Data No.11, 処方薬, 【内服】外来（院外）_都道府県別薬効分類別数量.xlsx",
        "ndb_code": "薬効分類コード: 396（糖尿病剤）",
        "data_year": "FY2024（令和6年度、2024年4月〜2025年3月）",
        "unit": "（処方数量の合計）※タスクBで人口当たり率に変換",
        "denominator": "（後続：人口当たり換算予定）",
        "high_threshold": "—",
        "analysis_level": "都道府県のみ（二次医療圏データは公開なし）",
        "role_in_study": "外来での薬物治療強度の代理指標（頑健性チェック・都道府県のみ）",
        "limitations": "【重要】NDB No.11において処方薬データは都道府県レベルのみ公開。"
                       "二次医療圏（約335圏）レベルの集計ファイルは存在しないため、"
                       "本研究の主解析（二次医療圏）では使用しない。"
                       "都道府県レベルの頑健性チェック（n=47）でのみ追加指標として使用する。"
                       "詳細は実施報告書参照。",
    },
]


# ===================================================================
# 秘匿率集計（地域別）
# ===================================================================

def compute_masking_rates(dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    二次医療圏データ（A1_district_raw.csv）から地域別秘匿率を算出。
    計画書 §5 の規則に従い、秘匿セルの割合を指標ごとに記録する。
    """
    logger.info("秘匿率集計を開始")

    target_cols = {
        "B001_20_patients": "B001-20糖尿病合併症管理料患者数",
        "B001_27_patients": "B001-27糖尿病透析予防指導患者数",
        "hba1c_test_count": "HbA1c検査算定回数",
        "hba1c_high_rate_pct": "特定健診HbA1c高値率",
        "fpg_high_rate_pct": "特定健診FPG異常率",
    }

    n_total = len(dist_df)
    summary_records = []
    for col, label in target_cols.items():
        if col not in dist_df.columns:
            continue
        n_masked = dist_df[col].isna().sum()
        mask_pct = n_masked / n_total * 100
        summary_records.append({
            "indicator_id": col,
            "indicator_label_ja": label,
            "n_districts_total": n_total,
            "n_masked": int(n_masked),
            "masking_rate_pct": round(mask_pct, 2),
            "note": "秘匿値（10未満）はNaNとして記録。補完なし。" if n_masked > 0 else "秘匿なし",
        })

    # 地域別秘匿状況（都道府県単位で集計）
    pref_records = []
    for pref, grp in dist_df.groupby("pref_name"):
        row = {"pref_name": pref}
        for col in target_cols:
            if col in dist_df.columns:
                n_m = grp[col].isna().sum()
                row[f"{col}_masked_n"] = int(n_m)
                row[f"{col}_masked_pct"] = round(n_m / len(grp) * 100, 1)
        pref_records.append(row)

    df_summary = pd.DataFrame(summary_records)
    df_pref = pd.DataFrame(pref_records)

    # 秘匿率が高い都道府県を特定（B001_20で30%超）
    if "B001_20_patients_masked_pct" in df_pref.columns:
        high_mask = df_pref[df_pref["B001_20_patients_masked_pct"] > 30]
        if len(high_mask) > 0:
            logger.warning(f"B001_20 秘匿率>30%の都道府県: {list(high_mask['pref_name'])}")

    logger.info(f"秘匿率サマリー:\n{df_summary[['indicator_label_ja','n_masked','masking_rate_pct']].to_string()}")

    return df_summary, df_pref


# ===================================================================
# 記述統計サマリー（Table.1の素）
# ===================================================================

def compute_descriptive_stats(dist_df: pd.DataFrame) -> pd.DataFrame:
    """
    各指標の記述統計（n, mean, SD, min, max, 秘匿数）を算出。
    論文 Table.1 の素材。
    """
    cols = {
        "hba1c_high_rate_pct": "特定健診HbA1c高値率（%）",
        "fpg_high_rate_pct": "特定健診FPG異常率（%）",
        "hba1c_test_count": "HbA1c検査算定回数（生値）",
        "B001_20_patients": "B001-20患者数（生値）",
        "B001_27_patients": "B001-27患者数（生値）",
    }

    records = []
    for col, label in cols.items():
        if col not in dist_df.columns:
            continue
        s = dist_df[col].dropna()
        records.append({
            "indicator": col,
            "label": label,
            "n_valid": len(s),
            "n_masked": dist_df[col].isna().sum(),
            "mean": round(s.mean(), 3),
            "sd": round(s.std(), 3),
            "median": round(s.median(), 3),
            "min": round(s.min(), 3),
            "max": round(s.max(), 3),
            "p25": round(s.quantile(0.25), 3),
            "p75": round(s.quantile(0.75), 3),
        })

    return pd.DataFrame(records)


# ===================================================================
# メイン実行
# ===================================================================

def main():
    logger.info("タスクA（後半）：コードブック・秘匿率集計開始")

    # 二次医療圏データ読み込み
    dist_path = INTERIM_DIR / "A1_district_raw.csv"
    if not dist_path.exists():
        logger.error(f"データファイルが見つかりません: {dist_path}")
        logger.error("先に 01_task_A_data_extraction.py を実行してください")
        return

    dist_df = pd.read_csv(dist_path, encoding="utf-8-sig")
    logger.info(f"二次医療圏データ読み込み: {len(dist_df)} 行")

    # 1. コードブック保存
    codebook_df = pd.DataFrame(CODEBOOK)
    codebook_path = INTERIM_DIR / "A3_codebook.csv"
    codebook_df.to_csv(codebook_path, index=False, encoding="utf-8-sig")
    logger.info(f"コードブック保存: {codebook_path}")

    # 論文Table.1用（英語・簡潔版）
    table1_cols = ["indicator_id", "indicator_label_en", "ndb_code",
                   "data_year", "unit", "analysis_level", "role_in_study"]
    table1 = codebook_df[table1_cols].copy()
    table1_path = TABLE_DIR / "Table1_codebook.csv"
    table1.to_csv(table1_path, index=False, encoding="utf-8-sig")
    logger.info(f"Table.1（論文用）保存: {table1_path}")

    # 2. 秘匿率集計
    mask_summary, mask_pref = compute_masking_rates(dist_df)
    mask_summary.to_csv(INTERIM_DIR / "A4_masking_summary.csv", index=False, encoding="utf-8-sig")
    mask_pref.to_csv(INTERIM_DIR / "A4_masking_by_prefecture.csv", index=False, encoding="utf-8-sig")
    logger.info("秘匿率テーブル保存完了")

    # 付録用（論文Appendix）
    mask_pref.to_csv(TABLE_DIR / "Appendix_masking_rate_by_prefecture.csv",
                     index=False, encoding="utf-8-sig")

    # 3. 記述統計
    desc_df = compute_descriptive_stats(dist_df)
    desc_path = TABLE_DIR / "A5_descriptive_stats_district.csv"
    desc_df.to_csv(desc_path, index=False, encoding="utf-8-sig")
    logger.info(f"記述統計保存: {desc_path}")
    logger.info(f"\n{desc_df[['label','n_valid','mean','sd','min','max']].to_string()}")

    # 都道府県データも記述統計
    pref_path = INTERIM_DIR / "A2_prefecture_raw.csv"
    if pref_path.exists():
        pref_df = pd.read_csv(pref_path, encoding="utf-8-sig")
        desc_pref = compute_descriptive_stats(pref_df)
        desc_pref.to_csv(TABLE_DIR / "A5_descriptive_stats_prefecture.csv",
                         index=False, encoding="utf-8-sig")
        logger.info("都道府県 記述統計保存完了")

    logger.info("=" * 50)
    logger.info("タスクA 全工程完了")
    logger.info("成果物:")
    logger.info(f"  {INTERIM_DIR / 'A1_district_raw.csv'}    ← 二次医療圏生データ")
    logger.info(f"  {INTERIM_DIR / 'A2_prefecture_raw.csv'}  ← 都道府県生データ")
    logger.info(f"  {INTERIM_DIR / 'A3_codebook.csv'}        ← コードブック（詳細版）")
    logger.info(f"  {TABLE_DIR / 'Table1_codebook.csv'}      ← 論文Table.1の素")
    logger.info(f"  {INTERIM_DIR / 'A4_masking_summary.csv'} ← 秘匿率サマリー")
    logger.info(f"  {INTERIM_DIR / 'A4_masking_by_prefecture.csv'} ← 都道府県別秘匿率（付録）")
    logger.info(f"  {TABLE_DIR / 'A5_descriptive_stats_district.csv'} ← 記述統計（圏）")
    logger.info("次ステップ: 03_task_B_standardization.py を実行")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
