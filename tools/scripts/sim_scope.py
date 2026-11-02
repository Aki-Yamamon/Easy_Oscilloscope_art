""".osa を、PC の画面上の「仮想オシロスコープ」で再生する（実機なしで確認する用）。

    python scripts/sim_scope.py source/senbonzakura_mix.osa --audio source/senbonzakura.wav
    python scripts/sim_scope.py source/badapple.osa --audio source/badapple.wav --start 60

見え方:
    ・実機と同じく、点を順番に線でつなぐ。輪郭から輪郭へのジャンプ（長い線）は、
      ビームが速く動くので暗く描く
    ・蛍光面の残光を、前の画面を少しずつ暗くすることで真似る（--persistence）

操作: ESC / ウィンドウを閉じる = 終了、SPACE = 一時停止（音声なしのときだけ）、←/→ = 5 秒戻る/進む（音声なしのときだけ）
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from osaconv.pack import read_osa
from osaconv.play import AudioClock, load_wav

BEAM = np.array([90, 255, 120], dtype=np.float32)    # 線の色（緑の蛍光面）
JUMP_DIM = 18.0                                        # この長さ（DAC 単位）を超える線は暗くする


def segment_colors(xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """点列 → (始点, 終点, 色) を作る。長い線ほど暗い。"""
    p = xy.astype(np.float32)
    a, b = p[:-1], p[1:]
    length = np.hypot(*(b - a).T)
    bright = np.where(length <= JUMP_DIM, 1.0, np.clip(JUMP_DIM / np.maximum(length, 1e-6), 0.08, 1.0) * 0.5)
    return np.stack([a, b], axis=1), bright


def main() -> None:
    ap = argparse.ArgumentParser(description=".osa を仮想オシロスコープで再生する")
    ap.add_argument("osa")
    ap.add_argument("--audio", help="一緒に鳴らす 16bit PCM の WAV")
    ap.add_argument("--start", type=float, default=0.0, help="開始位置（秒）")
    ap.add_argument("--size", type=int, default=640, help="ウィンドウの一辺（ピクセル）")
    ap.add_argument("--persistence", type=float, default=0.55,
                    help="残光の強さ 0〜0.95（0 = 残光なし）")
    ap.add_argument("--loop", action="store_true", help="最後まで行ったら先頭に戻る（音声なしのとき）")
    args = ap.parse_args()

    import pygame as pg

    header, frames, _ = read_osa(args.osa)
    fps, total = header.fps, header.frame_count
    duration = total / fps
    print(f"{args.osa}: {total} frames / {fps}fps / {header.points_per_frame} 点 / {duration:.1f}s")

    pg.init()
    S = args.size
    screen = pg.display.set_mode((S, S))
    pg.display.set_caption(f"仮想オシロ - {Path(args.osa).name}")
    font = pg.font.SysFont(None, 20)
    scale = (S - 1) / 255.0
    fade = pg.Surface((S, S))
    fade.fill((0, 0, 0))
    fade.set_alpha(int(255 * (1.0 - max(0.0, min(0.95, args.persistence)))))
    grid = pg.Surface((S, S), pg.SRCALPHA)
    for k in range(1, 8):                                  # 目盛り（8 × 8 マス）
        c = round(k * S / 8)
        pg.draw.line(grid, (60, 80, 70, 70), (c, 0), (c, S))
        pg.draw.line(grid, (60, 80, 70, 70), (0, c), (S, c))

    # ---- 時計（音声があれば音声の再生位置、なければ PC の時計）----
    stream = None
    clock = None
    if args.audio:
        import sounddevice as sd
        data, sr = load_wav(args.audio)
        clock = AudioClock(sr)
        state = {"pos": int(args.start * sr)}

        def callback(out, n, _t, _status):
            s = state["pos"]
            clock.on_block(s)
            m = max(0, min(n, len(data) - s))
            if m:
                out[:m] = data[s:s + m]
            out[m:] = 0
            state["pos"] = s + n

        stream = sd.OutputStream(samplerate=sr, channels=data.shape[1], dtype="int16",
                                 callback=callback, blocksize=1024)
        stream.start()
        clock.latency_s = float(stream.latency)
    t0 = time.perf_counter() - args.start
    paused_at = None

    def now() -> float:
        if clock is not None:
            p = clock.position()
            return args.start if p is None else p
        return (paused_at if paused_at is not None else time.perf_counter()) - t0

    tick = pg.time.Clock()
    last = -1
    running = True
    try:
        while running:
            for e in pg.event.get():
                if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
                    running = False
                elif e.type == pg.KEYDOWN and clock is None:
                    if e.key == pg.K_SPACE:
                        if paused_at is None:
                            paused_at = time.perf_counter()
                        else:
                            t0 += time.perf_counter() - paused_at
                            paused_at = None
                    elif e.key == pg.K_RIGHT:
                        t0 -= 5.0
                    elif e.key == pg.K_LEFT:
                        t0 = min(t0 + 5.0, time.perf_counter())

            t = now()
            i = int(t * fps)
            if i >= total:
                if args.loop and clock is None:
                    t0 = time.perf_counter()
                    i = 0
                else:
                    break
            i = max(0, i)

            screen.blit(fade, (0, 0))                      # 残光: 前の画面を少し暗くする
            segs, bright = segment_colors(frames[i])
            pts = segs * scale
            pts[..., 1] = (S - 1) - pts[..., 1]            # y は上向きが正
            cols = (BEAM[None, :] * bright[:, None]).astype(int).tolist()
            for (a, b), col in zip(pts.tolist(), cols):
                pg.draw.aaline(screen, col, a, b)
            screen.blit(grid, (0, 0))
            label = font.render(f"{t:6.1f}s / {duration:.1f}s  frame {i + 1}/{total}"
                                f"{'  [PAUSE]' if paused_at is not None else ''}", True, (150, 190, 160))
            pg.draw.rect(screen, (0, 0, 0), (4, 4, label.get_width() + 6, label.get_height() + 4))
            screen.blit(label, (7, 6))
            pg.display.flip()
            last = i
            tick.tick(60)
    except KeyboardInterrupt:
        pass
    finally:
        if stream is not None:
            stream.stop()
            stream.close()
        pg.quit()
    print(f"終了: frame {last + 1}/{total}")


if __name__ == "__main__":
    main()
