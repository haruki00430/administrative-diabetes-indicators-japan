# Annals of Epidemiology 投稿チェックリスト・アップロード手順

**論文**: Administrative Diabetes Indicators Capture Distinct Stages of the Care Cascade: An Ecological Study of 335 Secondary Medical Areas in Japan
**投稿先**: Annals of Epidemiology (Elsevier, sponsored by American College of Epidemiology)
**査読形式**: Single anonymized（著者名は査読者に開示される。匿名化原稿は不要）
**参照した投稿規定**: `Guide for authors - Annals of Epidemiology - ISSN 1047-2797 _ ScienceDirect.com by Elsevier.pdf`（20ページ、全文確認済み・2026-07-02）
**作成日**: 2026-07-02

---

## 1. 論文種別・分量チェック

| 項目 | 規定 | 本原稿 | 判定 |
|------|------|--------|------|
| 論文種別 | Original article | Original article | ✅ |
| 本文語数（Intro〜Conclusions） | ≤3,000 words | 2,212 words | ✅ |
| Abstract 語数 | ≤200 words（構造化: Purpose/Methods/Results/Conclusions） | 184 words、4見出し完備 | ✅ |
| Tables + Figures（本文） | ≤6 | Table×2 + Figure×3 = 5 | ✅ |
| Keywords | 3–10語、英語 | 6語 | ✅ |

**特記事項（Secondary Data 論文の必須要件）**: 本論文はNDB Open Data（二次利用・公開集計データ）の分析であるため、投稿規定「Analyses of Publicly Available and Secondary Data」に基づき、Cover Letterに (i) データセットの妥当性 (ii) データの複雑性の理解と対応、を明記する必要があります。→ `CoverLetter_AnnEpi.docx` に記載済み。

---

## 2. 本文ファイルへの修正内容（実施済み）

`11_v11_Administrative_Diabetes_Indicators_Care_Cascade_Annals.docx` を元に `Manuscript_AnnEpi.docx` を作成し、以下を修正しました。

| 修正箇所 | 内容 | 理由 |
|---------|------|------|
| Availability of data and materials | GitHub（`administrative-diabetes-indicators-japan`）とZenodo DOI（登録後に確定）への言及を追記 | 投稿規定 Research data / Data statement（Option B: リポジトリへの寄託・引用を推奨） |
| List of abbreviations（新規セクション） | NDB, FY, HbA1c, FPG, PCA, PC, MAUP, B001-20, B001-27 を定義 | Annals of Epidemiology 固有の "Journal specific information: Article structure" で必須とされる略語一覧 |
| Declaration of generative AI... | 見出しを投稿規定の推奨タイトルに変更し、本文を「[TOOL] を [目的] のために使用した」という具体的文言に確定（Claude Sonnet 4.6 / Claude Code, Anthropic および OpenAI Codex を明記） | 投稿規定は具体的ツール名の開示を要求（旧文言はプレースホルダーのまま「ジャーナル方針に応じて調整すべき」と記載されており未確定だった） |

**変更していない箇所**: Abstract、Introduction、Methods、Results、Discussion、Conclusions の本文、Table 1・2、Figure 1–3、参考文献リストは内容を変更していません（語数・構成要件を満たしているため）。

---

## 3. 新規作成ファイル

| ファイル | 内容 | 投稿規定上の根拠 |
|---------|------|------------------|
| `TitlePage_AnnEpi.docx` / `.md` | タイトル・著者・所属・連絡先・語数集計 | Title page セクション |
| `CoverLetter_AnnEpi.docx` / `.md` | Cover Letter（Funding/Declarations/査読者推薦は含めない。Secondary Data 必須開示を含む） | Cover Letter セクション（"should not include funding information, author declarations, or suggested or opposed reviewers"） |
| `Highlights_AnnEpi.docx` / `.md` | 5項目、各85字以内の箇条書き | Highlights セクション（3–5項目、各85字以内、ファイル名に"highlights"を含む） |
| `COI_Statement_AnnEpi.docx` / `.md` | 利益相反なし（"I have nothing to declare"） | Declaration of competing interests（宣言ツールの結果をWordファイルで別途アップロード） |
| `Figure_1_AnnEpi.png`〜`Figure_3_AnnEpi.png` | 本文図の個別ファイル | Figures セクション（論理的命名規則） |
| `SuppFig_S1_AnnEpi.png`〜`SuppFig_S3_AnnEpi.png` | 補足図の個別ファイル（`Supplement_AnnEpi.docx`にも同内容を掲載済み） | Supplementary material セクション |
| `GitHub_Zenodo_setup_guide.md` | GitHub/Zenodo 公開手順（日英・リポジトリリネーム含む） | Research data / Data linking セクション |

---

## 4. 図表の解像度に関する確認事項（要ユーザー判断）

投稿規定の解像度要件（カラー/グレースケール写真: 300dpi以上、線画: 1000dpi以上、線画とカラーの組み合わせ: 500dpi以上、フルページ幅換算 2244–7480px）に対し、現状の図は以下の通りです。

| ファイル | 実寸 | 埋め込みdpiタグ | 判定 |
|---------|------|-----------------|------|
| Figure_1_AnnEpi.png（概念図） | 3240×1140px | なし | 概ね良好 |
| Figure_2_AnnEpi.png（相関ヒートマップ） | 2160×1740px | なし | 概ね良好 |
| Figure_3_AnnEpi.png（PCAローディング図） | 1380×1178px | 200dpi | ⚠ **やや低解像度**（組み合わせ図の目安1772px以上を下回る） |
| SuppFig_S1_AnnEpi.png | 1485×583px | 150dpi | ⚠ **低解像度** |
| SuppFig_S2_AnnEpi.png | 1950×1260px | なし | 概ね良好 |
| SuppFig_S3_AnnEpi.png | 1334×729px | 150dpi | ⚠ **低解像度** |

**推奨対応**: `03_Analysis/scripts/04_task_C_pca_figures.py`（Figure 3）および `06_task_E_denominator_sensitivity.py`（Supplementary Figures）を、`savefig(..., dpi=600)` 等より高い解像度設定で再実行し、`03_Analysis/results/figures/` の該当PNGを再生成した上で本パッケージに再取り込みすることを推奨します。生データには触れず、既存の中間データ（`02_Data/interim/`）から再生成可能です。**この再生成は本作業では実施していません**（分析結果自体を変更する可能性のある操作のため、実行前にご確認いただくのが安全と判断しました）。

---

## 5. アップロード想定順序（Elsevier投稿システム）

| # | ファイル | システム上の分類 |
|---|---------|-----------------|
| 1 | `Manuscript_AnnEpi.docx` | Manuscript（本文・タイトル・著者情報を含む単一ファイル。Single anonymized review のため匿名化版は不要） |
| 2 | `TitlePage_AnnEpi.docx` | Title Page（任意・メタデータ確認用） |
| 3 | `CoverLetter_AnnEpi.docx` | Cover Letter |
| 4 | `Highlights_AnnEpi.docx` | Highlights |
| 5 | `COI_Statement_AnnEpi.docx` | Declaration of Interest |
| 6 | `Figure_1_AnnEpi.png` | Figure 1 |
| 7 | `Figure_2_AnnEpi.png` | Figure 2 |
| 8 | `Figure_3_AnnEpi.png` | Figure 3 |
| 9 | `Supplement_AnnEpi.docx` | Supplementary Material（Supplementary Figures S1–S3・Tables S1–S2を1ファイルに集約） |

> 投稿システムが補足図を個別ファイルとして要求する場合は `SuppFig_S1_AnnEpi.png`〜`SuppFig_S3_AnnEpi.png` を代わりに使用してください。

---

## 6. 投稿前 最終確認チェックリスト（投稿規定 Submission Checklist 準拠）

- [ ] Corresponding author の連絡先（メール・住所）が最新か
- [ ] 全ファイル（本文・図・補足資料）をアップロードしたか（表・脚注・キャプションを含めたか）
- [ ] スペルチェック・文法チェックを実施したか
- [ ] 本文で引用した全参考文献が参考文献リストに含まれるか、その逆も含めて確認したか
- [ ] 第三者著作物の転載許可（該当する場合）
- [ ] Figure 3・SuppFig S1・S3 の解像度再検討（上記4章）
- [ ] GitHub 公開設定・Zenodo DOI 取得（`GitHub_Zenodo_setup_guide.md` 参照）
- [ ] Data availability文中のZenodo DOIを確定後の値に更新

---

*作成: 2026-07-02*
