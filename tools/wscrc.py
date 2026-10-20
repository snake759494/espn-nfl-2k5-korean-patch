"""한글판 ISO 의 실행 파일 CRC(PCSX2 방식: 32비트 워드 XOR)를 계산하고, 와이드 패치 대상 명령이 원본과 같은지 확인한다.
python tools/wscrc.py ["한글판.iso"]"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__)); import iso
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def crc(d):
    c = 0
    for w in struct.unpack('<%dI' % (len(d) // 4), d[:len(d) // 4 * 4]): c ^= w
    return c
def v2o(d, va):
    ph = struct.unpack_from('<I', d, 0x1c)[0]
    for i in range(struct.unpack_from('<H', d, 0x2c)[0]):
        t, off, v, pa, fs, ms, fl, al = struct.unpack_from('<8I', d, ph + 32 * i)
        if v <= va < v + fs: return va - v + off
if __name__ == '__main__':
    k = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'ESPN NFL 2K5 (USA) (Korean).iso')
    el, es = {p: (l, s) for p, l, s, r in iso.walk(k)}['SLUS_209.19']
    d = iso.read(el, es, k)
    print('CRC %08X  -> widescreen/SLUS-20919_%08X.pnach' % (crc(d), crc(d)))
    for a, w in ((0x1ea324, 0x3c013f80), (0x12cea8, 0x3c013f80), (0x111e10, 0x460039c3)):
        v = struct.unpack_from('<I', d, v2o(d, a))[0]
        print('  %08x %s' % (a, 'OK' if v == w else 'CHANGED %08x' % v))
