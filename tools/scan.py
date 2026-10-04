"""모든 아카이브 파일(압축 리소스 포함)에서 영문 UTF-16 문자열 후보 수집."""
import sys, os, glob, re, json, struct
sys.path.insert(0, os.path.dirname(__file__)); import lz, wstrs
WORD = re.compile(r'[A-Za-z]{3,}')
def units(d):
    """(구분, 데이터) - 압축 체인이면 각 리소스 해제, 아니면 원본"""
    ch, end = lz.chain(d)
    if not ch: return [('raw', d)]
    out = []
    for o, mg, A, B, C, D in ch:
        u, p = lz.decompress(d[o + 0x20:o + 0x20 + A])
        out.append(('%x' % o, u))
    if end < len(d): out.append(('tail%x' % end, d[end:]))
    return out
if __name__ == '__main__':
    res = {}
    for f in sorted(glob.glob('extract/vc/*')):
        d = open(f, 'rb').read()
        if len(d) > 40_000_000: continue
        name = os.path.basename(f)
        tot = 0; samples = []
        for tag, u in units(d):
            for o, s in wstrs.find(u, 4):
                if len(WORD.findall(s)) >= 1 and sum(c.isalpha() for c in s) >= 4:
                    tot += 1
                    if len(samples) < 6: samples.append(s[:60])
        if tot: res[name] = (tot, samples)
    for k, (n, s) in sorted(res.items(), key=lambda x: -x[1][0]):
        print(n, n and '', len(s) and '', n, s[:4])
