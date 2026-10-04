"""화면 레이아웃 리소스(MRKS·비압축 TXTR 묶음·SCNE 등)의 화면 문구 추출/적용.
문자열은 UTF-16 0 종료 칸 → 칸 안에서 제자리 교체. 내부 노드 이름은 제외."""
import os, sys, re, json, glob
sys.path.insert(0, os.path.dirname(__file__)); import datafiles, lz
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TYPES = ('MRKS', 'TXTR', 'SCNE', 'LAYT', 'SITU', 'CRIB', 'DRCT', 'SMCD', 'MMCD', 'Hilt')
NODE = re.compile(r'_|^[a-z]|[a-z][A-Z]|\d$|^(?i:lambert|polySurface|pPlane|joint|group|dummy|root|opaque|white|black|grey|gray)')
def is_display(t):
    s = t.strip()
    if len(s) < 2 or not re.search(r'[A-Za-z]{2}', s): return False
    if not re.fullmatch(r"[A-Za-z0-9 '&!?.,:;%()/#+\-|\r\n\t\"<>@*=$\[\]]+", s): return False
    if '|' not in s and ' ' in s and re.search(r'[a-z]{3}', s) and not re.search(r'_|[a-z][A-Z]', s): return True
    if '|' in s: return True                                  # 버튼 태그 포함 안내문
    if NODE.search(s): return False
    if ' ' in s or s.endswith(':'): return True               # 구문/라벨
    return False
_WL = None
def whitelist():
    """공백 없는 한 단어 라벨: 직접 고른 목록(work/batches/lay_words.json)만 번역."""
    global _WL
    if _WL is None:
        p = os.path.join(ROOT, 'work', 'batches', 'lay_words.json')
        _WL = {x['en'] for x in json.load(open(p, encoding='utf-8'))} if os.path.exists(p) else set()
    return _WL
def segments(d):
    ch, end = lz.chain(d)
    base = end if ch else 0                       # 압축 머리 + 비압축 꼬리 → 꼬리만
    wl = whitelist()
    out = []
    for s, e, t in datafiles.u16_runs(d[base:]):
        if is_display(t) or t in wl or (len(t) > 2 and t[0].islower() and (t[1:] in wl or is_display(t[1:]))):
            out.append((s + base // 2, e + base // 2, t))
    return out
def raw_files():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'extract', 'vc', '*'))):
        h, ty = os.path.basename(f).split('.')
        if ty not in TYPES: continue
        out.append((int(h, 16), f))
    return out
def apply(d, tr):
    g = tr.getter('lay', names=True)
    segs = []
    for s, e, t in segments(d):
        if g(t) is None and len(t) > 2 and t[0].islower() and (t[1].isupper() or t[1] == '|') and g(t[1:]) is not None:
            s, t = s + 1, t[1:]                    # 앞 필드 값이 글자로 붙은 경우
        segs.append((s, e, t))
    return datafiles.inplace(d, g, segs)
if __name__ == '__main__':
    import collections
    cnt = collections.Counter(); files = collections.Counter()
    for h, f in raw_files():
        d = open(f, 'rb').read()
        for s, e, t in segments(d): cnt[t] += 1; files[h] += 1
    items = []; seen = {}
    for h, f in raw_files():
        d = open(f, 'rb').read()
        for s, e, t in segments(d):
            if t in seen: seen[t]['max'] = min(seen[t]['max'], e - s); continue
            it = {'id': len(items), 'en': t, 'max': e - s}; seen[t] = it; items.append(it)
    json.dump(items, open(os.path.join(ROOT, 'work', 'batches', 'lay_00.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(files), 'files', len(items), 'unique strings')
    sys.stdout.reconfigure(encoding='utf-8')
    print([x['en'] for x in items[:200]])
