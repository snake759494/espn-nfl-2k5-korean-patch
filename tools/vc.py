"""VC_20919/0..4 분할 아카이브 (Visual Concepts). 헤더: n, 0, nparts, part sectors[..], 0x9c부터 (hash,size,sector)*n.
섹터는 전체 연결 기준 (part = 0x80000 섹터 = 1GB)."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import iso
SEC = 2048
PART = 0x80000
def parts(isop=iso.ISO):
    e = {p: (l, s) for p, l, s, r in iso.walk(isop)}
    return [e['VC_20919/%d.' % i] for i in range(5)]
def table(isop=iso.ISO):
    P = parts(isop)
    h = iso.read(P[0][0], 0x9c + 12 * 5000, isop)
    n = struct.unpack_from('<I', h, 0)[0]
    return [struct.unpack_from('<3I', h, 0x9c + 12 * i) for i in range(n)]
def iso_off(sector, isop=iso.ISO, P=None):
    P = P or parts(isop)
    pi, ps = divmod(sector, PART)
    return P[pi][0] * SEC + ps * SEC
def read(ent, isop=iso.ISO, P=None):
    h, s, sec = ent
    with open(isop, 'rb') as f:
        f.seek(iso_off(sec, isop, P)); return f.read(s)
if __name__ == '__main__':
    T = table(); P = parts()
    print(len(T))
    with open(iso.ISO, 'rb') as f:
        for h, s, sec in T:
            f.seek(iso_off(sec, P=P)); b = f.read(16)
            print('%08x %10d %8d %s %r' % (h, s, sec, b[:8].hex(), b[:16]))
