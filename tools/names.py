"""선수·코치 이름, 구단·도시·경기장(ROST), 작전명·포메이션(PLAY), 크립 항목(CRIB) 추출/적용.
모두 UTF-16 0 종료 칸 → 칸 안에서 제자리 교체."""
import os, sys, re, json, glob
sys.path.insert(0, os.path.dirname(__file__)); import datafiles
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TYPES = ('ROST', 'PLAY', 'CRIB')
OK = re.compile(r"[A-Za-z0-9 .'&\-,!?:()/#+]+")
def is_name(t):
    s = t.strip()
    if len(s) < 2 or not OK.fullmatch(s): return False
    if not re.search(r'[A-Za-z]', s): return False
    if re.fullmatch(r'[a-z0-9_]+', s): return False                 # 소문자 키
    if re.search(r'[a-z][A-Z]|_', s): return False                  # camelCase
    if re.search(r'(.)\1\1', s): return False                       # 반복 문자(쓰레기)
    if not re.search(r'[AEIOUYaeiouy]', s) and len(s) > 3: return False
    if s.lower() in ('roster', 'editor'): return False
    if len(s) <= 3 and not re.fullmatch(r'[A-Z][a-z]+|[A-Z][A-Z]?\.?|[0-9]+[A-Za-z]*|[A-Z][a-z]?\.', s):
        return False
    return True
def files():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'extract', 'vc', '*'))):
        h, ty = os.path.basename(f).split('.')
        if ty in TYPES: out.append((int(h, 16), ty, f))
    return out
def segments(d):
    return [(s, e, t) for s, e, t in datafiles.u16_runs(d) if is_name(t)]
def apply(d, tr):
    return datafiles.inplace(d, tr.getter('nm'), segments(d))
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    groups = {'ROST': [], 'PLAY': [], 'CRIB': []}; seen = {}
    for h, ty, f in files():
        d = open(f, 'rb').read()
        for s, e, t in segments(d):
            if t in seen: seen[t]['max'] = min(seen[t]['max'], e - s); continue
            it = {'id': None, 'en': t, 'max': e - s, 'src': ty}; seen[t] = it; groups[ty].append(it)
    N = 400
    for ty, items in groups.items():
        for k in range(0, len(items), N):
            part = items[k:k + N]
            for i, it in enumerate(part): it['id'] = i
            json.dump(part, open(os.path.join(ROOT, 'work', 'batches', 'nm_%s_%02d.json' % (ty.lower(), k // N)), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(ty, len(items), (len(items) + N - 1) // N, [x['en'] for x in items[:40]])
