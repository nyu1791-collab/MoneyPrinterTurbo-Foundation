# 引き継ぎメモ

対象: `nyu1791-collab/MoneyPrinterTurbo-Foundation`（上流 harry0703/MoneyPrinterTurbo の独立フォーク）
作業ブランチ: `ccr-3b1e161a-pbc8r8`（開始時点の `main` と同じ `552bdba`）
確認日: 2026-10-20 UTC

## 1. 現状

- 基盤層として追加済み: オフライン・読み取り専用の `mpt doctor`、CI の `contents: read`、GHCR 公開の手動オプトイン（`publish=true` のときだけ push）。
- 既存のレビュー記録:
  - [WHOLE_REPOSITORY_REVIEW.md](WHOLE_REPOSITORY_REVIEW.md): Gemini 3.8 Flash による全 353 テキストファイルの静的レビュー。照合して採用した指摘のみ修正。不採用の 9 件は理由付きで記録。
  - [GEMINI_FOUNDATION_PROPOSALS.md](GEMINI_FOUNDATION_PROPOSALS.md): その前段の提案と修正。
  - [FOUNDATION_DESIGN.md](FOUNDATION_DESIGN.md): 設計と検証の経緯。Opus 提案は HTTP 429（クォータ 0 RPM）で未取得。
- 「アルゴン（Argon）」による査読の記録は、リポジトリ、PR（0 件）、Issue（0 件）のいずれにも見当たらない。

## 2. 引き継ぎ時の検証

| 項目 | 結果 |
| --- | --- |
| `uv sync --frozen --python 3.11`、`uv lock --check --offline` | 成功 |
| `ruff check`（CI と同じ対象） | 成功 |
| `compileall`（CI と同じ対象） | 成功 |
| 全体テスト、PATH の ffmpeg 6.1.1 | 修正前 2451 passed / 9 failed。修正後 **2463 passed / 0 failed / 19 skipped** |
| 全体テスト、同梱 ffmpeg 7.0.2（`IMAGEIO_FFMPEG_EXE` 指定） | **2463 passed / 0 failed / 19 skipped** |
| coverage（CI と同じ分岐計測、閾値 70%） | TOTAL 85%。閾値を満たす |

テストには Redis が必要（`MPT_TEST_REDIS_HOST=127.0.0.1`、`MPT_TEST_REDIS_PORT=6379`、`MPT_TEST_REDIS_DB=15`）。

## 3. 今回修正した不具合: ffmpeg のビルド差で破損音声を受理していた

- **原因**: `utils.get_ffmpeg_binary()` は `IMAGEIO_FFMPEG_EXE` → PATH → 同梱の順に選ぶ。この環境の PATH 上の `/usr/bin/ffmpeg`（6.1.1）は、破損した MP3 に `-xerror` を付けても終了コード 0 を返し、stderr にだけ `Header missing` 等を出す。
- **影響**:
  - `bgm._validate_audio`: BGM アップロードと TTS 応答の完全デコード検証が、破損 MP3 を受理していた。
  - `material_upload._validate_video`: 破損 MP4 を受理していた。
  - `voice.prepare_voxcpm_reference_audio`: 破損 MP3 から出力を作って成功扱いにしていた。
- **修正**:
  - 3 箇所とも「終了コードが 0 以外」または「stderr にエラー出力がある」を失敗とした。
  - BGM の「非空」判定は、進捗の `out_time_us` から framemd5 のフレーム数に変えた。6.1.1 では約 0.1 秒の無音 WAV の進捗が 0 のままになり、正しい音声を誤って拒否していたため。
- **検証**:
  - 修正前に失敗していたのは 9 件（BGM 1、TTS 完全デコード 5、WebUI 音声アップロード 1、WebUI BGM 2）。修正後は両ビルドで通過。
  - 新しい回帰テストは、修正前のコードで失敗することを `git stash` で確認した。
  - 正常音声への影響: 同梱楽曲 29 本と生成サンプル（WAV、FLAC、OGG、M4A、MP4、MP3）では stderr が空で、誤拒否はなかった。

## 4. 未解決・要判断

1. **このブランチで CI が動いていない**。`ci.yml` のトリガーは `pull_request` と `main` への push だけで、PR は 0 件、ワークフローの実行履歴も 0 件。`FOUNDATION_DESIGN.md` は「Actions はリポジトリ単位で無効」と記すが、API ではワークフローは `active` と返る。GitHub の設定画面で実態を確認する。
2. **Opus 提案は未取得**（Vertex のクォータ 0 RPM、[vertex-proposal-receipt.json](vertex-proposal-receipt.json)）。
3. **ffmpeg の解決順と版がばらつく**:
   - 検証側（`get_ffmpeg_binary`）は PATH を同梱より優先する。
   - MoviePy は既定で同梱（7.0.2）を使う。`app.ffmpeg_path` を設定すると `IMAGEIO_FFMPEG_EXE` が上書きされ、両者が同じになる。
   - Docker イメージは `python:3.11-slim-bullseye` に apt の `ffmpeg` を入れる。版は未確認。今回の修正は本番にも効く想定だが、Docker イメージ上では未検証。
   - 推奨: `mpt doctor` に ffmpeg の版と解決元を表示し、既知の問題がある版は警告する。もしくは Docker で版を固定する。
4. **OAuth の異常応答メッセージ**は HTTP 状態のみになり、RFC 6749 の標準エラーコード（`invalid_grant` など）も出なくなった。秘密値の漏えい防止を優先した結果。標準コードだけを許可リストで表示する改善余地がある。
5. **`config.toml` の自動生成**: `app.config` は読み込み時に `config.example.toml` から `config.toml` を作る（上流の挙動）。テスト実行でもリポジトリ直下に作られる（`.gitignore` 済み）。`mpt doctor` 自体は作らない。
6. **API キー未設定時の免認証モード**はコピー元の互換仕様として残る。初期運用はローカルか信頼できるネットワークに限定する。

## 5. 推奨する次の作業

1. GitHub の Actions 設定を確認し、このブランチで CI を実行する。PR の作成はオーナーの承認後。
2. Docker イメージの ffmpeg の版を確認し、必要なら版を固定する。
3. `mpt doctor` に ffmpeg の版と解決元の表示を追加する。
4. Opus のクォータ解消後に提案を取得し、採否を記録する。

## 6. 再現コマンド

```sh
uv sync --frozen --python 3.11
uv run --no-sync ruff check app cli.py main.py webui test docs/skill
MPT_TEST_REDIS_HOST=127.0.0.1 MPT_TEST_REDIS_PORT=6379 MPT_TEST_REDIS_DB=15 \
  uv run --no-sync python -X utf8 -m pytest -q test
# 同梱 ffmpeg で再確認する場合は IMAGEIO_FFMPEG_EXE に同梱バイナリのパスを指定する
```
