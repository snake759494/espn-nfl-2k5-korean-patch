"""(제작자용) work/batches/*.json → translation/index/*.json : 영어 원문 대신 원본 ISO 안의 위치만 기록.
위치 = [출처, 구역, 바이트 오프셋, 글자 수]  출처: 'elf' 또는 아카이브 해시(8자리), 구역: 'r'(원본 그대로) 또는 'c<오프셋>'(압축 리소스 해제본)"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import iso, vc, lz, datafiles
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DECOMP = (0x107a62a5, 0x8ee9eeed)          # 압축 리소스 안에서 문자열을 쓰는 파일
def sources():
    el, es = {p: (l, s) for p, l, s, r in iso.walk()}['SLUS_209.19']
    yield 'elf', 'r', iso.read(el, es)
    P = vc.parts()
    for h, size, sec in vc.table():
        if size > 40_000_000: continue
        d = vc.read((h, size, sec), P=P)
        yield '%08x' % h, 'r', d
        if h in DECOMP:
            for o, mg, A, B, C, D in lz.chain(d)[0]:
                yield '%08x' % h, 'c%x' % o, lz.decompress(d[o + 0x20:o + 0x20 + A])[0]
def main():
    need = {}
    for bp in sorted(glob.glob(os.path.join(ROOT, 'work', 'batches', '*.json'))):
        for it in json.load(open(bp, encoding='utf-8')): need[it['en']] = None
    left = set(need)
    blobs = []
    for src, unit, d in sources():
        if not left: break
        for s, e, t in datafiles.u16_runs(d, 1):
            if t in left: need[t] = [src, unit, 2 * s, e - s]; left.discard(t)
        blobs.append((src, unit, d))
    # 칸 안 일부(접두 글자가 붙은 경우 등): 부분 문자열 검색
    for t in list(left):
        b = t.encode('utf-16-le')
        for src, unit, d in blobs:
            i = d.find(b)
            if i >= 0: need[t] = [src, unit, i, len(t)]; left.discard(t); break
    os.makedirs(os.path.join(ROOT, 'translation', 'index'), exist_ok=True)
    for bp in sorted(glob.glob(os.path.join(ROOT, 'work', 'batches', '*.json'))):
        out = []
        for it in json.load(open(bp, encoding='utf-8')):
            loc = need[it['en']]
            if not loc:                       # 원본에 없는 문자열(번역문이 다시 잡힌 경우 등) → 제외
                print('  skip (not in original):', os.path.basename(bp), it['id']); continue
            out.append({k: v for k, v in it.items() if k not in ('en', 'ctx')} | {'loc': loc})
        json.dump(out, open(os.path.join(ROOT, 'translation', 'index', os.path.basename(bp)), 'w', encoding='utf-8'), separators=(',', ':'))
    print('indexed', len(need), 'missing', len(left))
if __name__ == '__main__': main()
