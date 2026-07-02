# GitHub・Zenodo 公開手順ガイド / GitHub & Zenodo Setup Guide

**プロジェクト / Project**: NDB_XXX_care_cascade_dm → リネーム予定 `administrative-diabetes-indicators-japan`
**論文 / Manuscript**: Administrative Diabetes Indicators Capture Distinct Stages of the Care Cascade: An Ecological Study of 335 Secondary Medical Areas in Japan
**投稿先 / Target journal**: Annals of Epidemiology (Elsevier)
**最終更新 / Last updated**: 2026-07-02

> **本ガイドは手順書のみです。実際の GitHub リネーム・Public化・Zenodo 新規登録操作はユーザー自身が行ってください**（ユーザー確認済み）。
> **This guide documents the steps only. The actual GitHub rename, publish-to-public, and Zenodo registration must be performed manually by the user** (confirmed with user).

---

## 現在のステータス / Current status

| 作業 / Task | 状態 / Status |
|------|------|
| GitHub リポジトリ名（現在: `NDB_XXX_care_cascade_dm`） | ⚠ **リネーム推奨** → `administrative-diabetes-indicators-japan` |
| GitHub 公開設定（現在: Private） | ⚠ **Public化を検討**（Accept後、または投稿時点でも可） |
| README.md（研究内容） | ⚠ **更新推奨**（旧タイトル "What Do Administrative Healthcare Counts Really Measure?" のまま） |
| CITATION.cff | ⚠ **新規作成推奨**（現状リポジトリに存在しない） |
| REPRODUCE.md | ⚠ **更新推奨**（旧原稿ファイル名を参照している） |
| LICENSE | ✅ 存在（MIT、内容確認のみ） |
| Zenodo DOI | ⚠ **新規登録推奨**（未取得） |
| Data availability 文中のURL | ⚠ **リネーム後のURLに統一** |

---

## 1. GitHub リポジトリのリネーム / Renaming the GitHub repository

### なぜ現在名を避けるか

既存プロジェクト `NDB_XXX_diabetes_ses`（血糖指標の測定論文）が既に `ndb-diabetes-indicators-measurement-japan` という名前を使用しているため、本論文（ケアカスケード解釈）とテーマが重複して見えるのを避けるべく、以下の名前をユーザーが選択しました。

| 項目 | 内容 |
|------|------|
| **新リポジトリ名 / New name** | `administrative-diabetes-indicators-japan` |
| **新URL / New URL** | https://github.com/haruki00430/administrative-diabetes-indicators-japan |
| **旧URL / Old URL** | https://github.com/haruki00430/NDB_XXX_care_cascade_dm（GitHubが自動リダイレクト / GitHub auto-redirects） |

### 手順 / Steps

1. GitHub の該当リポジトリ → **Settings** → **Repository name**
2. `administrative-diabetes-indicators-japan` に変更 → **Rename**
3. **About** 欄（右上の歯車アイコン）を更新:
   - **Description**: Ecological study on administrative diabetes indicators and the care cascade using NDB Open Data, Japan (335 secondary medical areas, FY2023–2024)
   - **Website**: Zenodo DOI URL（取得後）
   - **Topics**: `diabetes`, `care-cascade`, `administrative-data`, `ecological-study`, `ndb`, `japan`, `epidemiology`, `construct-validity`

---

## 2. Private → Public 化 / Making the repository public

1. Settings → Danger Zone → **Change repository visibility** → Public
2. タイミング: 投稿時点で公開する場合はそのまま実施可（他プロジェクトの前例に準拠）。Accept 後まで待つ方針でも可。
3. 公開前に以下を確認:
   - `02_Data/raw/` がリポジトリに含まれていないこと（`.gitignore` 済みか要確認）
   - NDBの実個票データが含まれていないこと（本プロジェクトは集計データのみのため問題なし）

---

## 3. README.md の更新 / Updating README.md

現在の README は 2026-06-24 時点の内容（旧タイトル "What Do Administrative Healthcare Counts Really Measure?"）のままです。本パッケージ作成に伴い、新タイトル・新リポジトリ名に合わせて更新することを推奨します（本セッションでルート `README.md` を更新済み。詳細は本ファイル末尾の「実施済み変更」を参照）。

---

## 4. CITATION.cff の作成 / Creating CITATION.cff

```yaml
cff-version: 1.2.0
message: "If you use this code or data, please cite it as below."
type: software
authors:
  - family-names: Saito
    given-names: Haruki
    orcid: "https://orcid.org/0009-0009-7890-6068"
    affiliation: "Fukushima Medical University School of Medicine"
  - family-names: Ohira
    given-names: Tetsuya
    orcid: "https://orcid.org/0000-0003-4532-7165"
    affiliation: "Fukushima Medical University School of Medicine"
title: "Administrative Diabetes Indicators Capture Distinct Stages of the Care Cascade: An Ecological Study of 335 Secondary Medical Areas in Japan"
version: 1.0.0
date-released: "2026-07-02"
url: "https://github.com/haruki00430/administrative-diabetes-indicators-japan"
doi: "10.5281/zenodo.XXXXXXX"  # Zenodo 取得後に更新 / update after Zenodo DOI is issued
repository-code: "https://github.com/haruki00430/administrative-diabetes-indicators-japan"
license: MIT
keywords:
  - diabetes
  - care-cascade
  - administrative-data
  - ecological-study
  - ndb
  - japan
  - epidemiology
  - construct-validity
```

（本セッションでプロジェクトルートに `CITATION.cff` を新規作成済み。DOI 欄は Zenodo 取得後に更新してください。）

---

## 5. Zenodo 新規登録手順 / Registering on Zenodo

1. **Zenodo にログイン** → https://zenodo.org → GitHub 連携（推奨 / recommended）
2. **Upload → New Upload**
3. **GitHub連携の場合 / If using GitHub integration**: リポジトリ `administrative-diabetes-indicators-japan` を選択 → GitHubで **Release** を作成すると自動的にDOIが付与されます
4. **手動の場合 / Manual upload**: 以下をアップロード
   - 集計データ（`02_Data/interim/` の公開可能なCSV、または `data/release/` 配下）
   - 解析スクリプト一式（`03_Analysis/scripts/` をzip化）
5. **Metadata 入力**:
   - Title: Administrative Diabetes Indicators Capture Distinct Stages of the Care Cascade: An Ecological Study of 335 Secondary Medical Areas in Japan
   - Authors: Haruki Saito (ORCID: 0009-0009-7890-6068), Tetsuya Ohira (ORCID: 0000-0003-4532-7165)
   - Description: Analysis scripts and aggregate secondary-medical-area-level data for an ecological study examining whether diabetes-related administrative indicators from Japan's NDB Open Data reflect a common construct or distinct care-cascade dimensions.
   - Keywords: diabetes, care cascade, administrative data, ecological study, Japan, NDB, epidemiology, construct validity
   - License: MIT（コード / code）、CC BY 4.0（データ / data）
6. **Access**: 投稿中は **Restricted**（Accept後にOpenへ変更） / Set to **Restricted** while under review; change to Open after acceptance
7. **Publish** → DOI 取得

### Zenodo DOI 取得後の作業 / After obtaining the Zenodo DOI

- `CITATION.cff` の `doi` フィールドを更新
- `README.md` のDOIバッジを更新
- `Manuscript_AnnEpi.docx` の Declarations > Availability of data and materials 内のDOIプレースホルダーを確定値に更新
- `CoverLetter_AnnEpi.docx`（該当箇所があれば）を更新
- 投稿システムの Data availability 入力欄にDOIを記入

---

## 6. GitHub 公開用ファイル整備チェックリスト

| ファイル | 説明 | 状態 |
|---------|------|------|
| `README.md` | 英日バイリンガル・研究概要・Citation・License | ✅ 本セッションで更新済み |
| `CITATION.cff` | 機械可読引用情報 | ✅ 本セッションで新規作成済み |
| `LICENSE` | MIT License | ✅ 既存 |
| `REPRODUCE.md` | 再現手順 | ✅ 本セッションで更新済み |
| `03_Analysis/scripts/` | 解析スクリプト | ✅ 既存 |
| `.gitignore` | raw データ除外設定 | ✅ 既存（要最終確認） |

---

## 7. Accept 後の作業 / Post-acceptance tasks

| タスク | タイミング | 備考 |
|--------|-----------|------|
| Zenodo を Restricted → Open に変更 | Accept 後 | ジャーナルDOI発行後が理想 |
| ジャーナルDOIをZenodoに追加 | 論文公開後 | Related Identifiers → is supplemented by |
| CITATION.cff・README.md 更新 | 論文公開後 | ジャーナルDOI追記 |
| Manuscript の Data availability 更新 | Zenodo DOI確定後 | 確定版DOIに更新 |

---

## 補足: 過去の判断からの変更点 / Note on the prior decision

2026-06-23時点の作業（`00_Docs/care_cascade_dm_投稿準備作業サマリー_20260623.md` Phase E）では「未公開リポジトリへの言及を避けるため」Data availability からGitHub記載を手動削除していました。今回のAnnals of Epidemiology投稿準備にあたり、ユーザーの指示（他プロジェクトと同様にGitHub/Zenodo整備）に基づき、Data availability に GitHub・Zenodo への言及を再度追加しています。

---

*作成: 2026-07-02*
