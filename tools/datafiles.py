"""아카이브 데이터 파일 번역 (제자리, 칸 길이 이내).
MANU(87408605): 미리 파싱된 HTML. 텍스트 노드는 UTF-16 0 종료 칸 → 칸 안에서 교체."""
import struct, re
OKCH = set([9, 10, 13, 0xae, 0x2122, 0xe9, 0x2019, 0x201c, 0x201d])
def u16_runs(d, minlen=2):
    u = struct.unpack('<%dH' % (len(d) // 2), d[:len(d) // 2 * 2])
    out = []; start = None
    for i, x in enumerate(u):
        ok = x in OKCH or 0x20 <= x <= 0x7e
        if ok and start is None: start = i
        if not ok:
            if start is not None and x == 0 and i - start >= minlen:
                out.append((start, i, ''.join(map(chr, u[start:i]))))
            start = None
    return out
def has_text(s):
    return re.search('[A-Za-z]{3}', re.sub(r'<[^>]*>|\|[^|]*\|', '', s)) is not None
def manu_segments(d):
    return [(s, e, t) for s, e, t in u16_runs(d) if has_text(t)]
def manu(d, tr):
    return inplace(d, tr.getter('manu'), manu_segments(d))
def inplace(d, g, segs):
    b = bytearray(d); n = 0
    for s, e, t in segs:
        v = g(t)
        if v is None: continue
        if len(v) > e - s:
            print('  [too long]', repr(t[:40])); continue
        b[2 * s:2 * e] = v.encode('utf-16-le') + bytes(2 * (e - s - len(v)))
        n += 1
    return bytes(b), n
def triv(d, tr):
    g1, g2 = tr.getter('triv', names=True), tr.getter('lay')
    return inplace(d, lambda t: g1(t) or g2(t), manu_segments(d))
def drct(d, tr):
    g1, g2, g3 = tr.getter('drct'), tr.getter('lay', names=True), tr.getter('nm')
    import ktext; PS = ktext.playset()
    segs = [(s, e, t) for s, e, t in u16_runs(d) if (' ' in t.strip() and re.search('[A-Za-z]{2}', t)) or t in PS]
    return inplace(d, lambda t: (g3(t) if t in PS else None) or g1(t) or g2(t), segs)
def scne_plays(d, tr):
    """압축 체인 SCNE 안의 작전명 → 플레이북과 같은 번역 (해제·교체·재압축)"""
    import lz, ktext, struct
    PS = ktext.playset(); gn = tr.getter('nm'); gl = tr.getter('lay', names=True)
    def g(t): return (gn(t) if t in PS else None) or gl(t)
    def want(t): return t in PS or (' ' in t.strip() and gl(t) is not None)
    ch, end = lz.chain(d)
    out = bytearray(); n = 0; pos = 0
    for o, mg, A, B, C, D in ch:
        out += d[pos:o]
        u, _ = lz.decompress(d[o + 0x20:o + 0x20 + A])
        segs = [(s, e, t) for s, e, t in u16_runs(u) if want(t)]
        u2, k = inplace(u, g, segs)
        if k:
            nb = d[o + 0x28]
            comp = lz.compress(u2, nb=nb, extra=struct.unpack_from('<I', d, o + 0x24)[0])
            assert lz.decompress(comp)[0] == u2
            comp += bytes((-len(comp)) % 16)
            out += d[o:o + 4] + struct.pack('<I', len(comp)) + d[o + 8:o + 0x20] + comp
            n += k
        else:
            out += d[o:o + 0x20 + A]
        pos = o + 0x20 + A
    tail = d[pos:]
    if len(tail) % 2 == 0 and pos % 2 == 0:
        segs = [(s, e, t) for s, e, t in u16_runs(tail) if want(t)]
        tail, k = inplace(tail, g, segs); n += k
    out += tail
    return bytes(out), n
HANDLERS = {0x107a62a5: scne_plays, 0x87408605: manu, 0x5a14cf27: triv, 0xc59d46a8: drct,
            0x0b1a755e: drct, 0x15bc1b16: drct, 0x613f39cf: drct, 0xc1cd47b1: drct, 0xc9e499cf: drct}
