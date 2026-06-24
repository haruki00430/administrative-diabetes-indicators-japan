# -*- coding: utf-8 -*-
"""
タスクA：NDB No.11 糖尿病関連指標の抽出
対象：二次医療圏（主解析）・都道府県（頑健性チェック）
出力：02_Data/interim/ に保存

注意事項（計画書 §0より）:
- 本研究はNDB公開集計データのみを使用する生態学的研究
- 個票データは一切扱わない
- 秘匿（マスク）値は NaN として記録し、勝手に補完しない

処方薬データ制限に関する注記:
- 抗糖尿病薬処方データはNDB No.11において二次医療圏レベルのファイルが存在しない
- 都道府県レベルのファイルのみ利用可能なため、都道府県の頑健性チェックでのみ使用
- 詳細は実施報告書を参照
"""

import sys
import os
import logging
from pathlib import Path

import numpy as np
import pandas as pd

# パス設定
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
NDB_BASE = PROJECT_DIR.parent.parent / "02_Data" / "raw" / "NDB_OpenData" / "No.11"
OUT_DIR = PROJECT_DIR / "02_Data" / "interim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUT_DIR / "task_A_extraction.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ===================================================================
# 共通ユーティリティ
# ===================================================================

def clean_numeric(val):
    """秘匿値「‐」「-」をNaN変換、全角数字→半角、文字列→float"""
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if s in ("-", "‐", "－", ""):
        return np.nan
    # 全角数字→半角
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return np.nan


def apply_clean(df, cols):
    for c in cols:
        df[c] = df[c].apply(clean_numeric)
    return df


def count_masked(series):
    """秘匿（NaN）セル数を返す"""
    return series.isna().sum()


# ===================================================================
# Part 1: B医学管理等 二次医療圏別患者数（B001-20, B001-27）
# ===================================================================

def extract_B_district(ndb_base: Path) -> pd.DataFrame:
    """
    B医学管理等 二次医療圏別患者数.xlsx から
    B001-20（糖尿病合併症管理料）と B001-27（糖尿病透析予防指導管理料）の
    患者数を二次医療圏別に抽出する。

    Returns
    -------
    DataFrame: columns = [district_code, district_name, B001_20, B001_27]
               * 単位：患者数（生値）。率への変換はタスクBで実施。
    """
    fp = (ndb_base / "01_医科診療行為（患者数）"
          / "01_公費レセプトを含まないデータ"
          / "B_医学管理等" / "二次医療圏別患者数.xlsx")
    logger.info(f"読み込み: {fp.name}")

    df_raw = pd.read_excel(fp, header=None)

    # 行3=ヘッダー, 行4=二次医療圏コード(4桁), 行5=医療圏名, 行6〜=データ
    district_codes = df_raw.iloc[4, 6:].tolist()   # 二次医療圏コード（4桁）
    district_names = df_raw.iloc[5, 6:].tolist()   # 医療圏名
    n_districts = len(district_names)
    logger.info(f"二次医療圏数（Bデータ列）: {n_districts}")

    # ターゲット行を取得
    targets = {"B001_20": None, "B001_27": None}
    for idx, row in df_raw.iterrows():
        code = str(row.iloc[0]).strip()
        if code == "B001_20":
            targets["B001_20"] = idx
        elif code == "B001_27":
            targets["B001_27"] = idx
        if all(v is not None for v in targets.values()):
            break

    logger.info(f"B001_20 行インデックス: {targets['B001_20']}")
    logger.info(f"B001_27 行インデックス: {targets['B001_27']}")

    records = []
    for i, (dcode, dname) in enumerate(zip(district_codes, district_names)):
        if pd.isna(dname) or str(dname) == "nan":
            continue
        col_idx = 6 + i
        b20 = clean_numeric(df_raw.iloc[targets["B001_20"], col_idx])
        b27 = clean_numeric(df_raw.iloc[targets["B001_27"], col_idx])
        # 4桁コードが入っている列はスキップ（都道府県ラベル列=nan, コード列）
        dcode_str = str(dcode).strip() if pd.notna(dcode) else ""
        records.append({
            "district_code": dcode_str.zfill(4) if dcode_str.isdigit() else dcode_str,
            "district_name": str(dname).strip(),
            "B001_20_patients": b20,
            "B001_27_patients": b27,
        })

    result = pd.DataFrame(records)
    # 「二次医療圏判別不可」など特殊行を除外
    result = result[~result["district_name"].str.contains("判別不可|nan", na=True)].copy()

    logger.info(f"B医学管理等 抽出完了: {len(result)} 圏")
    logger.info(f"  B001_20 秘匿数: {count_masked(result['B001_20_patients'])}")
    logger.info(f"  B001_27 秘匿数: {count_masked(result['B001_27_patients'])}")

    return result


# ===================================================================
# Part 2: D_検査 二次医療圏別算定回数（HbA1c D005）
# ===================================================================

def extract_D_district(ndb_base: Path) -> pd.DataFrame:
    """
    D_検査 二次医療圏別算定回数.xlsx から
    D005 HbA1c（診療行為コード: 160010010）の算定回数を抽出する。
    """
    fp = (ndb_base / "01_医科診療行為（算定回数）"
          / "01_公費レセプトを含まないデータ"
          / "D_検査" / "二次医療圏別算定回数.xlsx")
    logger.info(f"読み込み: {fp.name}")

    df_raw = pd.read_excel(fp, header=None)

    pref_codes = df_raw.iloc[4, 6:].tolist()
    district_names = df_raw.iloc[5, 6:].tolist()
    n_districts = len(district_names)
    logger.info(f"二次医療圏数（Dデータ）: {n_districts}")

    # HbA1c行（診療行為コード=160010010）を探す
    hba1c_row = None
    for idx, row in df_raw.iterrows():
        if str(row.iloc[2]).strip() == "160010010":
            hba1c_row = idx
            break

    if hba1c_row is None:
        logger.error("HbA1c（160010010）行が見つかりません")
        return pd.DataFrame()

    logger.info(f"HbA1c算定回数 行インデックス: {hba1c_row}")

    records = []
    for i, (dcode, dname) in enumerate(zip(pref_codes, district_names)):
        if pd.isna(dname) or str(dname) == "nan":
            continue
        col_idx = 6 + i
        hba1c_cnt = clean_numeric(df_raw.iloc[hba1c_row, col_idx])
        dcode_str = str(dcode).strip() if pd.notna(dcode) else ""
        records.append({
            "district_code": dcode_str.zfill(4) if dcode_str.isdigit() else dcode_str,
            "district_name": str(dname).strip(),
            "hba1c_test_count": hba1c_cnt,
        })

    result = pd.DataFrame(records)
    result = result[~result["district_name"].str.contains("判別不可|nan", na=True)].copy()

    logger.info(f"D検査 抽出完了: {len(result)} 圏")
    logger.info(f"  HbA1c算定 秘匿数: {count_masked(result['hba1c_test_count'])}")

    return result


# ===================================================================
# Part 3: 特定健診 HbA1c 二次医療圏別（高値率計算）
# ===================================================================

def extract_checkup_hba1c_district(ndb_base: Path) -> pd.DataFrame:
    """
    特定健診 HbA1c 二次医療圏別性年齢階級別分布.xlsx から
    HbA1c高値率（≥6.5%）を二次医療圏別に算出する。

    構造（列）:
      Col0: 都道府県名, Col1: 二次医療圏番号, Col2: 二次医療圏名,
      Col3: HbA1c階層, Col4-10: 男（40-44...70-74）, Col11: 男中計,
      Col12-18: 女（40-44...70-74）, Col19: 女中計

    HbA1c高値 ≥6.5% 定義:
      「8.4以上」「8.0以上8.4未満」「6.5以上8.0未満」の合計
    """
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "HbA1C　二次医療圏別性年齢階級別分布.xlsx")
    logger.info(f"読み込み: {fp.name}")

    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    # 列割り当て
    df_raw.columns = [
        "pref_name", "district_code", "district_name", "hba1c_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]

    # ffill（都道府県名・医療圏名は先頭行のみ記入）
    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    df_raw["district_code"] = df_raw["district_code"].ffill()
    df_raw["district_name"] = df_raw["district_name"].ffill()

    # 数値クリーニング（秘匿「‐」→NaN）
    num_cols = ["m_4044","m_4549","m_5054","m_5559","m_6064","m_6569","m_7074","m_total",
                "f_4044","f_4549","f_5054","f_5559","f_6064","f_6569","f_7074","f_total"]
    df_raw = apply_clean(df_raw, num_cols)

    # 合計人数（男中計＋女中計）
    df_raw["total_both"] = df_raw["m_total"].fillna(0) + df_raw["f_total"].fillna(0)
    # どちらも NaN の場合は NaN に戻す
    both_nan = df_raw["m_total"].isna() & df_raw["f_total"].isna()
    df_raw.loc[both_nan, "total_both"] = np.nan

    # 高値（≥6.5%）フラグ
    HIGH_LEVELS = {"8.4以上", "8.0以上8.4未満", "6.5以上8.0未満"}
    df_raw["is_high"] = df_raw["hba1c_level"].isin(HIGH_LEVELS)

    # 医療圏別に集計
    records = []
    for (pref, code, dname), grp in df_raw.groupby(
        ["pref_name", "district_code", "district_name"], sort=False
    ):
        total = grp["total_both"].sum()
        high_total = grp.loc[grp["is_high"], "total_both"].sum()

        masked_count = grp["total_both"].isna().sum()
        high_rate = (high_total / total * 100) if total > 0 else np.nan

        # floatコード（101.0）→ int → zfill4（'0101'）
        code_str = str(int(code)).zfill(4) if pd.notna(code) else ""
        records.append({
            "pref_name": pref,
            "district_code": code_str,
            "district_name": dname,
            "hba1c_high_n": high_total,
            "hba1c_total_n": total,
            "hba1c_high_rate_pct": round(high_rate, 4) if not np.isnan(high_rate) else np.nan,
            "hba1c_masked_cells": masked_count,
        })

    result = pd.DataFrame(records)
    # 判別不可行など不要行を除外
    result = result[result["district_name"].notna()].copy()

    logger.info(f"HbA1c健診 抽出完了: {len(result)} 圏")
    logger.info(f"  HbA1c高値率 秘匿含む圏（1セル以上）: {(result['hba1c_masked_cells'] > 0).sum()}")
    logger.info(f"  hba1c_high_rate_pct 範囲: {result['hba1c_high_rate_pct'].min():.2f}"
                f" 〜 {result['hba1c_high_rate_pct'].max():.2f} %")

    return result


# ===================================================================
# Part 4: 特定健診 空腹時血糖 二次医療圏別（高値率計算）
# ===================================================================

def extract_checkup_fpg_district(ndb_base: Path) -> pd.DataFrame:
    """
    特定健診 空腹時血糖 二次医療圏別性年齢階級別分布.xlsx から
    空腹時血糖異常率（≥110 mg/dL）を算出する。

    FPG異常 ≥110 mg/dL 定義:
      「126以上」「110以上126未満」の合計
    """
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "空腹時血糖　二次医療圏別性年齢階級別分布.xlsx")
    logger.info(f"読み込み: {fp.name}")

    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    df_raw.columns = [
        "pref_name", "district_code", "district_name", "fpg_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]

    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    df_raw["district_code"] = df_raw["district_code"].ffill()
    df_raw["district_name"] = df_raw["district_name"].ffill()

    num_cols = ["m_4044","m_4549","m_5054","m_5559","m_6064","m_6569","m_7074","m_total",
                "f_4044","f_4549","f_5054","f_5559","f_6064","f_6569","f_7074","f_total"]
    df_raw = apply_clean(df_raw, num_cols)

    df_raw["total_both"] = df_raw["m_total"].fillna(0) + df_raw["f_total"].fillna(0)
    both_nan = df_raw["m_total"].isna() & df_raw["f_total"].isna()
    df_raw.loc[both_nan, "total_both"] = np.nan

    HIGH_FPG = {"126以上", "110以上126未満"}
    df_raw["is_high"] = df_raw["fpg_level"].isin(HIGH_FPG)

    records = []
    for (pref, code, dname), grp in df_raw.groupby(
        ["pref_name", "district_code", "district_name"], sort=False
    ):
        total = grp["total_both"].sum()
        high_total = grp.loc[grp["is_high"], "total_both"].sum()
        masked_count = grp["total_both"].isna().sum()
        high_rate = (high_total / total * 100) if total > 0 else np.nan

        code_str = str(int(code)).zfill(4) if pd.notna(code) else ""
        records.append({
            "pref_name": pref,
            "district_code": code_str,
            "district_name": dname,
            "fpg_high_n": high_total,
            "fpg_total_n": total,
            "fpg_high_rate_pct": round(high_rate, 4) if not np.isnan(high_rate) else np.nan,
            "fpg_masked_cells": masked_count,
        })

    result = pd.DataFrame(records)
    result = result[result["district_name"].notna()].copy()

    logger.info(f"空腹時血糖健診 抽出完了: {len(result)} 圏")
    logger.info(f"  FPG高値率 秘匿含む圏（1セル以上）: {(result['fpg_masked_cells'] > 0).sum()}")
    logger.info(f"  fpg_high_rate_pct 範囲: {result['fpg_high_rate_pct'].min():.2f}"
                f" 〜 {result['fpg_high_rate_pct'].max():.2f} %")

    return result


# ===================================================================
# Part 5: 都道府県レベル（頑健性チェック用） + 処方薬追加
# ===================================================================

def extract_B_prefecture(ndb_base: Path) -> pd.DataFrame:
    """B医学管理等 都道府県別患者数から B001-20, B001-27 を抽出"""
    fp = (ndb_base / "01_医科診療行為（患者数）"
          / "01_公費レセプトを含まないデータ"
          / "B_医学管理等" / "都道府県別患者数.xlsx")
    logger.info(f"読み込み（都道府県）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None)

    # 行3=ヘッダー: [分類コード, 分類名称, 診療行為コード, 診療行為, 点数, 総計, 北海道, 青森, ...]
    pref_names = df_raw.iloc[3, 6:].tolist()
    n_pref = len([x for x in pref_names if pd.notna(x)])
    logger.info(f"都道府県数: {n_pref}")

    targets = {"B001_20": None, "B001_27": None}
    for idx, row in df_raw.iterrows():
        code = str(row.iloc[0]).strip()
        if code == "B001_20":
            targets["B001_20"] = idx
        elif code == "B001_27":
            targets["B001_27"] = idx
        if all(v is not None for v in targets.values()):
            break

    records = []
    for i, pname in enumerate(pref_names):
        if pd.isna(pname):
            continue
        col_idx = 6 + i
        b20 = clean_numeric(df_raw.iloc[targets["B001_20"], col_idx])
        b27 = clean_numeric(df_raw.iloc[targets["B001_27"], col_idx])
        records.append({
            "pref_name": str(pname).strip(),
            "B001_20_patients": b20,
            "B001_27_patients": b27,
        })

    result = pd.DataFrame(records)
    logger.info(f"B医学管理等（都道府県）抽出完了: {len(result)} 件")
    return result


def extract_D_prefecture(ndb_base: Path) -> pd.DataFrame:
    """D_検査 都道府県別算定回数から HbA1c（D005）を抽出"""
    fp = (ndb_base / "01_医科診療行為（算定回数）"
          / "01_公費レセプトを含まないデータ"
          / "D_検査" / "都道府県別算定回数.xlsx")
    logger.info(f"読み込み（都道府県）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None)
    pref_names = df_raw.iloc[3, 6:].tolist()

    hba1c_row = None
    for idx, row in df_raw.iterrows():
        if str(row.iloc[2]).strip() == "160010010":
            hba1c_row = idx
            break

    records = []
    for i, pname in enumerate(pref_names):
        if pd.isna(pname):
            continue
        col_idx = 6 + i
        cnt = clean_numeric(df_raw.iloc[hba1c_row, col_idx])
        records.append({"pref_name": str(pname).strip(), "hba1c_test_count": cnt})

    return pd.DataFrame(records)


def extract_checkup_hba1c_prefecture(ndb_base: Path) -> pd.DataFrame:
    """
    特定健診 HbA1c 都道府県別 から高値率を算出。
    都道府県ファイルは 18列構造（二次医療圏コード列なし）:
      Col0: 都道府県名, Col1: 検査値階層,
      Col2-9: 男（40-44...70-74, 中計）, Col10-17: 女（40-44...70-74, 中計）
    """
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "HbA1C　都道府県別性年齢階級別分布.xlsx")
    logger.info(f"読み込み（都道府県HbA1c）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    df_raw.columns = [
        "pref_name", "hba1c_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]
    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    num_cols = ["m_total", "f_total"]
    df_raw = apply_clean(df_raw, num_cols)
    df_raw["total_both"] = df_raw["m_total"].fillna(0) + df_raw["f_total"].fillna(0)
    both_nan = df_raw["m_total"].isna() & df_raw["f_total"].isna()
    df_raw.loc[both_nan, "total_both"] = np.nan

    HIGH_LEVELS = {"8.4以上", "8.0以上8.4未満", "6.5以上8.0未満"}
    df_raw["is_high"] = df_raw["hba1c_level"].isin(HIGH_LEVELS)

    records = []
    for pref, grp in df_raw.groupby("pref_name", sort=False):
        total = grp["total_both"].sum()
        high_total = grp.loc[grp["is_high"], "total_both"].sum()
        masked = grp["total_both"].isna().sum()
        high_rate = (high_total / total * 100) if total > 0 else np.nan
        records.append({
            "pref_name": pref,
            "hba1c_high_rate_pct": round(high_rate, 4) if not np.isnan(high_rate) else np.nan,
            "hba1c_total_n": total,
            "hba1c_masked_cells": masked,
        })

    result = pd.DataFrame(records)
    result = result[result["pref_name"].notna()].copy()
    result = result[~result["pref_name"].str.contains("判別不可", na=True)].copy()
    logger.info(f"HbA1c健診（都道府県）抽出完了: {len(result)} 件")
    return result


def extract_checkup_fpg_prefecture(ndb_base: Path) -> pd.DataFrame:
    """
    特定健診 空腹時血糖 都道府県別 から高値率を算出。
    18列構造（都道府県ファイル）:
      Col0: 都道府県名, Col1: 検査値階層, Col2-9: 男, Col10-17: 女
    """
    fp = (ndb_base / "07_特定健診 検査"
          / "01_公費レセプトを含まないデータ"
          / "空腹時血糖　都道府県別性年齢階級別分布.xlsx")
    logger.info(f"読み込み（都道府県FPG）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None, skiprows=5)
    df_raw.columns = [
        "pref_name", "fpg_level",
        "m_4044", "m_4549", "m_5054", "m_5559", "m_6064", "m_6569", "m_7074", "m_total",
        "f_4044", "f_4549", "f_5054", "f_5559", "f_6064", "f_6569", "f_7074", "f_total",
    ]
    df_raw["pref_name"] = df_raw["pref_name"].ffill()
    num_cols = ["m_total", "f_total"]
    df_raw = apply_clean(df_raw, num_cols)
    df_raw["total_both"] = df_raw["m_total"].fillna(0) + df_raw["f_total"].fillna(0)
    both_nan = df_raw["m_total"].isna() & df_raw["f_total"].isna()
    df_raw.loc[both_nan, "total_both"] = np.nan

    HIGH_FPG = {"126以上", "110以上126未満"}
    df_raw["is_high"] = df_raw["fpg_level"].isin(HIGH_FPG)

    records = []
    for pref, grp in df_raw.groupby("pref_name", sort=False):
        total = grp["total_both"].sum()
        high_total = grp.loc[grp["is_high"], "total_both"].sum()
        masked = grp["total_both"].isna().sum()
        high_rate = (high_total / total * 100) if total > 0 else np.nan
        records.append({
            "pref_name": pref,
            "fpg_high_rate_pct": round(high_rate, 4) if not np.isnan(high_rate) else np.nan,
            "fpg_total_n": total,
            "fpg_masked_cells": masked,
        })

    result = pd.DataFrame(records)
    result = result[result["pref_name"].notna()].copy()
    result = result[~result["pref_name"].str.contains("判別不可", na=True)].copy()
    logger.info(f"FPG健診（都道府県）抽出完了: {len(result)} 件")
    return result


def extract_antidiabetic_drug_prefecture(ndb_base: Path) -> pd.DataFrame:
    """
    処方薬（内服）外来（院外）都道府県別薬効分類別数量.xlsx から
    糖尿病剤（薬効分類コード: 396）の処方数量合計を都道府県別に抽出する。

    ファイル構造（56列）:
      Col0: 薬効分類コード, Col1: 薬効分類名称, Col2: 医薬品コード, Col3: 医薬品名,
      Col4: 単位, Col5: 薬価基準収載医薬品コード, Col6: 薬価, Col7: 後発品区分,
      Col8: 総計, Col9-55: 都道府県（01北海道〜47沖縄）
      Row2: カラム名, Row3: 都道府県名, Row4+: データ行

    注意: 処方薬データは都道府県レベルのみ存在するため
          二次医療圏の主解析では使用せず、都道府県の頑健性チェックのみ。
          （詳細は実施報告書参照）
    """
    fp = (ndb_base / "05_処方薬"
          / "01_公費レセプトを含まないデータ"
          / "01_処方薬（内服／外用／注射）全"
          / "【内服】外来（院外）_都道府県別薬効分類別数量.xlsx")
    logger.info(f"読み込み（処方薬・都道府県）: {fp.name}")

    df_raw = pd.read_excel(fp, header=None)
    logger.info(f"処方薬ファイル shape: {df_raw.shape}")

    # 都道府県名はRow3のCol9以降
    pref_names = [str(x).strip() for x in df_raw.iloc[3, 9:] if pd.notna(x)]
    logger.info(f"都道府県数: {len(pref_names)}, 先頭5: {pref_names[:5]}")

    # データはRow4以降。薬効分類コード（Col0）をffillして396（糖尿病剤）でフィルタ
    data = df_raw.iloc[4:].copy()
    data.columns = range(len(data.columns))
    data[0] = data[0].ffill()  # 薬効分類コードのffill

    # Col0 == "396" の行を抽出
    mask_396 = data[0].astype(str).str.strip() == "396"
    df_396 = data[mask_396].copy()
    logger.info(f"糖尿病剤（396）行数: {len(df_396)}")

    if df_396.empty:
        logger.error("糖尿病剤（396）の行が見つかりません")
        return pd.DataFrame()

    # 都道府県列（Col9〜）を数値変換して合計
    records = []
    for i, pname in enumerate(pref_names):
        col_idx = 9 + i
        if col_idx < len(df_396.columns):
            qty_series = df_396[col_idx].apply(clean_numeric)
            total_qty = qty_series.sum(skipna=True) if not qty_series.isna().all() else np.nan
        else:
            total_qty = np.nan
        records.append({"pref_name": pname, "antidiabetic_drug_qty": total_qty})

    result = pd.DataFrame(records)
    # 都道府県名が数字コードのみの場合（「01」等）は除外
    result = result[~result["pref_name"].str.match(r"^\d+$", na=True)].copy()
    logger.info(f"処方薬（都道府県）抽出完了: {len(result)} 件")
    logger.info(f"  秘匿数: {count_masked(result['antidiabetic_drug_qty'])}")
    return result


# ===================================================================
# Part 6: 統合・保存
# ===================================================================

def merge_and_save_district(b_df, d_df, hba1c_df, fpg_df, out_dir: Path):
    """
    二次医療圏データを統合してCSV保存。
    マージキー: district_code（4桁、全ファイルに共通）
    医療圏名は都道府県をまたいで重複するため、コードをキーにする必須。
    """
    logger.info("=== 二次医療圏データ統合 ===")

    # 基盤: HbA1c健診（district_code + district_name + pref_name をすべて持つ）
    merged = hba1c_df[["district_code", "district_name", "pref_name",
                         "hba1c_high_rate_pct", "hba1c_total_n", "hba1c_masked_cells"]].copy()

    # FPG健診（district_codeをキーに）
    merged = merged.merge(
        fpg_df[["district_code", "fpg_high_rate_pct", "fpg_total_n", "fpg_masked_cells"]],
        on="district_code", how="outer"
    )

    # B001-20/27（district_codeをキーに）
    merged = merged.merge(
        b_df[["district_code", "B001_20_patients", "B001_27_patients"]],
        on="district_code", how="outer"
    )

    # D005 HbA1c算定（district_codeをキーに）
    merged = merged.merge(
        d_df[["district_code", "hba1c_test_count"]],
        on="district_code", how="outer"
    )

    # 並び替え
    col_order = [
        "district_code", "district_name", "pref_name",
        "hba1c_high_rate_pct", "hba1c_total_n", "hba1c_masked_cells",
        "fpg_high_rate_pct", "fpg_total_n", "fpg_masked_cells",
        "B001_20_patients", "B001_27_patients",
        "hba1c_test_count",
    ]
    merged = merged[[c for c in col_order if c in merged.columns]]
    merged = merged.sort_values("district_code").reset_index(drop=True)

    out_path = out_dir / "A1_district_raw.csv"
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"保存: {out_path}")
    logger.info(f"  行数: {len(merged)}, 列数: {len(merged.columns)}")
    logger.info(f"  欠損状況:\n{merged.isna().sum().to_string()}")

    return merged


def merge_and_save_prefecture(b_df, d_df, hba1c_df, fpg_df, drug_df, out_dir: Path):
    """都道府県データを統合してCSV保存"""
    logger.info("=== 都道府県データ統合 ===")

    merged = hba1c_df[["pref_name",
                         "hba1c_high_rate_pct", "hba1c_total_n"]].copy()
    merged = merged.merge(
        fpg_df[["pref_name", "fpg_high_rate_pct", "fpg_total_n"]],
        on="pref_name", how="outer"
    )
    merged = merged.merge(b_df, on="pref_name", how="outer")
    merged = merged.merge(d_df, on="pref_name", how="outer")
    if not drug_df.empty:
        merged = merged.merge(drug_df, on="pref_name", how="outer")

    merged = merged.sort_values("pref_name").reset_index(drop=True)

    out_path = out_dir / "A2_prefecture_raw.csv"
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"保存: {out_path}")
    logger.info(f"  行数: {len(merged)}, 列数: {len(merged.columns)}")

    return merged


# ===================================================================
# メイン実行
# ===================================================================

def main():
    logger.info("========================================")
    logger.info("タスクA：NDB No.11 データ抽出開始")
    logger.info(f"NDB_BASE: {NDB_BASE}")
    logger.info(f"OUT_DIR : {OUT_DIR}")
    logger.info("========================================")

    # 二次医療圏レベル
    b_dist = extract_B_district(NDB_BASE)
    d_dist = extract_D_district(NDB_BASE)
    hba1c_dist = extract_checkup_hba1c_district(NDB_BASE)
    fpg_dist = extract_checkup_fpg_district(NDB_BASE)
    dist_df = merge_and_save_district(b_dist, d_dist, hba1c_dist, fpg_dist, OUT_DIR)

    # 都道府県レベル
    b_pref = extract_B_prefecture(NDB_BASE)
    d_pref = extract_D_prefecture(NDB_BASE)
    hba1c_pref = extract_checkup_hba1c_prefecture(NDB_BASE)
    fpg_pref = extract_checkup_fpg_prefecture(NDB_BASE)
    drug_pref = extract_antidiabetic_drug_prefecture(NDB_BASE)
    pref_df = merge_and_save_prefecture(b_pref, d_pref, hba1c_pref, fpg_pref, drug_pref, OUT_DIR)

    logger.info("========================================")
    logger.info("タスクA 完了")
    logger.info(f"  二次医療圏データ: {len(dist_df)} 圏")
    logger.info(f"  都道府県データ  : {len(pref_df)} 件")
    logger.info("次ステップ: 02_task_A_codebook.py を実行")
    logger.info("========================================")


if __name__ == "__main__":
    main()
