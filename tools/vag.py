"""PS2 SPU ADPCM(VAG) 디코드/인코드. 16바이트 프레임 = [shift|filter<<4][flags][14바이트 = 28 샘플]."""
import numpy as np
F = [(0, 0), (60, 0), (115, -52), (98, -55), (122, -60)]
def decode(data, hist=(0, 0)):
    n = len(data) // 16
    out = np.empty(n * 28, np.int16)
    h1, h2 = hist
    o = 0
    for i in range(n):
        fr = data[16 * i:16 * i + 16]
        sh = fr[0] & 15; fl = (fr[0] >> 4) & 7
        if fl > 4: fl = 0
        f0, f1 = F[fl]
        for b in fr[2:16]:
            for nib in (b & 15, b >> 4):
                s = (nib - 16 if nib >= 8 else nib) << 12
                s = (s >> sh) + ((h1 * f0 + h2 * f1 + 32) >> 6)
                s = max(-32768, min(32767, s))
                out[o] = s; o += 1
                h2, h1 = h1, s
    return out
def flags(data):
    """프레임 플래그 배열(1=루프 끝/종료, 3=루프, 4=루프 시작, 7=무음 종료 등)"""
    return np.frombuffer(data, np.uint8)[1::16]
def encode(pcm):
    """int16 → VAG 프레임 (필터·시프트 전수 탐색, 간단 구현)"""
    pcm = np.asarray(pcm, np.int32)
    pad = (-len(pcm)) % 28
    if pad: pcm = np.concatenate([pcm, np.zeros(pad, np.int32)])
    out = bytearray(); h1 = h2 = 0
    for i in range(0, len(pcm), 28):
        blk = pcm[i:i + 28]; best = None
        for fl in range(5):
            f0, f1 = F[fl]
            for sh in range(13):
                a1, a2 = h1, h2; err = 0; nib = []
                for x in blk:
                    pred = (a1 * f0 + a2 * f1 + 32) >> 6
                    q = int(round(((int(x) - pred) << sh) / 4096.0)) if sh <= 12 else 0
                    q = max(-8, min(7, q))
                    s = max(-32768, min(32767, ((q << 12) >> sh) + pred))
                    err += (int(x) - s) ** 2; nib.append(q & 15); a2, a1 = a1, s
                if best is None or err < best[0]: best = (err, fl, sh, nib, a1, a2)
                if err == 0: break
        _, fl, sh, nib, h1, h2 = best
        fr = bytearray([sh | (fl << 4), 0]) + bytes(nib[k] | (nib[k + 1] << 4) for k in range(0, 28, 2))
        out += fr
    return bytes(out)
