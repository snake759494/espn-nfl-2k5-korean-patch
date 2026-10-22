"""PSS 동영상(MPEG-PS + 개인 스트림 0xBD 의 SShd/SSbd 오디오) 오디오 추출·교체 도우미."""
import os, sys, struct, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import vc, iso, vag
def packets(d):
    """(페이로드 시작, 끝) 목록 — 0xBD 패킷의 오디오 바이트 위치(원본 내 절대 위치)."""
    out = []; i = 0
    while True:
        i = d.find(b'\x00\x00\x01\xbd', i)
        if i < 0: break
        L = int.from_bytes(d[i + 4:i + 6], 'big'); hl = d[i + 8]; p = i + 9 + hl
        while d[p] == 0xff: p += 1
        p += 3                                        # 하위 스트림 id + 2바이트
        out.append((p, i + 6 + L)); i = i + 6 + L
    return out
def audio(d):
    pk = packets(d); s = b''.join(d[a:b] for a, b in pk)
    assert s[:4] == b'SShd', s[:16]
    typ, rate, ch, il = struct.unpack_from('<IIII', s, 8)
    assert s[0x20:0x24] == b'SSbd'; size = struct.unpack_from('<I', s, 0x24)[0]
    return pk, dict(type=typ, rate=rate, ch=ch, il=il, size=size, hdr=0x28), s
def _layout(info):
    """채널별 (본문 내 시작, 길이) 블록 목록. 마지막 덜 찬 블록은 채널마다 절반씩."""
    il, ch, size = info['il'], info['ch'], info['size']
    full = size // (il * ch); r = size - full * il * ch
    lay = [[] for _ in range(ch)]
    for k in range(full):
        for c in range(ch): lay[c].append(((k * ch + c) * il, il))
    if r:
        h = r // ch
        for c in range(ch): lay[c].append((full * il * ch + c * h, h))
    return lay
def decode(s, info):
    body = s[info['hdr']:info['hdr'] + info['size']]
    chans = [vag.decode(b''.join(body[a:a + n] for a, n in L)) for L in _layout(info)]
    n = min(map(len, chans)); return np.stack([x[:n] for x in chans], 1)
def encode(x, info):
    """(샘플, 채널) int16 → 원본과 같은 길이의 SSbd 본문 바이트"""
    import vagfast
    body = bytearray(info['size'])
    for c, L in enumerate(_layout(info)):
        tot = sum(n for _, n in L) // 16 * 28
        pcm = np.zeros(tot, np.int64); m = min(tot, len(x)); pcm[:m] = x[:m, c]
        b = vagfast.encode(pcm); p = 0
        for a, n in L: body[a:a + n] = b[p:p + n]; p += n
    return bytes(body)
def patch(d, body, info, pk):
    """동영상 바이트 d 의 오디오 본문을 body 로 바꾼 새 바이트(패킷 위치·크기 그대로)."""
    s = bytearray(b''.join(d[a:b] for a, b in pk))
    s[info['hdr']:info['hdr'] + info['size']] = body
    out = bytearray(d); p = 0
    for a, b in pk: out[a:b] = s[p:p + b - a]; p += b - a
    return bytes(out)
def read(h, isop=iso.ISO):
    E = {e[0]: e for e in vc.table(isop)}; P = vc.parts(isop); e = E[h]
    f = open(isop, 'rb'); f.seek(vc.iso_off(e[2], isop, P)); return f.read(e[1])
