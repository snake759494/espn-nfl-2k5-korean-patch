"""빌드 준비: 사용자의 원본 ISO 에서 원문 묶음(work/batches/*.json)과 작업 파일을 다시 만든다.
translation/index/*.json 의 위치 정보로 영어 원문을 읽어 온다(저장소에는 원문을 넣지 않음)."""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import iso, vc, lz
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def main():
    os.makedirs(os.path.join(ROOT, 'work', 'batches'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'extract', 'vc'), exist_ok=True)
    el, es = {p: (l, s) for p, l, s, r in iso.walk()}['SLUS_209.19']
    elf = iso.read(el, es)
    open(os.path.join(ROOT, 'extract', 'SLUS_209.19'), 'wb').write(elf)
    T = {'%08x' % e[0]: e for e in vc.table()}; P = vc.parts()
    # 추출본(분석·전수조사 도구용)
    for h, e in T.items():
        if e[1] > 40_000_000: continue
        d = vc.read(e, P=P)
        tag = d[:4].decode('latin1') if d[:4].isalnum() else 'bin'
        open(os.path.join(ROOT, 'extract', 'vc', '%s.%s' % (h, tag)), 'wb').write(d)
    cache = {}
    def blob(src, unit):
        k = (src, unit)
        if k not in cache:
            d = elf if src == 'elf' else vc.read(T[src], P=P)
            if unit != 'r':
                o = int(unit[1:], 16); A = int.from_bytes(d[o + 4:o + 8], 'little')
                d = lz.decompress(d[o + 0x20:o + 0x20 + A])[0]
            cache[k] = d
        return cache[k]
    n = 0
    for ip in sorted(glob.glob(os.path.join(ROOT, 'translation', 'index', '*.json'))):
        out = []
        for it in json.load(open(ip, encoding='utf-8')):
            src, unit, off, ln = it['loc']
            en = blob(src, unit)[off:off + 2 * ln].decode('utf-16-le')
            out.append({k: v for k, v in it.items() if k != 'loc'} | {'en': en})
            n += 1
        json.dump(out, open(os.path.join(ROOT, 'work', 'batches', os.path.basename(ip)), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('batches restored:', n, 'strings')
if __name__ == '__main__': main()
