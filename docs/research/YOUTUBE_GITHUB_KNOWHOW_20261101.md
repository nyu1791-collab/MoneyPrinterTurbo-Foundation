# GitHubから集めた英語YouTube制作の知識

確認日：2026-11-01。対象は英語の解説・雑学。広告上の高速化率・スター数・収益の主張を実績の根拠にしない。以下はソースと文書から得た知識であり、外部の全ツールをこのPCで実行した記録ではない。

## 1. ShortGPT / RayVentura

[リポジトリ](https://github.com/RayVentura/ShortGPT)、[雑学用の台本](https://github.com/RayVentura/ShortGPT/blob/stable/shortGPT/prompt_templates/facts_generator.yaml)、[投稿用情報のテンプレート](https://github.com/RayVentura/ShortGPT/blob/stable/shortGPT/prompt_templates/yt_title_description.yaml)、[雑学エンジン](https://github.com/RayVentura/ShortGPT/blob/stable/shortGPT/engine/facts_short_engine.py)を確認。MIT。

- 参考になるのは、短い導入で関心を引き、説明へすぐ入る構成と、本文からタイトル・説明を別に作る設計。
- 本体では独自の英語プロンプトに「問い・仕組み・身近な例・持ち帰り」を採用した。長さは目安に変えた。
- テンプレートに含まれる雑学の具体例は、事実として流用していない。生成例の面白さは、事実の裏付けではない。
- ShortGPT全体、古いMoviePy環境、Dockerは導入しない。既存MoneyPrinterの字幕・編集機能を使う。

## 2. short-video-maker / gyoridavid

[README](https://github.com/gyoridavid/short-video-maker)、[場面の組み立て](https://github.com/gyoridavid/short-video-maker/blob/main/src/short-creator/ShortCreator.ts)、[Pexels素材の選定](https://github.com/gyoridavid/short-video-maker/blob/main/src/short-creator/libraries/Pexels.ts)を確認。MIT。

- 一つの場面にナレーションと検索語を持たせ、音声の長さから場面を組む。ジョブを順番に処理して、同時描画を増やさない考え方が参考になる。
- このPCではMoneyPrinterの既存の台本順検索を有効化し、素材処理の並列数を1にした。これは検索語の順序を近づける機能で、台詞ごとの厳密な場面同期を新設したものではない。
- 外部実装には解像度の完全一致や長さの余裕を求める選定、無関係になり得る汎用検索語への切替もある。これらは採用しない。
- READMEはWindows未対応と記す。Kokoro・Whisper・Remotion・Dockerの別構成を追加しない。既存のEdge時刻情報を使い、別の字幕認識モデルを毎回動かさない。

## 3. MoneyPrinterTurbo-Extended / Asad-Ismail

[READMEと制作例](https://github.com/Asad-Ismail/MoneyPrinterTurbo-Extended)、[意味に沿う素材選定](https://github.com/Asad-Ismail/MoneyPrinterTurbo-Extended/blob/main/app/services/semantic_video.py)、LICENSEを確認。MIT。

- 内容に関連する映像を使い、説明と関係の薄い背景動画へ頼りすぎない点を参考にする。
- 本体にも台本順の素材選択や字幕表示があるため、重複する仕組みを作らず設定で活用する。
- SentenceTransformer、画像類似度モデル、Chatterbox、WhisperXの追加は見送る。CPU指定でもモデルの取得・メモリ・認識時間が増えるため、この16GB PCの通常経路には足さない。
- 単語強調の有無や語数を、公開や書き出しの判定条件にはしない。READMEの「完全な同期」等の表現は、このPCの検証結果として扱わない。

## 4. MoneyPrinterV2 / FujiwaraChoki

[README](https://github.com/FujiwaraChoki/MoneyPrinterV2)、[YouTubeの説明](https://github.com/FujiwaraChoki/MoneyPrinterV2/blob/main/docs/YouTube.md)、config.example.json、LICENSEを確認。AGPL-3.0。

- 題材が決まっていれば、題材提案の生成を飛ばす設計を参考にする。MoneyPrinterTurboにも提供台本なら台本生成を省く経路があり、それを維持する。
- 題材、タイトル、説明、素材の指示を同じテーマに寄せる。一方、投稿ボット、営業、別SNS、ブラウザのログイン操作は今回の制作経路へ追加しない。
- 「AI画像ならYouTubeに問題視されにくい」という説明は、採用の根拠にしない。ソースコードをこちらへコピーせず、設計の考え方だけ参考にした。

## 5. MoneyPrinterTurbo / harry0703

[英語README](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md)と、現在のFoundation内のtask.py、llm.py、voice.py、material.py、video.py、CLI・WebUIの入口を照合。手元のベースは9248c27。MIT。

- 本体の強みは、台本・音声・素材・字幕の工程がすでに接続されていること。海外向けという理由で別の大きな基盤へ乗り換えない。
- 提供台本、既存音声、ローカル素材も使える。試聴音声の再利用と素材検索の保存も既にある。
- 自分の英語の切り口、具体例、説明を本文に持たせ、素材はそれを説明するために使う。ツールの名前や宣伝だけで収益を見込まない。

## 英語チャンネルで試す出発点

- 「意外な事実を大量列挙」より、一つの身近な疑問を説明する形から始める。ポップコーンは下記の実作例を用意した。「Why do airplane windows have rounded corners?」は次の題材案で、まだ台本の裏付け資料は取得していない。
- 冒頭で問いや見える現象を置き、説明の中心に日常の比喩を一つ置く。前置きと同じ話の繰り返しを減らす。
- タイトルは短く、実際の内容と一致させる。これも [YouTube公式のタイトル説明](https://support.google.com/youtube/answer/12340300?hl=en)に沿う。数字・大文字・ハッシュタグの数を厳格な合格条件にしない。
- 他サイトの文章の読み上げだけにせず、独自の説明や例を加える。[YouTube公式](https://support.google.com/youtube/answer/1311392?hl=en)も独自性・内容の価値を説明している。制作中に別の監査工程を追加する提案ではない。
- まず45〜75秒程度か3〜5分程度を目安に作り、実際の視聴データが得られたら題材・導入・タイトルを調整する。今回、再生数や収益の実測はしていない。

## 実際に反映したもの

`presets/youtube-en.toml` と `youtube-en.cmd`、初回だけ設定する `tools/use_youtube_en.py` を追加。英語・説明型の台本、台本順の素材、音声時刻の字幕、BGMなし、素材の単独処理を出発点にした。字幕・音声・描画の別基盤は追加していない。

台本・検索語・投稿用情報の自動再生成を1要求に変更。OpenAI互換・Gemini・LiteLLMでは、本経路のSDK再送も無効化。画質480ピクセルの一律排除を外した。目標のための品質監査や再生成は追加していない。

各参照ファイルのURLと取得時のblob SHAは [参照記録](youtube_en_sources_20261101.json)。外部のソースやプロンプトの文章は移植せず、独自の設定と実装にした。

## 実作例

「Why does popcorn pop?」を自作の英文・図で約35秒の縦動画にした。事実の参考は [Virot・Ponomarenkoの論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4345489/)。殻に含まれた水分、加熱による圧力、殻の破断、でんぷんの膨張を日常語で説明し、論文の図や文章は転載していない。

既存のMoneyPrinterの音声再利用・字幕・ローカル素材・映像結合を通した。台本生成・素材サービスへの接続は0回、Edge音声合成は1回。目安の秒数に合わせる自動再生成はしていない。公開後の再生数や収益は未測定。
