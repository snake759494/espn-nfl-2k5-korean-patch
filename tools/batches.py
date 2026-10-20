"""ELF UTF-16 문자열 → 번역 묶음 work/batches/elf_NN.json [{id, en, max, ctx}]
내부 식별자(소문자 키, 밑줄, 경로, 파일명, 포맷 전용)는 제외."""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
import iso, ktext
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SKIP = re.compile(r'[_\\]|\.(?i:iff|irx|bin|elf|img|ps2|tx2|pss|mpg|wav|vag|ico|sys|cnf)\b|^[a-z0-9]+[A-Z]\w*$|^[a-z0-9]+$|^\W*$|://|^[A-Z0-9]+[0-9]+$')
def is_text(s):
    t = s.strip()
    if len(t) < 2 or not re.search(r'[A-Za-z]{2}', t): return False
    if SKIP.search(t): return False
    if re.fullmatch(r'[a-z][a-zA-Z0-9]*', t): return False          # camelCase / 소문자 키
    if re.fullmatch(r'[%\d\s.,:;/()+\-*#xXdislufpc]+', t): return False
    return True
def main():
    ents = {p: (l, s) for p, l, s, r in iso.walk()}
    el, es = ents['SLUS_209.19']
    elf = iso.read(el, es)
    S = ktext.elf_strings(elf)
    seen = {}; items = []
    for i, (o, s, mx) in enumerate(S):
        if not is_text(s): continue
        if s in seen:
            seen[s]['max'] = min(seen[s]['max'], mx); continue
        prev = S[i - 1][1] if i else ''; nxt = S[i + 1][1] if i + 1 < len(S) else ''
        it = {'id': len(items), 'en': s, 'max': mx, 'ctx': [prev[:60], nxt[:60]]}
        seen[s] = it; items.append(it)
    os.makedirs(os.path.join(ROOT, 'work', 'batches'), exist_ok=True)
    N = 250
    for k in range(0, len(items), N):
        json.dump(items[k:k + N], open(os.path.join(ROOT, 'work', 'batches', 'elf_%02d.json' % (k // N)), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=0)
    print(len(items), 'strings', sum(len(x['en']) for x in items), 'chars', (len(items) + N - 1) // N, 'batches')
if __name__ == '__main__': main()
