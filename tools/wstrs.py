"""UTF-16LE 문자열 추출 (2바이트 정렬, 0 종료)."""
import re, sys
def find(d, n=3):
    out = []
    for m in re.finditer(rb'(?:[\x09\x0a\x0d\x20-\x7e]\x00){%d,}' % n, d):
        if m.start() % 2: continue
        out.append((m.start(), m.group().decode('utf-16-le')))
    return out
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for o, s in find(d, int(sys.argv[2]) if len(sys.argv) > 2 else 3):
        sys.stdout.buffer.write(('%08x %s\n' % (o, s.replace('\n', '\n'))).encode('utf-8'))
