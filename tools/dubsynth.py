"""번역된 더빙 대본(translation/dub/*.json)을 합성·인코딩해 캐시(work/dub_cache)에 쌓는다. 이미 있으면 건너뜀.
python tools/dubsynth.py [반복 간격 초] [k/m 분할] [스트림 comm|misc|pa]  — 간격을 주면 새 대본이 생길 때마다 계속 처리"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__)); import speech, dub
def run_once(S, k=0, m=1, stream='comm'):
    sc = {i: t for i, t in dub.load_script(stream).items() if i % m == k}; spk = dub.load_speaker(); n = 0; t0 = time.time()
    for i, text in sorted(sc.items()):
        dub.clip_bytes(S, i, text, dub.voice_for(stream, i, spk), stream); n += 1
        if n % 100 == 0: print('synth %d/%d  %.2fs/clip' % (n, len(sc), (time.time() - t0) / n), flush=True)
    return n
if __name__ == '__main__':
    S = speech.Speech()
    every = float(sys.argv[1]) if len(sys.argv) > 1 else 0
    k, m = map(int, sys.argv[2].split('/')) if len(sys.argv) > 2 else (0, 1)
    stream = sys.argv[3] if len(sys.argv) > 3 else 'comm'
    while True:
        run_once(S, k, m, stream)
        if not every: break
        time.sleep(every)
