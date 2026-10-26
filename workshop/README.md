# ビー玉の小さな工房 / Marble Workshop

70秒のオリジナル工作装置アニメーション。木製レール → ドミノ → シーソー → 滑車とゲート → 木の階段 → 折り紙の通路 → 真鍮チャイム → 木の器。

## ダウンロード

[完成MP4を直接ダウンロード](https://github.com/shirura1-a11y/marble-survival/raw/refs/heads/workshop-film/workshop/workshop_chain_70s.mp4)

GitHubで動画プレビューが表示されない場合も、上のRawリンクからファイルを取得できます。

## 仕様と制作方法

- MP4 / H.264 / yuv420p、縦720×1280（9:16）、70秒、24fps、ステレオAAC。
- Blender CyclesのCPU描画。木目、木の面取り、ガラス内部の色帯、紙の厚み、真鍮、広い窓光、被写界深度を使用。
- 元の描画は540×960・12fps。Open Image Denoiseで除ノイズし、FFmpegで動き補間して24fps、Lanczosで720×1280に出力。ネイティブ720p/24fps描画ではありません。
- 全素材・BGM・効果音はこの制作で生成。外部の映像・写真・音楽・音声サンプルは使用していません。ナレーションなし。無料・オープンソースのツールのみ使用。
- 実物工作の質感を目指したCG作品です。実写ではありません。25枚のドミノはBlenderの剛体・衝突・摩擦シミュレーションで倒し、その結果をスローモーションで再生しています。その他の装置は演出用キーフレーム、距離に基づくビー玉の回転、重力形状の落下軌道、カップ内でのメッシュ接触補正を使用しており、装置全体の剛体・摩擦シミュレーションではありません。実写相当の物理的自然さを保証するものではありません。
- 特定のテレビ番組の映像、ロゴ、音楽は使用していません。

## 再制作

Python 3.12、Blender 4.3.2、Mesa EGL、FFmpeg（libx264/AAC）が必要です。既存レース作品のソースには変更を加えていません。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install numpy==2.3.5 Pillow==12.3.0 oidn==0.2.1 OpenEXR==3.4.4 opencolorio==2.5.2
```

スクリプトの `ROOT` とPython仮想環境の絶対パスを作業場所に合わせて設定します。元のクラウド環境の作業場所は `/workspace/marble-survival/output/workshop` です。

```sh
blender -b --python-exit-code 1 -t 5 --python build_film.py
# 同梱の剛体ベイクを使う場合は以下の再計算2行を省略できます。
blender -b workshop_chain.blend --python-exit-code 1 -t 2 --python simulate_dominos.py
blender -b --python-exit-code 1 -t 5 --python build_film.py
blender -b workshop_chain.blend --python-exit-code 1 -t 5 --python render_frames.py -- 1 1680 2
.venv/bin/python make_audio.py
```

`denoise_worker.py` はBlenderの同梱OpenColorIO設定を参照します。Blenderと除ノイズ処理を別プロセスにして、それぞれのTBBライブラリの競合を避けています。`render_frames.py` は既存の描画フレームを再使用するため、シーンを変更して描き直すときは出力を別の場所へ退避してください。

`encode_film.sh` がラウドネス調整・動き補間・拡大・MP4圧縮を行います。`verify_film.py` は長さ、縦横比、フレーム数、形式、音声、および全編デコードを検証します。

接触検証用の `verify_contacts.py` と `verify_surfaces.py`、実行結果JSONも同梱しています。Blenderから対象シーンを読み込んで実行します。
