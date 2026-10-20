"""한글 ISO 전수조사: 모든 아카이브 파일(압축 체인 해제 + 비압축 꼬리)과 실행 파일에서
아직 영문으로 남은 화면 문구 후보를 찾는다 → work/audit.json {파일: [[구역, 문자위치, 칸, 문자열], ...]}"""
import os, sys, re, json
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import iso, vc, lz, datafiles
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KISO = os.path.join(ROOT, 'ESPN NFL 2K5 (USA) (Korean).iso')
SKIP = {'TXTR': False}
def english(t):
    s = re.sub(r'\|[A-Z0-9_/]+\|', ' ', t).strip()
    if len(s) < 4: return False
    if re.search(r'[_\\]|\.(iff|irx|bin|ps2)\b|^[a-z]+[A-Z]', s): return False
    words = re.findall(r"[A-Za-z']+", s)
    if len(words) < 2: return False
    if sum(1 for w in words if len(w) > 1) < 2: return False
    if not re.search(r'[a-z]{2}', s) and len(words) < 2: return False
    if re.search(r'(.)\1\1\1', s): return False
    return True
def scan(ent):
    h, size, sec = ent
    if size > 40_000_000 or size < 16: return h, []
    with open(KISO, 'rb') as f:
        f.seek(vc.iso_off(sec, KISO, P)); d = f.read(size)
    out = []
    ch, end = lz.chain(d)
    units = []
    if ch:
        for o, mg, A, B, C, D in ch:
            try: units.append(('c%x' % o, lz.decompress(d[o + 0x20:o + 0x20 + A])[0]))
            except Exception: pass
        units.append(('t%x' % end, d[end:] if end % 2 == 0 else d[end + 1:]))
    else:
        units.append(('r', d))
    for tag, u in units:
        for s, e, t in datafiles.u16_runs(u, 4):
            if english(t): out.append([tag, s, e - s, t])
    return h, out
P = None
def init():
    global P; P = vc.parts(KISO)
if __name__ == '__main__':
    T = vc.table(KISO)
    res = {}
    with Pool(max(2, os.cpu_count() - 1), initializer=init) as p:
        for h, out in p.imap_unordered(scan, T, chunksize=4):
            if out: res['%08x' % h] = out
    el, es = {p: (l, s) for p, l, s, r in iso.walk(KISO)}['SLUS_209.19']
    elf = iso.read(el, es, KISO)
    import ktext
    res['ELF'] = [['elf', o, mx, s] for o, s, mx in ktext.elf_strings(elf) if english(s)]
    json.dump(res, open(os.path.join(ROOT, 'work', 'audit.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(res), 'files', sum(len(v) for v in res.values()), 'strings')
