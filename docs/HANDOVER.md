# 引き継ぎメモ

対象: `nyu1791-collab/MoneyPrinterTurbo-Foundation`（上流 harry0703/MoneyPrinterTurbo の独立フォーク）
作業ブランチ: `ccr-3b1e161a-pbc8r8`（開始時点の `main` と同じ `552bdba`）
確認日: 2026-10-20 UTC

## 1. 現状

- 基盤層として追加済み: オフライン・読み取り専用の `mpt doctor`、CI の `contents: read`、GHCR 公開の手動オプトイン（`publish=true` のときだけ push）。
- 既存のレビュー記録:
  - [WHOLE_REPOSITORY_REVIEW.md](WHOLE_REPOSITORY_REVIEW.md): Gemini 3.8 Flash による全 353 テキストファイルの静的レビュー。照合して採用した指摘のみ修正。不採用の 10 件は理由付きで記録。
  - [GEMINI_FOUNDATION_PROPOSALS.md](GEMINI_FOUNDATION_PROPOSALS.md): その前段の提案と修正。
  - [FOUNDATION_DESIGN.md](FOUNDATION_DESIGN.md): 設計と検証の経緯。Opus 提案は HTTP 429（クォータ 0 RPM）で未取得。
- 「アルゴン（Argon）」による査読の記録は、リポジトリ、PR（0 件）、オープンな Issue（0 件）のいずれにも見当たらない。

## 2. 検証結果

| 項目 | 結果 |
| --- | --- |
| `uv sync --frozen --python 3.11`、`uv lock --check --offline` | 成功 |
| `ruff check`、`compileall`（CI と同じ対象） | 成功 |
| 全体テスト、PATH の ffmpeg 6.1.1（最終状態） | **2469 passed / 0 failed / 19 skipped**（修正前は 2451 passed / 9 failed） |
| 全体テスト、ffmpeg 5.1.9（bookworm、Docker の推奨先） | **2469 passed / 0 failed / 19 skipped** |
| 全体テスト、同梱 ffmpeg 7.0.2（OAuth 変更前） | 2463 passed / 0 failed / 19 skipped |
| 全体テスト、ffmpeg 4.3.7（bullseye、現在の Docker と同系統） | 2448 passed / 15 failed / 19 skipped（OAuth 変更前）。失敗は動画レンダラ 14 件（`amix normalize`）と色テスト 1 件。詳細は §4-3 |
| coverage（CI と同じ分岐計測、閾値 70%） | TOTAL 85%（OAuth 変更前） |

テストには Redis が必要。検証は Redis 7.0.15 で、CI と同じ環境変数（`MPT_TEST_REDIS_HOST=127.0.0.1`、`MPT_TEST_REDIS_PORT=6379`、`MPT_TEST_REDIS_DB=15`）を指定して実施。

## 3. 今回修正した内容

### 3-1. ffmpeg 6.1 系で破損音声を受理していた不具合

- **原因**: `utils.get_ffmpeg_binary()` は `IMAGEIO_FFMPEG_EXE` → PATH → 同梱の順に選ぶ。この環境の PATH 上の `/usr/bin/ffmpeg`（6.1.1）は、破損した MP3 に `-xerror` を付けても終了コード 0 を返し、stderr にだけ `Header missing` 等を出す。
- **影響**（6.1 系のみ。bullseye の 4.3.7 では、旧コードでも破損 MP3・MP4 は拒否されていた）:
  - `bgm._validate_audio`: BGM アップロードと TTS 応答の完全デコード検証が、破損 MP3 を受理していた。
  - `material_upload._validate_video`: 破損 MP4 を受理していた。
  - `voice.prepare_voxcpm_reference_audio`: 破損 MP3 から出力を作って成功扱いにしていた。
- **修正**:
  - 3 箇所とも「終了コードが 0 以外」または「stderr にエラー出力がある」を失敗とした。
  - BGM の「非空」判定は、進捗の `out_time_us` から framemd5 のフレーム数に変えた。6.1.1 では約 0.1 秒の無音 WAV の進捗が 0 のままになり、正しい音声を誤って拒否していたため。
- **検証**:
  - 修正前に失敗していたのは 9 件（BGM 1、TTS 完全デコード 5、WebUI 音声アップロード 1、WebUI BGM 2）。修正後は 6.1.1 と 7.0.2 で通過。
  - 回帰テストは修正前のコードで失敗することを確認した（`git stash` と一時的な差し替え）。
  - 正常音声への影響: 同梱楽曲 29 本と生成サンプル（WAV、FLAC、OGG、M4A、MP4、MP3）では stderr が空で、誤拒否はなかった。
  - 判定の比較（6.1.1 / 4.3.7 / 7.0.2）: 6.1.1 では旧コードが破損 MP3 を受理し、無音 WAV を誤拒否。新コードは 3 つとも正しく判定。

### 3-2. OAuth の異常応答メッセージ

- 前回の修正で HTTP 状態のみになっていたため、RFC 6749 / 8628 の**標準エラー識別子だけ**を `error=<code>` で表示するように戻した（例: `error=invalid_grant`）。
- 許可リストに無い値、`error_description`、本文は一切出さない。
- 新規テスト 6 件。修正前のコードでは標準識別子の 3 件（device / poll / refresh）が失敗することを確認。

## 4. 未解決・要判断

1. **このブランチで CI が動いていない**。`ci.yml` のトリガーは `pull_request` と `main` への push だけで、PR は 0 件、CI（`ci.yml`）の実行履歴も 0 件。`FOUNDATION_DESIGN.md` は「Actions はリポジトリ単位で無効」と記すが、API ではワークフローは `active` と返る。GitHub の設定画面で実態を確認する。
2. **Opus 提案は未取得**（Vertex のクォータ 0 RPM、[vertex-proposal-receipt.json](vertex-proposal-receipt.json)）。
3. **Docker の ffmpeg は動画レンダラの要件を満たさない**:
   - `python:3.11-slim-bullseye` の apt は ffmpeg 4.3.9 を入れる（bullseye-security の索引で確認）。4.3.9 の `.deb` はこの環境から取得できなかったため、同系統の 4.3.7 で検証した。
   - 4.3 系では `app/services/video_project.py` のレンダラが `amix normalize` で失敗する。このレンダラは製品の生成経路（`task.py`、API、WebUI）からは参照されず、CLI の `python -m app.services.video_project` とテストだけが使う。
   - 色テスト（BT.709）も 4.3.7 では許容誤差を外れる。6.1.1、7.0.2、5.1.9 では通る。
   - **推奨**: Docker の base を `python:3.11-slim-bookworm` に変え、apt のソース行も bookworm に直す。bookworm の ffmpeg 5.1.9 では全体テストが通ることを確認済み。Docker デーモンがこの環境に無いため、Dockerfile の build は未検証。
   - ffmpeg の解決順: 検証側（`get_ffmpeg_binary`）は PATH を同梱より優先する。MoviePy は既定で同梱（7.0.2）を使う。`app.ffmpeg_path` を設定すると両者が揃う。
   - `docs/video-projects.md` の要件に FFmpeg 4.4 以上を追記済み。
4. **`config.toml` の自動生成**: `app.config` は読み込み時に `config.example.toml` から `config.toml` を作る（上流の挙動）。テスト実行でもリポジトリ直下に作られる（`.gitignore` 済み）。`mpt doctor` 自体は作らない。
5. **API キー未設定時の免認証モード**はコピー元の互換仕様として残る。初期運用はローカルか信頼できるネットワークに限定する。
6. **`mpt doctor` に ffmpeg の版を表示する案は取り下げた**。doctor は FFmpeg を実行しない契約（`FOUNDATION_DESIGN.md`）のため。版の確保は Docker 側で行う。

## 5. 推奨する次の作業

1. GitHub の Actions 設定を確認する。このブランチで CI を走らせるには PR か `main` への反映が要る。PR の作成はオーナーの承認後。
2. Dockerfile を bookworm（ffmpeg 5.1 系）へ移す。Docker デーモンのある環境で build し、可能なら全体テストを回す。
3. Opus のクォータ解消後に提案を取得し、採否を記録する。
4. 「Argon」の査読記録の所在を確認し、本メモと照合する。

## 6. 再現コマンド

```sh
uv sync --frozen --python 3.11
uv run --no-sync ruff check app cli.py main.py webui test docs/skill
MPT_TEST_REDIS_HOST=127.0.0.1 MPT_TEST_REDIS_PORT=6379 MPT_TEST_REDIS_DB=15 \
  uv run --no-sync python -X utf8 -m pytest -q test
# 別の ffmpeg で再確認する場合は、その実行ファイルを PATH の先頭に置くか、
# IMAGEIO_FFMPEG_EXE にパスを指定する
```
