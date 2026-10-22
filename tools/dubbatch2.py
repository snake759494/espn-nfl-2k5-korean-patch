"""2차 받아쓰기(work/asr2_comm_*.jsonl, 1차에서 비워 둔 클립을 다시 받아쓴 것)로 번역 묶음을 만든다.
work/dub_batches/dub_r2_NNN.json [{id, en, en1(1차 받아쓰기), dur, max, prev, next}] — 이미 번역된 클립 수 순서대로 N개씩.
번역 결과는 translation/dub/dub_r2_NNN.json (dub_*.json 이라 해설 대본으로 함께 읽히고, 이름순으로 뒤라 1차 빈칸을 덮어씀)."""
import os, json, glob
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
N = 600
def main(flush=False):
    r1 = {}; r2 = {}
    for fp in glob.glob(os.path.join(ROOT, 'work', 'asr_comm_[0-9].jsonl')):
        for l in open(fp, encoding='utf-8'): r = json.loads(l); r1[r['i']] = r
    for fp in glob.glob(os.path.join(ROOT, 'work', 'asr2_comm_[0-9].jsonl')):
        for l in open(fp, encoding='utf-8'):
            try: r = json.loads(l); r2[r['i']] = r
            except Exception: pass
    sc = {}
    for fp in glob.glob(os.path.join(ROOT, 'translation', 'dub', 'dub_*.json')): sc.update(json.load(open(fp, encoding='utf-8')))
    od = os.path.join(ROOT, 'work', 'dub_batches')
    done = set()
    for fp in glob.glob(os.path.join(od, 'dub_r2_*.json')): done |= {x['id'] for x in json.load(open(fp, encoding='utf-8'))}
    todo = sorted(i for i in r2 if i not in done)
    ctx = lambda i: (r2.get(i) or r1.get(i) or {}).get('en', '')
    made = []; k = len(glob.glob(os.path.join(od, 'dub_r2_*.json')))
    while len(todo) >= N or (flush and todo):
        ids, todo = todo[:N], todo[N:]
        items = [{'id': i, 'en': r2[i]['en'], 'en1': r1.get(i, {}).get('en', ''), 'dur': r2[i]['dur'],
                  'max': max(3, int(r2[i]['dur'] * 5.5)), 'prev': ctx(i - 1), 'next': ctx(i + 1),
                  'prev_ko': sc.get(str(i - 1), ''), 'next_ko': sc.get(str(i + 1), '')} for i in ids]
        name = 'dub_r2_%03d' % k; k += 1
        json.dump(items, open(os.path.join(od, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        made.append(name)
    print(' '.join(made) if made else '(none)', '| asr2', len(r2), 'left', len(todo))
if __name__ == '__main__':
    import sys; main('--flush' in sys.argv)          # --flush: 마지막 남은 클립도 묶음으로
