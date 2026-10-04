"""아카이브의 리소스(압축 체인 포함)에서 화면 문구 후보(UTF-16 0 종료 칸) 수집 → work/res_strings.json
{ "hash": [[리소스 오프셋(-1=비압축 원본), [[문자위치, 칸길이, 문자열], ...]], ...] }"""
import os, sys, re, json, glob
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import lz, datafiles
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SKIPTYPES = {'TXTR', 'AUDO', 'Unif', 'TSET', 'bin', 'MANU', 'TRIV', 'HITX', 'HiSn'}
IDENT = re.compile(r'[_\\/]|^[a-z0-9]|[a-z][A-Z]|\.\w{2,4}$|^[A-Z0-9]+\d$|^\W+$')
def is_ui(t):
    s = t.strip()
    if len(s) < 2 or not re.search(r'[A-Za-z]{2}', s): return False
    if IDENT.search(s): return False
    return True
def units(d):
    ch, end = lz.chain(d)
    if not ch: return [(-1, d)]
    out = []
    for o, mg, A, B, C, D in ch:
        u, p = lz.decompress(d[o + 0x20:o + 0x20 + A]); out.append((o, u))
    return out
def scan(fn):
    h = os.path.basename(fn).split('.')[0]
    d = open(fn, 'rb').read()
    res = []
    try:
        for o, u in units(d):
            ss = [[s, e - s, t] for s, e, t in datafiles.u16_runs(u) if is_ui(t)]
            if ss: res.append([o, ss])
    except Exception as ex:
        return h, 'ERR ' + str(ex)
    return h, res
if __name__ == '__main__':
    fs = [f for f in sorted(glob.glob(os.path.join(ROOT, 'extract', 'vc', '*'))) if f.split('.')[-1] not in SKIPTYPES]
    out = {}
    with Pool(max(2, os.cpu_count() - 1)) as p:
        for i, (h, r) in enumerate(p.imap_unordered(scan, fs, chunksize=4)):
            if r: out[h] = r
    json.dump(out, open(os.path.join(ROOT, 'work', 'res_strings.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    n = sum(len(x[1]) for v in out.values() if isinstance(v, list) for x in v)
    print(len(fs), 'files', len(out), 'with text', n, 'strings')
