"""VC LZSS (SLUS 0x128838).  스트림: u32 해제크기, u32 ?, u8 오프셋비트수 n, 이후 플래그(LSB 먼저, 1=매치).
매치: u16 w, off = w & (2^n-1), len = (w>>n)+3, 뒤에서부터 복사(dst[i]=dst[i-off])."""
import struct
def decompress(src):
    usize = struct.unpack_from('<I', src, 0)[0]
    nb = src[8]; p = 9
    out = bytearray(usize)
    o = 0; mo = (1 << nb) - 1; ml = (1 << (16 - nb)) - 1
    while o < usize:
        fl = src[p]; p += 1
        for b in range(8):
            if o >= usize: break
            if fl >> b & 1:
                w = src[p] | src[p + 1] << 8; p += 2
                off = w & mo; ln = ((w >> nb) & ml) + 3
                for i in range(ln - 1, -1, -1):
                    if o + i < usize: out[o + i] = out[o + i - off] if o + i - off >= 0 else 0
                    # (원본은 경계 검사 없음)
                o += ln
            else:
                out[o] = src[p]; p += 1; o += 1
    return bytes(out), p
def compress(data, nb=12, extra=1):
    """겹치지 않는 매치(off>=len)만 써서 앞/뒤 복사 차이가 없게."""
    n = len(data); maxoff = (1 << nb) - 1; maxlen = (1 << (16 - nb)) - 1 + 3
    out = bytearray(struct.pack('<II', n, extra)); out.append(nb)
    head = {}
    i = 0; flags_pos = None; bit = 8
    def flag(v):
        nonlocal flags_pos, bit
        if bit == 8:
            flags_pos = len(out); out.append(0); bit = 0
        if v: out[flags_pos] |= 1 << bit
        bit += 1
    chains = {}
    while i < n:
        best_l = 0; best_o = 0
        if i + 3 <= n:
            key = data[i:i + 3]
            cand = chains.get(key)
            if cand:
                for j in reversed(cand[-64:]):
                    off = i - j
                    if off > maxoff: break
                    lim = min(maxlen, off, n - i)
                    if lim < 3: continue
                    l = 3
                    if data[j:j + 3] != key: continue
                    while l < lim and data[j + l] == data[i + l]: l += 1
                    if l > best_l: best_l, best_o = l, off
                    if l == lim and lim == maxlen: break
        if best_l >= 3:
            flag(1); w = best_o | ((best_l - 3) << nb); out += struct.pack('<H', w)
            for k in range(i, i + best_l):
                if k + 3 <= n: chains.setdefault(data[k:k + 3], []).append(k)
            i += best_l
        else:
            flag(0); out.append(data[i])
            if i + 3 <= n: chains.setdefault(data[i:i + 3], []).append(i)
            i += 1
    return bytes(out)
def chain(d):
    """연속 리소스 (magic, A=payload크기, B, C, FEEDBEEF?, D) 목록."""
    out = []; o = 0
    while o + 0x20 <= len(d):
        mg = d[o:o + 4]
        A, B, C, F, D = struct.unpack_from('<5I', d, o + 4)
        if F != 0xfeedbeef: break
        out.append((o, mg, A, B, C, D))
        o += 0x20 + A
    return out, o
