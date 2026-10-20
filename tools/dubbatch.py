"""받아쓰기 결과(work/asr_comm_*.jsonl)에서 연속으로 끝난 구간을 500클립씩 번역 묶음으로 만든다.
work/dub_batches/dub_NNNNN.json [{id, en, dur, max, prev, next}] — max = 한국어 음절 한도(대략 초당 5.5)
이미 만든 묶음은 건너뛴다. 출력: 새로 만든 묶음 이름"""
import os, sys, json, glob
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
N = 500
def load():
    rows = {}
    for fp in glob.glob(os.path.join(ROOT, 'work', 'asr_comm_[0-9].jsonl')):
        for l in open(fp, encoding='utf-8'):
            try: r = json.loads(l); rows[r['i']] = r
            except Exception: pass
    return rows
def main():
    rows = load(); od = os.path.join(ROOT, 'work', 'dub_batches'); os.makedirs(od, exist_ok=True)
    made = []; total = 30269
    for b in range(0, total, N):
        name = 'dub_%05d' % b
        if os.path.exists(os.path.join(od, name + '.json')): continue
        ids = range(b, min(b + N, total))
        if not all(i in rows for i in ids): break
        items = []
        for i in ids:
            r = rows[i]
            if not r['en'].strip(): continue
            items.append({'id': i, 'en': r['en'], 'dur': r['dur'], 'max': max(3, int(r['dur'] * 5.5)),
                          'prev': rows.get(i - 1, {}).get('en', ''), 'next': rows.get(i + 1, {}).get('en', '')})
        json.dump(items, open(os.path.join(od, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        made.append(name)
    print(' '.join(made) if made else '(none)', '| asr done', len(rows))
if __name__ == '__main__': main()
