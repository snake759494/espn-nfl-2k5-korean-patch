"""합성 캐시에 아직 없는 대본 수(스트림별)."""
import os, sys, hashlib
sys.path.insert(0, os.path.dirname(__file__)); import dub, speech
S = speech.Speech(); spk = dub.load_speaker(); tot = 0
for st in ('comm', 'misc', 'pa'):
    n = 0
    for i, t in dub.load_script(st).items():
        v = dub.voice_for(st, i, spk); t = dub.ko_num(t); L = int(S.tables[st][1][i + 1] - S.tables[st][1][i])
        key = hashlib.md5((('%d|%s|%s|%d' % (i, t, v, L)) + ('' if st == 'comm' else '|' + st)).encode()).hexdigest()
        if not os.path.exists(os.path.join(dub.CACHE, key + '.vag')): n += 1
    print(st, n); tot += n
print('left', tot)
