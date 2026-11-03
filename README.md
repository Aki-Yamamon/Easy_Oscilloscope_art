# 簡単!オシロスコープアート

動画やゲームを、**オシロスコープの XY モード**に線画として映し出すプロジェクトです。
PC で映像を作り、USB シリアルで ESP32 に送り、ESP32 の DAC 出力 2 本(X / Y)をオシロスコープにつなぎます。

> 舞鶴高専 2026 高専祭の展示用に制作しました。 現在のバージョン: **v3.2.1**

[demo](docs/images/testview.gif)

## 起動をするまえに
著作権に抵触する恐れがあるため、システムを起動時呼び出すhome.osaやテスト用のwavファイルを本リポジトリには含めておりません。

起動および最低限の動作確認のために
- home.osa
- badapple.osa
- badapple.wav
という名前のファイルを`tools/source`に追加してください
ファイル生成については[こちら](#自分の動画を変換して流す)をご参照下さい。
また以下の写真が私の環境でのSEや起動時に流すosaファイルの構成等になります。
参考にしてください。
[fils](docs/images/screen.png)

## 目次

- [できること](#できること)
- [仕組み](#仕組み)
- [環境情報](#環境情報)
- [環境構築と起動](#環境構築と起動)
- [使い方](#使い方)
  - [メニュー構成](#メニュー構成)
  - [ゲームの操作方法](#ゲームの操作方法)
  - [ビデオ再生](#ビデオ再生)
  - [自分の動画を変換して流す](#自分の動画を変換して流す)
- [コマンドリファレンス](#コマンドリファレンス)
- [問題と解決方法](#問題と解決方法)
- [ディレクトリ構成](#ディレクトリ構成)
- [改造するには](#改造するには)
- [更新履歴](#更新履歴)
- [ライセンス](#ライセンス)

## できること

| 機能 | 内容 |
|---|---|
| ビデオ再生 | Bad Apple!! などの動画を、音声つきでオシロに映す。YouTube の動画 ID を入れて再生することもできる |
| ゲーム | TETRIS と PAC MAN をキーボードで遊べる。LEADERBOARD つき |
| 動画変換 | 好きな動画を輪郭線のデータ(`.osa`)に変換できる |

## 仕組み

```
PC (Python)                          ESP32                       オシロスコープ (XYモード)
 メニュー / ゲーム / 動画 ─ 線 → N点 ─ USBシリアル ─→ DAC25 (X) ──→ CH1
 (osagame, osaconv)        (uint8)    921600bps      DAC26 (Y) ──→ CH2
```

- 映像は「輪郭の線」を 1 フレーム N 点(既定 1000 点)の座標列にして送ります。
- ESP32 は受け取った最新フレームを、DAC で描き続けます。
- ESP32 は通信が 1 秒以上途切れると、待機用の「動く円」に戻ります。

## 環境情報

作者の環境です。

| 項目 | 内容 |
|---|---|
| OS | Windows 11 |
| マイコン | ESP32(無印、ESP32 Dev Module) |
| Python | 3.11 |
| 書き込み | Arduino IDE |
| 動画の変換と再生 | ffmpeg(PATH に通す)、`yt-dlp`(YouTube 再生を使う場合) |
| オシロスコープ | **XY モードが使えるもの**(例: IWATSU SS-7802 20MHz) |

## 環境構築と起動

### 1. ダウンロード

最新バージョンは **v3.2.1** です。`git clone` するか、Releases からダウンロードしてください。

```powershell
git clone https://github.com/aki-yamamon/oscilloscope_art-.git
cd oscilloscope_art-
```

### 2. Python 環境を作る

```powershell
cd tools
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

> `Scripts` です(`Script` ではありません)。PowerShell で実行できないと言われたときは、
> `Set-ExecutionPolicy -Scope Process RemoteSigned` を実行してからもう一度試してください。

`ModuleNotFoundError` が出たときは、足りないものを個別に入れます。

```powershell
pip install sounddevice yt-dlp pyserial
```

### 3. ESP32 に書き込む

1. Arduino IDE で `firmware/osa_stream/osa_stream.ino` を開く
2. ボード: `ESP32 Dev Module`
3. **Partition Scheme: `Huge APP (3MB No OTA/1MB SPIFFS)`** を選ぶ
4. **シリアルモニタは閉じる**(開いていると PC から送れません)
5. 書き込む。成功すると、オシロに**動く円**が出ます

### 4. 配線

| ESP32 | オシロスコープ |
|---|---|
| GPIO25 | CH1(X) |
| GPIO26 | CH2(Y) |
| GND | CH1 / CH2 のグラウンド |

オシロは **XY モード**にし、両チャンネルとも **DC カップリング**にします。

### 5. 起動

```powershell
cd tools
python -m osagame --port COM6 --no-preview
```

`COM6` は自分の ESP32 のポート番号に変えてください(デバイスマネージャーの「ポート (COM と LPT)」で確認できます)。

ESP32 がなくても、画面だけで動作を確認できます。

```powershell
python -m osagame --no-serial --no-preview
```

> プレビューを出したままだと重くなるので、本番では `--no-preview` をおすすめします。
> キー入力は pygame のウィンドウで受け取るため、**カーソル(フォーカス)を常にそのウィンドウの上に置いて**ください。

### 6. 必要なファイルを置く

動画ファイルは著作権の都合で、このリポジトリには入れていません。
Bad Apple!! を再生したいときは、`tools/source/` に次の 3 つを置いてください。

- `home.osa`(同梱)
- `badapple.osa`
- `badapple.wav`

作り方は[自分の動画を変換して流す](#自分の動画を変換して流す)を見てください。

## 使い方

### メニュー構成

起動すると `home.osa` が流れます。**Enter** でメニューに入ります。
カーソル `>` は **上下キー**で動かし、**Enter** で決定します。

```
HOME 画面 ─ Enter ─→ MENU
                      ├─ VIDEO
                      │    ├─ BAD APPLE!!
                      │    ├─ ENTER THE RINK   YouTube の動画 ID を入力して再生
                      │    ├─ HISTORY          再生した動画の一覧
                      │    └─ BACK
                      ├─ GAME
                      │    ├─ TETRIS
                      │    ├─ PAC MAN
                      │    ├─ LEADERBOARD
                      │    └─ BACK
                      ├─ EXPLINE   (COMING SOON)
                      └─ HOME
```

QUIT を選ぶか、ウィンドウを閉じると終了します。

### ゲームの操作方法

#### TETRIS

| キー | 動作 |
|---|---|
| ← → | 横移動 |
| Z / X | 左回転 / 右回転 |
| ↓ | ゆっくり落とす |
| ↑ | 急速落下(ハードドロップ) |

#### PAC MAN

| キー | 動作 |
|---|---|
| ↑ ↓ ← → | 進む向きを変える |

- 色を付けられないため、ゴーストはすべて同じプログラムで動いています。
- 軽さのために、コーナーでの挙動の差やフルーツのボーナスなどは省いています。

ゲームオーバーになると名前を入力でき、LEADERBOARD に記録されます。

### ビデオ再生

- **BAD APPLE!!**: `source/badapple.osa` と `badapple.wav` を同時に再生します。
- **ENTER THE RINK**: YouTube の URL の `watch?v=` の後ろ(動画 ID 11 文字)を入力します。URL ごとの入力でも大丈夫です。
  1. `CHECKING...` で動画を探す
  2. 成功すると `SUCCESS / PLZ WAITING...` が出て、裏でダウンロードと変換をする
  3. 終わると自動で再生
- 15 分より長い動画は受け付けません。
- 再生した動画は `tools/source/addvideo/history.json` に残り、**HISTORY** から選んで何度でも再生できます。
- 再生中に **ESC** で止められます。

必要なもの: `yt-dlp`(`pip install yt-dlp`)、ffmpeg(PATH に通す)

### 自分の動画を変換して流す

`tools/` で venv を有効にして実行します。`<>` は自分の値に置き換えてください。

```powershell
cd tools

# 1. 動画 → .osa(輪郭データ)
python -m osaconv <ファイル名>.mp4 -o <生成ファイル名>.osa --start <開始秒> --seconds <長さ秒> --invert --epsilon 1.5 --min-length 40 --points 1000

# 2. 映像だけ流す
python -m osaconv.stream <生成ファイル名>.osa --port <ポート番号> --baud 921600 --loop

# 3. 音声(.wav)を取り出す
ffmpeg -ss <開始秒> -t <長さ秒> -i <ファイル名>.mp4 -vn -ac 2 -ar 44100 -c:a pcm_s16le <生成ファイル名>.wav

# 4. 映像と音声を同時に再生
python -m osaconv.play <生成ファイル名>.osa --audio <生成ファイル名>.wav --port <ポート番号> --baud 921600
```

変換結果は、PC 上で確認できます。

```powershell
python scripts/view_osa.py <生成ファイル名>.osa --count 12
```

輪郭がうまく取れないときは、スライダーで調整できます。

```powershell
python scripts/tune_contour.py <ファイル名>.mp4 --frame 1000
```

## コマンドリファレンス

すべて `tools/` で、venv を有効にして実行します。`--help` でも確認できます。

### `python -m osagame`  メニュー、ゲーム、動画の本体

| 引数 | 既定値 | 意味 |
|---|---|---|
| `--port` | なし | ESP32 のポート。例: `COM6`。`--no-serial` のときは不要 |
| `--baud` | `921600` | ボーレート。ESP32 側の `BAUD` と合わせる |
| `--points` | `1000` | 1 フレームの点数 N(`.osa` と合わせる) |
| `--fps` | `30` | フレームレート |
| `--scale` | `1.0` | 表示倍率(X と Y の両方)。例: `0.485` |
| `--scale-x` | `--scale` と同じ | X だけの倍率 |
| `--scale-y` | `--scale` と同じ | Y だけの倍率 |
| `--home` | `source/home.osa` | ホーム画面の `.osa`。差し替えられる |
| `--no-serial` | オフ | ESP32 に送らず、PC の画面だけで動かす(動作確認用) |
| `--no-preview` | オフ | PC 画面へのプレビュー描画をやめる(負荷軽減。本番向け) |
| `--preview-every` | `1` | プレビューを N フレームに 1 回だけ描く |
| `--profile` | オフ | 5 秒ごとに処理時間・メモリ・スレッド数を表示する(重いときの調査用) |
| `--reset-wait` | `2.0` | ポートを開いたあとに待つ秒数(ESP32 のリセット対策) |

例:

```powershell
# 実機で本番
python -m osagame --port COM6 --baud 921600 --no-preview

# ESP32 なしで確認
python -m osagame --no-serial --no-preview

# 表示の大きさがオシロに合わないとき
python -m osagame --port COM6 --scale-x 0.5 --scale-y 0.485 --no-preview

# 重い原因を調べる
python -m osagame --no-serial --profile
```

### `python -m osaconv`  動画 → `.osa` 変換

`python -m osaconv <video> -o <out.osa> [オプション]`

| 引数 | 既定値 | 意味 |
|---|---|---|
| `video` | (必須) | 入力する動画 |
| `-o`, `--out` | (必須) | 出力する `.osa` |
| `--fps` | `30` | フレームレート |
| `--points` | `1000` | 1 フレームの点数 N |
| `--start` | `0.0` | 変換を始める位置(秒) |
| `--seconds` | 最後まで | 変換する長さ(秒)。ESP32 のフラッシュに埋め込むなら 35 秒前後が目安 |
| `--threshold` | 自動(大津法) | 二値化のしきい値 |
| `--invert` | オフ | 白黒を反転(白背景の動画で、画面の枠が出ないようにする) |
| `--blur` | `0` | ぼかし。奇数を指定。0 でなし |
| `--epsilon` | `1.0` | 輪郭の点の間引きの強さ。小さいほど滑らかで、点が増える |
| `--min-length` | `20.0` | これより短い輪郭は捨てる |
| `--external` | オフ | 外側の輪郭だけ使う |

### `python -m osaconv.stream`  映像だけを送る

`python -m osaconv.stream <osa> --port <port> [オプション]`

| 引数 | 既定値 | 意味 |
|---|---|---|
| `osa` | (必須) | 送る `.osa` |
| `--port` | (必須) | 例: `COM6` |
| `--baud` | `921600` | ボーレート |
| `--loop` | オフ | 最後まで行ったら先頭に戻る |
| `--start-frame` | `0` | 開始するフレーム番号 |
| `--benchmark SEC` | なし | 時刻を待たず、最高の速さで SEC 秒送り、通信の限界を測る |
| `--reset-wait` | `2.0` | ポートを開いたあとに待つ秒数 |

### `python -m osaconv.play`  映像と音声の同期再生

`python -m osaconv.play <osa> --audio <wav> --port <port> [オプション]`

| 引数 | 既定値 | 意味 |
|---|---|---|
| `osa` | (必須) | 映像の `.osa` |
| `--audio` | (必須) | 16bit PCM の `.wav` |
| `--port` | (必須) | 例: `COM6` |
| `--baud` | `921600` | ボーレート |
| `--offset-ms` | `0.0` | 映像と音声のずれの補正。`+` で映像が先に出る |
| `--loop` | オフ | くり返し再生 |
| `--reset-wait` | `2.0` | ポートを開いたあとに待つ秒数 |

### `scripts/`  補助ツール

| コマンド | 役割 | 引数 |
|---|---|---|
| `python scripts/view_osa.py <osa>` | `.osa` を PC 上に並べて確認 | `--count`(並べる数、既定 `6`)、`--save <画像>`(保存して終了) |
| `python scripts/tune_contour.py <画像か動画>` | 輪郭抽出をスライダーで調整 | `--frame`(見るフレーム、既定 `0`)、`--width`(表示の横幅、既定 `1500`)。キー: `q` 終了 / `p` 値を表示 / `s` 保存 / `←→` `a` `d` 前後のフレーム |
| `python scripts/make_test.py` | テスト用の `.osa`(円が動く)を作る | `-o`(既定 `test.osa`)、`--fps`(`30`)、`--points`(`1000`)、`--seconds`(`5.0`)、`--period`(`4.0`、1 周する秒数) |
| `python scripts/make_sync_test.py` | 映像と音声のずれを測るテストデータを作る | `--seconds`(`10`)、`--fps`(`30`)、`--points`(`1000`)、`--rate`(`44100`)、`--osa`(`sync_test.osa`)、`--wav`(`sync_test.wav`) |
| `python scripts/osa2h.py <osa> -o <out.h>` | `.osa` を C のヘッダに変換(フラッシュ埋め込み版向け) | `-o`(必須) |

### 映像と音声のずれを合わせる

```powershell
python scripts/make_sync_test.py
python -m osaconv.play sync_test.osa --audio sync_test.wav --port COM6 --loop
```

- 実行中に `+10` や `-10` と入力して Enter を押すと、映像のタイミングを 10ms ずつ動かせます(`+` で映像が先)。
- ぴったり合ったら、終了時に表示される値を `--offset-ms` に渡します。
- 音声は有線のスピーカーかヘッドホンで。Bluetooth は遅延が大きく、合わせにくいです。

### 通信に余裕があるか測る

```powershell
python -m osaconv.stream <生成ファイル名>.osa --port COM6 --baud 921600 --benchmark 10
```

`(+N/s)` の N が通信の限界(フレーム/秒)です。30 を十分に超えれば余裕があります。30〜35 だとぎりぎりで、本番で途切れるかもしれません。

| ボーレート | 理論上の限界(作者の計算) |
|---|---|
| 921600 | 約 45 フレーム/秒 |
| 2000000 | 約 99 フレーム/秒 |

2000000 を試すときは、**ESP32 の `BAUD` と PC の `--baud` の両方**を変えて、書き込み直してください。

## 問題と解決方法

### オシロスコープが変な風に映る

次の順に確認してください。

1. **XY モード**になっているか
2. CH1 と CH2 の**カップリングが両方とも DC** か(AC だと形がくずれます)
3. 2 つのチャンネルが**合成(ADD など)になっていないか**。X と Y が別々の入力として使われる設定にする
4. 拡大率(VOLTS/DIV)を 2 つのチャンネルで同じにする
5. 縦横比がおかしいときは `--scale-x` / `--scale-y` で補正する

### 正しく動くか確かめたい(`--no-serial`)

ESP32 やオシロがなくても、PC だけで確認できます。

```powershell
python -m osagame --no-serial --no-preview
```

`--no-serial` は ESP32 に送らず、PC 側の画面だけを動かします。`--port` は不要です。
`--no-preview` を外すと、PC 画面に線が描かれます。プログラムを改造したときの確認に便利です。

### 通信の症状

| 症状 | 意味・対処 |
|---|---|
| `crc` や `lost` が増え続ける | 通信が乱れている。ボーレートを下げる、短いケーブルに替える |
| `[PC] skipped` が増える | PC の送信が間に合っていない。他のアプリを閉じる、`--no-preview` を付ける |
| `ok` が 0 のまま、動く円しか出ない | ボーレートの不一致、またはシリアルモニタが開いている |
| 動画の途中で円に戻る | データが 1 秒以上途切れている |
| `tmo` が増える | 受信の途中で止まっている。ケーブルを確認する |
| `ModuleNotFoundError: sounddevice` | `pip install sounddevice` |

### 気をつけること

- **USB-シリアルチップの上限は、COM6 という名前だけでは分かりません。** デバイスマネージャーで名前を確認してください。一般に CP2102 は最大約 1Mbps、CH340 は約 2Mbps とされています。まず 921600 で試してください。
- ポートを開いた瞬間に ESP32 がリセットされることがあります。そのため DTR / RTS を無効にして開き、2 秒待っています(`--reset-wait`)。
- `Serial.printf` による**デバッグ表示は、映像の通信と同じ線に混ざります**。状況は `STAT` の行としてだけ返しています。
- 時間がたつほど重くなる問題は v3.1.1 で直しました。それでも重いときは `--profile` で調べられます。

## ディレクトリ構成

```
.
├── README.md
├── LICENSE
├── docs/
│   ├── AUDIO_SYNC_SPEC.md      音声同期の仕様書と引き継ぎメモ
│   └── EXTRACT_SPEC.md
├── firmware/
│   └── osa_stream/
│       └── osa_stream.ino      ESP32 のスケッチ(受信して DAC で描く)
└── tools/
    ├── requirements.txt
    ├── osaconv/                動画の変換と送信
    │   ├── convert.py          動画 → .osa(python -m osaconv の本体)
    │   ├── contour.py          輪郭の抽出
    │   ├── path.py             線の集まり → N 点(ジャンプは暗く)
    │   ├── pack.py             .osa の読み書き
    │   ├── stream.py           シリアル送信(映像のみ)。パケット形式の定義もここ
    │   └── play.py             映像 + 音声の同期再生
    ├── osagame/                メニュー、ゲーム、YouTube 再生
    │   ├── app.py              起動、キー入力、毎フレームの送信、メニュー定義(build_app)
    │   ├── screens.py          画面ごとのキー処理と画面遷移
    │   ├── ui.py               文字、メニュー、テキストボックス
    │   ├── font.py             文字の形(線の座標)
    │   ├── addvideo.py         YouTube の動画 ID → .osa + .wav → 再生
    │   ├── history.py          LEADERBOARD
    │   ├── osatetris/          TETRIS
    │   └── osapacman/          PAC MAN
    ├── scripts/                補助ツール(上のコマンドリファレンス参照)
    ├── source/                 home.osa、nyancat.osa、動画の保存先(addvideo/)
    ├── samples/
    └── tests/
```

## 改造するには

構成は次のとおりです。

| ファイル | 担当 | 役割 |
|---|---|---|
| `osagame/app.py` | ロジック(全体) | 起動、キー入力の受け取り、毎フレームの送信。メニュー項目の定義もここ(`build_app`) |
| `osagame/screens.py` | ロジック(画面) | 画面ごとの「キーが押されたらどうなるか」。画面遷移はここ |
| `osagame/ui.py` | 表示と小さな状態 | 文字、メニュー、テキストボックスの形を作る。カーソル位置や文字送りの進み具合も持つ |
| `osagame/font.py` | 表示(データ) | 文字の形(線の座標)だけ |
| `osaconv/path.py` | 表示(変換) | 線の集まりを、ジャンプを暗くした N 点に変換する |
| `osaconv/stream.py` | 通信 | パケットを作ってシリアルで送る |
| `osaconv/pack.py` | ファイル | `.osa` を読む |

動作フロー:

```
キー入力 ─ app.py ─→ screens.py の handle()     ← 状態を変える(ロジック)
                          │
毎フレーム:               ↓
screens.py の polylines() ─→ ui.py / font.py     ← 線(折れ線)を作る(表示)
        │
        ↓ app.render()
osaconv/path.py                                   ← 線 → N 点(uint8)
        │
        ↓
osaconv/stream.py ─→ シリアル ─→ ESP32 ─→ オシロ
```

`screens.py` は `pygame` を知りません。`app.py` がキーを `"up"` `"enter"` などの文字列に変換して渡すので、画面のロジックは PC だけで試せます。

よくある改造:

- **メニュー項目の追加**: `app.py` の `build_app()` の `Menu([...])` に `("名前", lambda: app.goto("画面名"))` を 1 行足す
- **新しい画面**: `screens.py` に `Screen` を継承したクラスを作り、`build_app()` で `app.register("名前", ...)` する。`handle()` がキー処理、`polylines()` が表示
- **文字の追加**: `font.py` の `GLYPHS` に 1 行足す
- **点滅や揺れ**: `ui.py` の `Menu.polylines()` や `TextBox.polylines()`
- **ホーム動画の差し替え**: `.osa` を作り、`--home <ファイル>` で指定する

## 更新履歴

- **v3.2.1**: ゲームの難易度を調整。TETRIS の HOLD を削除、PAC MAN のゴーストの AI を強化
- **v3.1.1**: 時間がたつほどゲームが重くなるバグを修正
  (`polylines_to_path` の `_order` が、折れ線の本数のおよそ 2 乗の回数 `_is_closed` を呼んでいたのが原因)
- **v3.0**: TETRIS、PAC MAN を追加(効果音つき)
- **v0.3.0**: 映像と音声の同期再生
- **v0.2.0**: PC からシリアルで送って再生
- **v0.1.0**: `.osa` を ESP32 のフラッシュに埋め込んで再生

## ライセンス

[MIT License](LICENSE)

ただし、次のものは対象外です。

- Bad Apple!! など、動画・音楽の権利は、それぞれの権利者にあります。テスト、セッティング用として
- YouTube の動画を使うときは、YouTube の利用規約と、動画の著作権を守ってください。
  
## AIの利用につい

このプロジェクトは、設計・実機での検証・統合を作者が行い、
コードの下書き、リファクタリング、README の文章作成に生成AI(Claude, Gemini)を使用しています。
すべての内容は作者が確認していますが、不具合があれば Issue で教えてください。て

## 謝辞

共同制作してくれた某部員　なれないpythonで急遽extract.pyを短期間で作ってくれてありがとう。
舞鶴高専　電気情報工学科の先生方 オシロスコープの使用許可をありがとうございます。