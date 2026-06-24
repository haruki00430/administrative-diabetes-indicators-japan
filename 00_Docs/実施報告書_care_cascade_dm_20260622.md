# 論文②「What Do Administrative Healthcare Counts Really Measure?」実施報告書

**作成日**: 2026年6月22日  
**プロジェクト**: NDB_XXX_care_cascade_dm（NDB 方法論ライン・論文②）  
**論文タイトル（仮）**: "What Do Administrative Healthcare Counts Really Measure? Triangulating Diabetes Burden Across Prescription, Laboratory, Claims, and Survey-Based Indicators in Japan"  
**担当**: Claude Sonnet 4.6  
**報告対象**: タスクA〜F の全実施工程・発生エラー・成果物・完了条件チェック  

**一次資料（唯一の真実源）**:  
- `00_Docs/03_Research/論文2_計画書兼作業指示書.docx` — §0 絶対制約・§1〜§10 全規定・タスクA〜F 定義・完了条件チェックリスト

**前提**: NEJM AI 投稿済み論文 Manuscript ID = AI-26-00824（AI-26-00824、2026-06-17 投稿済み、査読待ち）との同一ポートフォリオ内（方法論ライン）

---

## 文書構成

| 章 | 内容 |
|----|------|
| §1 | 背景・研究設計・ガードレール確認 |
| §2 | プロジェクト初期設定（フォルダ・config.yaml） |
| §3 | タスクA: データ抽出 ETL |
| §4 | タスクB: 年齢標準化 |
| §5 | タスクC: 相関行列・PCA・図表作成 |
| §6 | タスクD: 頑健性・感度分析 |
| §7 | タスクE: 英文原稿ドラフト |
| §8 | タスクF: 想定査読コメント先回り応答メモ |
| §9 | ファイル一覧 |
| §10 | まとめ・完了条件チェック |

---

## §1. 背景・研究設計・ガードレール確認

### 1.1 論文②の位置付け

NDB 研究ポートフォリオは「応用ライン」「ST-GNN ライン」「方法論ライン」の3系統で構成される。論文②は**方法論ライン**の先頭（② Proxy Validity）に相当し、NDB オープンデータの5種類の糖尿病関連指標が「同じ疾患負担」を測定しているのかを三角測量的手法で検証する研究である。

### 1.2 作業指示書（唯一の真実源）の確認

DOCX（`論文2_計画書兼作業指示書.docx`）はバイナリ形式のため、python-docx で本文を抽出して内容を確認した。

確認した主要規定：

| 条項 | 規定内容 |
|------|---------|
| §0-1 | 個票データ不使用（NDB オープンデータ＝公開集計データのみ） |
| §0-2 | 秘匿値（‐）は NaN として記録し補完しない |
| §0-3 | 外的指標を「真値（ground truth）」と呼ばない |
| §0-4 | 処方薬除外理由を実施報告書に明記する |
| §3 | 解析単位: 二次医療圏（主解析）・都道府県（頑健性確認） |
| §4 | 5指標（主解析）＋処方薬1指標（都道府県のみ） |
| §5 | 直接標準化（基準: 2020年国勢調査 40-74歳）・Spearman 相関・PCA |
| §8 | タスクA〜F の実施順序と完了条件 |
| §9 | 完了条件チェックリスト（12項目） |

### 1.3 処方薬データの二次医療圏除外方針の確認

計画書確認段階で、処方薬（薬効分類 396）の二次医療圏別データが NDB No.11 に存在しないことをファイル構造調査で確認した。ユーザー（研究者）より「処方薬を二次医療圏では使わず5指標で主解析を進めること、除外理由を実施報告書に明記すること」の承認を受領している。→ §3.3 参照

---

## §2. プロジェクト初期設定

### 2.1 フォルダ構造作成

`projects/NDB_XXX_care_cascade_dm/` 配下に以下の標準フォルダを作成した。

| フォルダ | 用途 |
|---------|------|
| `00_Docs/` | 実施報告書・作業メモ |
| `02_Data/interim/` | 中間データ（A1〜C0 系） |
| `03_Analysis/scripts/` | 解析スクリプト（01〜05） |
| `03_Analysis/results/figures/` | 図（fig1〜fig_D1） |
| `03_Analysis/results/tables/` | 表（A3〜D4、Table2） |
| `04_Manuscripts/` | Quarto 原稿 + references.bib |
| `config/` | config.yaml |

### 2.2 config.yaml 作成

解析設定を一元管理するために `config/config.yaml` を作成した。主要設定内容：

| 設定項目 | 値 |
|---------|-----|
| NDB ラウンド | No.11（FY2024 レセプト・FY2023 特定健診） |
| 主解析単位 | 二次医療圏（約335圏） |
| 頑健性確認単位 | 都道府県（47） |
| 秘匿閾値 | <10件 → NaN（補完なし） |
| 年齢標準化 | 直接法・2020年国勢調査 40-74歳 |
| 乱数シード | 42 |
| PCA 成分数 | 3 |
| 外れ値除外候補 | 東京都・大阪府・沖縄県 |

---

## §3. タスクA: データ抽出 ETL

### 3.1 スクリプト概要

**スクリプト 1**: `01_task_A_data_extraction.py`  
**スクリプト 2**: `02_task_A_codebook.py`

タスクA の処理フロー：

```
NDB Excel → clean_numeric() → 5指標抽出 → district_code でマージ → CSV 出力
                                              ↓
                                       コードブック・秘匿率計算 → CSV 出力
```

### 3.2 発生したエラーと対処

| # | エラー | 原因 | 対処 |
|---|--------|------|------|
| 1 | `ValueError: Length mismatch: Expected 18 elements, new values have 20` | 都道府県版 HbA1c/FPG 関数が二次医療圏版（20列）の構造を誤用 | `extract_checkup_hba1c_prefecture()` を18列構造に修正 |
| 2 | マージ後 5,532 行（想定 336 行）になる | `district_name` をマージキーにすると「西部」「東部」等が複数県で同名のため Cartesian 積が発生 | マージキーを `district_code`（4桁数字）に変更 |
| 3 | 健診ファイルの地区コードが `101.0`（float）で他ファイルの `'0101'`（str）と一致しない | Excel が地区コード列を float64 で読み込む | `str(int(code)).zfill(4)` で型変換統一 |
| 4 | `KeyError: 'pref_code'` | 都道府県マージ関数が `pref_code` 列を参照していたが HbA1c 修正後に列が消えた | 都道府県マージ関数から `pref_code` 選択を削除 |
| 5 | 都道府県 HbA1c/FPG が 48 行（「判別不可」1行含む） | 「二次医療圏判別不可」が都道府県ファイルにも出現 | `~str.contains("判別不可")` フィルタ追加 |
| 6 | 処方薬抽出が 54 行・数値が不正 | 開始列（col 2 を使用）が誤り（正しくは col 9〜）・薬効コード 396 の ffill が未適用 | `df_raw.iloc[3, 9:]` で都道府県名取得・`data[0].ffill()` で薬効コード前方補完 |

### 3.3 処方薬データを二次医療圏解析から除外した理由（必須記載事項）

**確認経緯**: タスクA のファイル構造調査において、NDB No.11「05_処方薬」フォルダ内の全ファイルを走査した結果、処方薬データ（薬効分類 396・糖尿病剤）は**都道府県別集計のみ**が公開されており、二次医療圏別集計ファイルは存在しないことを確認した（2026-06-22 確認）。

**措置**:

| 解析 | 処方薬の扱い |
|------|------------|
| 主解析（二次医療圏 n=335） | **除外**（データが存在しないため） |
| 頑健性確認（都道府県 n=47） | 6番目の追加指標として使用 |
| 論文 Supplementary Table S1 | 除外理由を英文で明記済み |
| コードブック A3_codebook.csv | `limitations` フィールドに日英両文で記録済み |

**補足**: この除外は解析上の恣意的判断ではなく、NDB オープンデータの公表形式に起因するデータ不在（Data Not Available）である。

### 3.4 タスクA の実行結果

| 出力ファイル | 内容 | 行数 | 状態 |
|------------|------|------|------|
| `A1_district_raw.csv` | 二次医療圏生データ（5指標） | 338→335（判別不可等除去後） | ✅ |
| `A2_prefecture_raw.csv` | 都道府県生データ（6指標） | 47 | ✅ |
| `A3_codebook.csv` | 指標コードブック（処方薬除外理由含む） | 6 | ✅ |
| `A4_masking_summary.csv` | 指標別秘匿率サマリー | 5 | ✅ |
| `A4_masking_by_prefecture.csv` | 都道府県別秘匿率 | 47 | ✅ |
| `Table1_codebook.csv` | 論文 Table.1 草稿（英語） | 6 | ✅ |
| `A5_descriptive_stats_district.csv` | 二次医療圏 記述統計 | 5 | ✅ |
| `A5_descriptive_stats_prefecture.csv` | 都道府県 記述統計 | 5 | ✅ |

**秘匿率**:

| 指標 | 秘匿率 |
|------|--------|
| B001-20（糖尿病合併症管理料） | **13.4%**（45/335圏） |
| B001-27（糖尿病透析予防指導） | **13.1%**（44/335圏） |
| HbA1c 高値率（健診） | 0% |
| FPG 異常率（健診） | 0% |
| HbA1c 検査算定回数 | 0% |

---

## §4. タスクB: 年齢標準化

### 4.1 スクリプト概要

**スクリプト**: `03_task_B_standardization.py`

| 指標種別 | 標準化手法 | 根拠 |
|---------|-----------|------|
| HbA1c 高値率・FPG 異常率（健診） | **直接法**（2020年国勢調査 40-74歳・5歳階級別基準人口） | 年齢別分布が NDB から取得可能 |
| HbA1c 検査・B001-20・B001-27（臨床） | **代理分母換算**（健診受診者数 1,000 人あたり率） | 二次医療圏別年齢内訳が NDB に存在しない |

**基準人口（2020年国勢調査）**:

| 年齢階級 | 全国人口 | 重み |
|---------|---------|------|
| 40-44歳 | 7,671,000 | 0.1308 |
| 45-49歳 | 9,302,000 | 0.1586 |
| 50-54歳 | 8,262,000 | 0.1409 |
| 55-59歳 | 7,566,000 | 0.1290 |
| 60-64歳 | 7,680,000 | 0.1310 |
| 65-69歳 | 9,063,000 | 0.1546 |
| 70-74歳 | 9,095,000 | 0.1551 |
| **合計** | **58,639,000** | 1.0000 |

### 4.2 発生したエラーと対処

| # | エラー | 原因 | 対処 |
|---|--------|------|------|
| 1 | B1 出力が 350 行（ユニーク圏数 335）になる | コード 4705（八重山）が A1 に4行存在（沖縄県2行 × 「判別不可」2行の Cartesian 積） | `drop_duplicates("district_code")` の前に `~contains("判別不可")` フィルタを先に適用 |
| 2 | HbA1c/FPG 標準化結果も 336 行（1行過剰） | 健診 Excel で pref=「二次医療圏判別不可」がコード 4705 として出現しグループ化が2行になる | 標準化関数の結果に対しても `drop_duplicates("district_code")` を追加 |

### 4.3 標準化結果

| 指標 | 粗率（平均） | 標準化率（平均） | 変化方向 | 解釈 |
|------|------------|----------------|---------|------|
| HbA1c 高値率 | 7.66% | 7.55% | 低下 | 高齢者多い地域を若い基準人口で調整 |
| FPG 異常率 | 15.53% | 16.28% | 上昇 | 若年基準人口は FPG 正常域が多いため逆補正 |

### 4.4 タスクB の実行結果

| 出力ファイル | 内容 | 行数 | 状態 |
|------------|------|------|------|
| `B1_district_standardized.csv` | 二次医療圏標準化済みデータ（5指標） | **335** | ✅ |
| `B2_prefecture_standardized.csv` | 都道府県標準化済みデータ（6指標） | 47 | ✅ |
| `B3_standardization_comparison.csv` | 標準化前後比較 | 335 | ✅ |
| `B4_analysis_dataset_district.csv` | 解析用データセット（5指標・欠損なし健診2指標） | 335 | ✅ |

---

## §5. タスクC: 相関行列・PCA・図表作成

### 5.1 スクリプト概要

**スクリプト**: `04_task_C_pca_figures.py`

| 解析 | 手法 | 対象 n |
|------|------|-------|
| Spearman 相関行列 | pairwise complete obs | 251〜335 |
| PCA | z-score 標準化・3成分 | **251**（完全ケース） |
| 外的変数相関 | 代理高齢化率（65-74歳比率）× PC スコア | 335 |

### 5.2 図表一覧と内容

| 出力 | 内容 | 解像度 | 状態 |
|------|------|-------|------|
| `fig1_correlation_heatmap.png` | Spearman 相関ヒートマップ（5×5）+ 有意水準表記 | 300 dpi | ✅ |
| `fig2_pca_biplot.png` | PCA バイプロット（PC1 vs PC2、矢印 = ローディング） | 300 dpi | ✅ |
| `fig3_scatter_matrix.png` | 散布図マトリックス（主要6ペア + 回帰線） | 300 dpi | ✅ |
| `fig4_cross_year.png` | 都道府県 Z スコア比較（6指標・47都道府県・英語表記） | 300 dpi | ✅ |
| `C1_spearman_correlation.csv` | Spearman 相関行列 | — | ✅ |
| `C2_pca_loadings.csv` | PCA ローディング（3成分） | — | ✅ |
| `Table2_pc_external_correlation.csv` | PC × 代理高齢化率 Spearman 相関（軸命名根拠） | — | ✅ |

### 5.3 Spearman 相関行列（主要結果）

| | HbA1c_hr | FPG_hr | HbA1c_test | B001_20 | B001_27 |
|--|---------|--------|-----------|--------|--------|
| **HbA1c_hr** | 1.00 | 0.32*** | 0.04 | **−0.07** | 0.15** |
| **FPG_hr** | | 1.00 | 0.43*** | −0.23*** | −0.04 |
| **HbA1c_test** | | | 1.00 | 0.00 | −0.01 |
| **B001_20** | | | | 1.00 | 0.43*** |
| **B001_27** | | | | | 1.00 |

*Spearman ρ; ***p<0.001, **p<0.01, *p<0.05*

**核心的発見**: HbA1c 高値率（健診スクリーニング）× B001-20（合併症管理）= **ρ = −0.07**（無相関）

### 5.4 PCA 主要結果

| PC | 寄与率 | 最大ローディング変数 | 解釈ラベル | 代理高齢化率との ρ |
|----|--------|------------------|---------|----------------|
| **PC1** | **31.2%** | FPG_hr (0.66)・HbA1c_test (0.53)・HbA1c_hr (0.47) | 「診断・検査強度」 | **+0.426** (p<0.001) |
| **PC2** | **24.0%** | B001_20 (0.74)・B001_27 (0.63) | 「合併症管理強度」 | **−0.300** (p<0.001) |
| PC3 | 20.4% | — | — | −0.319 (p<0.001) |
| **累積 PC1+PC2** | **55.2%** | | | |

### 5.5 実装上の注意事項

- `fig4_cross_year.png`（都道府県比較）: 都道府県名はローマ字（PREF_EN マッピング辞書）を使用。日本語文字は使用しないため日本語フォント設定は不要。
- 図表ラベルは全て英語。日本語文字を含むデータ列は表示前に変換する。

---

## §6. タスクD: 頑健性・感度分析

### 6.1 スクリプト概要

**スクリプト**: `05_task_D_robustness.py`

| 解析 | 内容 |
|------|------|
| D1 | 二次医療圏 vs 都道府県 の相関行列比較（|Δρ|<0.15 を頑健基準） |
| D2 | 外れ値除外感度分析（東京都・大阪府・沖縄県、5シナリオ） |
| D3 | 処方薬指標の追加（都道府県レベル、6番目指標） |
| D4 | MAUP スケール依存性の記述的評価 |

### 6.2 主要結果

**D1: 圏 vs 県 比較**

| 結果 | 値 |
|------|-----|
| 頑健ペア数（|Δρ|<0.15） | **8/10 ペア** |
| 非頑健ペア | HbA1c_hr × B001_20（圏 −0.07 vs 県 −0.42）・FPG_hr × B001_20 |
| 解釈 | スクリーニング × 管理の乖離はスケール依存あり（MAUP Moderate） |

**D2: 外れ値除外感度分析**

| ペア | 有意シナリオ数 / 5 | 解釈 |
|------|-----------------|------|
| HbA1c_hr × FPG_hr | 5/5 | ✅ 頑健 |
| B001_20 × B001_27 | 5/5 | ✅ 頑健 |
| FPG_hr × HbA1c_test | 5/5 | ✅ 頑健 |
| **HbA1c_hr × B001_20** | **0/5** | ✅ **null 結果が頑健**（除外後も無相関） |

**D3: 処方薬指標（都道府県レベル）**

| ペア | Spearman ρ | 有意水準 | 解釈 |
|------|-----------|---------|------|
| Drug × HbA1c_test | **0.870** | *** | 検査指標と同一次元 |
| Drug × FPG_hr | 0.532 | *** | スクリーニング系と中程度相関 |
| Drug × B001_20 | −0.201 | ns | 管理系との相関なし |
| Drug × B001_27 | −0.142 | ns | 管理系との相関なし |

**D4: MAUP リスク**

| リスク | ペア数 |
|--------|-------|
| Low（|Δρ|<0.15 かつ方向一致） | 6 |
| Moderate（方向一致だが|Δρ|≥0.15） | 2 |
| High（方向不一致） | 2 |

### 6.3 出力ファイル

| ファイル | 内容 | 状態 |
|---------|------|------|
| `D1_district_vs_prefecture_correlation.csv` | 圏 vs 県 相関比較（10ペア） | ✅ |
| `D2_outlier_sensitivity.csv` | 外れ値除外感度（5シナリオ × 4ペア） | ✅ |
| `D3_drug_indicator_coverage.csv` | 処方薬 × 他5指標の相関（都道府県） | ✅ |
| `D4_maup_comparison.csv` | MAUP スケール依存性評価 | ✅ |
| `fig_D1_robustness_comparison.png` | 頑健性比較図（2パネル） | ✅ |

---

## §7. タスクE: 英文原稿ドラフト

### 7.1 原稿構成

**ファイル**: `04_Manuscripts/Manuscript_care_cascade_dm.qmd`（Quarto 形式）

| セクション | 文字数（目安） | 状態 |
|-----------|-------------|------|
| Abstract（構造化・5項目） | 約 350 語 | ✅ |
| Introduction | 約 700 語 | ✅ |
| Methods | 約 900 語 | ✅ |
| Results | 約 700 語 | ✅ |
| Discussion | 約 700 語 | ✅ |
| Declarations（Ethics・COI・AI開示） | 完備 | ✅ |
| Table 1 記述統計・Table 2 相関行列 | 本文内 Markdown 表 | ✅ |
| Supplementary Table S1（処方薬除外理由） | 英文 | ✅ |

### 7.2 規定遵守事項の確認

| 規定 | 対応箇所 | 確認 |
|------|---------|------|
| 個票データ不使用の明記 | Methods 冒頭 "All data represent publicly available aggregate statistics; no individual-level data were accessed." | ✅ |
| 外的指標を「真値」と呼ばない | Introduction: "no single ground truth exists" として明示 | ✅ |
| AI 利用開示 | Declarations「AI Use Disclosure」に Claude Sonnet 4.6 を明記 | ✅ |
| 処方薬除外理由 | Supplementary Table S1 に英文で記載 | ✅ |
| MAUP の限界記述 | Discussion「Limitations」第6パラグラフ | ✅ |
| 年齢標準化の制約 | Methods「Age Standardization」で直接法不可の理由を明記 | ✅ |
| 指標選択ガイドライン | Discussion 内に「Indicator Selection Guide」テーブルを掲載 | ✅ |

---

## §8. タスクF: 想定査読コメント先回り応答メモ

**ファイル**: `00_Docs/task_F_reviewer_response_memo.md`

整備した想定コメントと応答（5件）：

| # | 想定コメント | 応答要旨 | 裏付け |
|---|-------------|---------|-------|
| 1 | "n=47 では検定力不足" | 主解析は n=335 圏。47 は頑健性チェック用。 | B4（n=335）・PCA n=251 の計算根拠 |
| 2 | "指標に真値を想定している" | 「no single ground truth」を Introduction に明示。相関行列は対称。 | 論文 Introduction・Table 2（対称行列） |
| 3 | "年齢調整が指標間で一貫しない" | NDB 二次医療圏データに年齢内訳なし → 代理分母採用。Methods に明記。制約は全研究共通。 | Methods「Age Standardization」・NDB データ構造 |
| 4 | "PC 軸ラベルが主観的" | ローディング表（Table C2）が根拠。「may reflect」という限定的表現を使用。 | `C2_pca_loadings.csv`・Fig.2 |
| 5 | "X 指標（眼科・DPC・自己申告）を含めないのか" | 選択基準（NDB No.11 公開・DM 特異性・二次医療圏単位・手法多様性）を Method に明記。DPC 等は別途申請が必要でスコープ外。 | Methods「Indicators」節・config.yaml |

---

## §9. ファイル一覧

### 9.1 スクリプト

| ファイル | 内容 | 状態 |
|---------|------|------|
| `01_task_A_data_extraction.py` | NDB Excel 抽出 ETL（5指標 + 処方薬） | ✅ 完成 |
| `02_task_A_codebook.py` | コードブック・秘匿率計算 | ✅ 完成 |
| `03_task_B_standardization.py` | 年齢標準化（直接法 + 代理分母） | ✅ 完成 |
| `04_task_C_pca_figures.py` | 相関行列・PCA・Fig.1〜4 作成 | ✅ 完成 |
| `05_task_D_robustness.py` | 頑健性・感度分析・Fig.D1 作成 | ✅ 完成 |

### 9.2 中間データ（`02_Data/interim/`）

| ファイル | 内容 | 行数 |
|---------|------|------|
| `A1_district_raw.csv` | 二次医療圏生データ（5指標） | 335 |
| `A2_prefecture_raw.csv` | 都道府県生データ（6指標） | 47 |
| `A3_codebook.csv` | 指標コードブック（処方薬除外理由含む） | 6 |
| `A4_masking_summary.csv` | 指標別秘匿率 | 5 |
| `A4_masking_by_prefecture.csv` | 都道府県別秘匿率 | 47 |
| `B1_district_standardized.csv` | 二次医療圏標準化済みデータ | 335 |
| `B2_prefecture_standardized.csv` | 都道府県標準化済みデータ | 47 |
| `B3_standardization_comparison.csv` | 標準化前後比較 | 335 |
| `B4_analysis_dataset_district.csv` | 解析用最終データセット（5指標） | 335 |
| `C0_pca_dataset.csv` | PCA スコア（PC1〜PC3） | 251 |

### 9.3 図（`03_Analysis/results/figures/`）

| ファイル | 内容 | 状態 |
|---------|------|------|
| `fig1_correlation_heatmap.png` | Fig.1: Spearman 相関ヒートマップ（300 dpi） | ✅ |
| `fig2_pca_biplot.png` | Fig.2: PCA バイプロット（300 dpi） | ✅ |
| `fig3_scatter_matrix.png` | Fig.3: 散布図マトリックス 6ペア（300 dpi） | ✅ |
| `fig4_cross_year.png` | Fig.S1: 都道府県 Z スコア比較（300 dpi） | ✅ |
| `fig_D1_robustness_comparison.png` | Fig.S2: 頑健性比較 2パネル（300 dpi） | ✅ |

### 9.4 表（`03_Analysis/results/tables/`）

| ファイル | 内容 |
|---------|------|
| `Table1_codebook.csv` | 論文 Table 1 草稿（英語） |
| `A5_descriptive_stats_district.csv` | 記述統計（二次医療圏） |
| `A5_descriptive_stats_prefecture.csv` | 記述統計（都道府県） |
| `B3_standardization_comparison.csv` | 標準化前後比較 |
| `C1_spearman_correlation.csv` | Spearman 相関行列 |
| `C2_pca_loadings.csv` | PCA ローディング |
| `Table2_pc_external_correlation.csv` | PC × 外的変数相関（論文 Table 2） |
| `D1_district_vs_prefecture_correlation.csv` | 頑健性 D1 |
| `D2_outlier_sensitivity.csv` | 頑健性 D2 |
| `D3_drug_indicator_coverage.csv` | 頑健性 D3 |
| `D4_maup_comparison.csv` | 頑健性 D4 |
| `Appendix_masking_rate_by_prefecture.csv` | Appendix: 都道府県別秘匿率 |

### 9.5 原稿・ドキュメント

| ファイル | 内容 | 状態 |
|---------|------|------|
| `04_Manuscripts/Manuscript_care_cascade_dm.qmd` | 英文原稿（Quarto）| ✅ |
| `04_Manuscripts/references.bib` | 参考文献（BibTeX・4件プレースホルダ） | ✅ |
| `00_Docs/task_F_reviewer_response_memo.md` | 想定査読コメント応答メモ（5件） | ✅ |
| `00_Docs/実施報告書_care_cascade_dm_20260622.md` | 本ファイル | ✅ |
| `config/config.yaml` | 解析設定一元管理 | ✅ |

---

## §10. まとめ・完了条件チェック

### 10.1 タスク別完了状況

| タスク | 内容 | 状態 |
|--------|------|------|
| A | データ抽出 ETL（5指標 + コードブック + 秘匿率） | ✅ **完了** |
| B | 年齢標準化（直接法 + 代理分母換算） | ✅ **完了** |
| C | 相関行列・PCA・図表作成（Fig.1〜4、Table.2） | ✅ **完了** |
| D | 頑健性・感度分析（D1〜D4、Fig.D1） | ✅ **完了** |
| E | 英文原稿ドラフト（IMRAD・AI開示・Supplementary 含む） | ✅ **完了** |
| F | 想定査読コメント先回り応答メモ（5件） | ✅ **完了** |

### 10.2 完了条件チェックリスト（計画書 §9 対応）

| # | チェック項目 | 確認 |
|---|------------|------|
| 1 | `02_Data/raw/` を変更していない（生データ読み取り専用） | ✅ |
| 2 | 個票データを一切使用していない | ✅ |
| 3 | 秘匿値（‐）を NaN として記録し補完していない | ✅ |
| 4 | 外的指標を「真値（ground truth）」と呼んでいない | ✅ |
| 5 | 処方薬除外理由を実施報告書に明記した（§3.3） | ✅ |
| 6 | 処方薬除外理由を論文 Supplementary Table S1 に英文記載した | ✅ |
| 7 | 年齢標準化の制約（代理分母）を Methods に明記した | ✅ |
| 8 | MAUP の限界を Limitations セクションに記述した | ✅ |
| 9 | 全スクリプトに UTF-8 エンコーディングを明示した | ✅ |
| 10 | 乱数シードを固定した（PCA: `random_state=42`） | ✅ |
| 11 | AI 利用開示を論文 Declarations セクションに記載した | ✅ |
| 12 | スクリプト 01〜05 を番号順に実行すると同じ結果が再現される | ✅ |

### 10.3 主要数値サマリー

| 指標 | 値 |
|------|-----|
| 解析圏数（主解析） | **335 二次医療圏** |
| PCA 完全ケース数 | **251 圏** |
| PC1 寄与率 | **31.2%**（診断・検査強度） |
| PC2 寄与率 | **24.0%**（合併症管理強度） |
| 累積寄与率（PC1+PC2） | **55.2%** |
| 核心的発見: HbA1c 高値率 × B001-20 | **ρ = −0.07**（全5シナリオで一貫して非有意） |
| 頑健ペア率（D1: |Δρ|<0.15） | **8/10 ペア** |

### 10.4 次のステップ（ユーザー作業）

| 優先度 | 作業 |
|--------|------|
| 高 | `quarto render Manuscript_care_cascade_dm.qmd --to docx` で投稿用 DOCX 生成 |
| 高 | 著者名・所属機関・ORCID を原稿に補完 |
| 高 | `references.bib` の参考文献 DOI 検証・追加（4件プレースホルダ → 実文献） |
| 中 | GitHub リポジトリ作成・Zenodo DOI 取得（Data Availability 欄を更新） |
| 中 | 投稿先選定（BMC Medical Research Methodology / Population Health Metrics / JCE） |

---

*本報告書は Claude Sonnet 4.6（Claude Code）が作成した。全解析内容・数値・解釈は研究者の最終確認・承認を要する。*  
*唯一の真実源: `00_Docs/03_Research/論文2_計画書兼作業指示書.docx`*
