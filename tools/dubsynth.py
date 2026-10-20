"""번역된 더빙 대본(translation/dub/*.json)을 합성·인코딩해 캐시(work/dub_cache)에 쌓는다. 이미 있으면 건너뜀.
python tools/dubsynth.py [반복 간격 초] [k/m 분할]  — 간격을 주면 새 대본이 생길 때마다 계속 처리"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__)); import speech, dub
def run_once(S, k=0, m=1):
    sc = {i: t for i, t in dub.load_script().items() if i % m == k}; spk = dub.load_speaker(); n = 0; t0 = time.time()
    for i, text in sorted(sc.items()):
        dub.clip_bytes(S, i, text, dub.VOICES[spk.get(i, 'A')]); n += 1
        if n % 100 == 0: print('synth %d/%d  %.2fs/clip' % (n, len(sc), (time.time() - t0) / n), flush=True)
    return n
if __name__ == '__main__':
    S = speech.Speech()
    every = float(sys.argv[1]) if len(sys.argv) > 1 else 0
    k, m = map(int, sys.argv[2].split('/')) if len(sys.argv) > 2 else (0, 1)
    while True:
        run_once(S, k, m)
        if not every: break
        time.sleep(every)
