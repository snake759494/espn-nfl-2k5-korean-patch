"""해설·선수 이름 음성(ADPCM 원시 스트림)과 그 클립 색인(FONT 묶음 8ee9eeed 안 SPCI 표).
색인 표: [해시, 1, 22050, 0xC000, 0] + 바이트 오프셋[n+1] (마지막 = 스트림 크기)."""
import os, sys, struct, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import vc, iso
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
STREAMS = {'comm': 0x6421cfe6, 'names': 0x0c508bdb, 'pa': 0x03d494df, 'misc': 0xaa692c32}
FONT = 0x8ee9eeed
RATE = 22050
def find_tables(font, sizes):
    a = np.frombuffer(font[:len(font) // 4 * 4], np.uint32).astype(np.int64)
    out = {}
    for name, sz in sizes.items():
        k = int(np.where(a == sz)[0][-1]); j = k
        while j > 0 and a[j - 1] < a[j]: j -= 1
        assert a[j] == 0 and a[j - 3] == RATE, (name, a[j - 5:j])
        out[name] = (4 * j, a[j:k + 1].copy())          # (표 바이트 위치, 오프셋 배열)
    return out
class Speech:
    def __init__(self, isop=iso.ISO):
        self.isop = isop
        T = {e[0]: e for e in vc.table(isop)}; self.P = vc.parts(isop)
        self.ent = {n: T[h] for n, h in STREAMS.items()}
        font = vc.read(T[FONT], isop, self.P)
        self.tables = find_tables(font, {n: self.ent[n][1] for n in STREAMS})
        self.f = open(isop, 'rb')
    def count(self, name): return len(self.tables[name][1]) - 1
    def raw(self, name, i):
        off = self.tables[name][1]
        h, size, sec = self.ent[name]
        self.f.seek(vc.iso_off(sec, self.isop, self.P) + int(off[i])); return self.f.read(int(off[i + 1] - off[i]))
    def pcm(self, name, i):
        import vag
        return vag.decode(self.raw(name, i))
