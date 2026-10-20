"""numba 가속 PS2 SPU ADPCM 인코더(프레임마다 필터 5 × 시프트 13 전수 탐색, 오차 최소)."""
import numpy as np
from numba import njit
F0 = np.array([0, 60, 115, 98, 122], np.int64)
F1 = np.array([0, 0, -52, -55, -60], np.int64)
@njit(cache=True)
def _enc(pcm, out, F0, F1):
    n = len(pcm) // 28
    h1 = 0; h2 = 0
    nib = np.zeros(28, np.int64); bn = np.zeros(28, np.int64)
    for f in range(n):
        best = -1.0; bfl = 0; bsh = 0; bh1 = 0; bh2 = 0
        for fl in range(5):
            f0 = F0[fl]; f1 = F1[fl]
            for sh in range(13):
                a1 = h1; a2 = h2; err = 0.0
                for k in range(28):
                    x = pcm[28 * f + k]
                    pred = (a1 * f0 + a2 * f1 + 32) >> 6
                    d = (x - pred) << sh
                    q = (d + (2048 if d >= 0 else -2048)) // 4096
                    if q > 7: q = 7
                    if q < -8: q = -8
                    s = ((q << 12) >> sh) + pred
                    if s > 32767: s = 32767
                    if s < -32768: s = -32768
                    e = x - s; err += e * e
                    nib[k] = q & 15; a2 = a1; a1 = s
                    if best >= 0 and err >= best: break
                if best < 0 or err < best:
                    best = err; bfl = fl; bsh = sh; bh1 = a1; bh2 = a2
                    for k in range(28): bn[k] = nib[k]
        h1 = bh1; h2 = bh2
        o = 16 * f
        out[o] = bsh | (bfl << 4); out[o + 1] = 2
        for k in range(14): out[o + 2 + k] = bn[2 * k] | (bn[2 * k + 1] << 4)
def encode(pcm, flag=2):
    """int16 배열 → VAG 프레임 바이트 (모든 프레임 플래그 = flag, 원본 해설 스트림과 같은 2)"""
    pcm = np.asarray(pcm, np.int64)
    pad = (-len(pcm)) % 28
    if pad: pcm = np.concatenate([pcm, np.zeros(pad, np.int64)])
    out = np.zeros(len(pcm) // 28 * 16, np.uint8)
    _enc(pcm, out, F0, F1)
    out[1::16] = flag
    return out.tobytes()
