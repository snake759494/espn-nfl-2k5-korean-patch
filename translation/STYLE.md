# ESPN NFL 2K5 (PS2) 한글화 번역 지침

## 입출력
- 입력 묶음(JSON 배열) 항목: `{"id": 번호, "en": 원문, "max": 최대 글자 수, "ctx": [앞 문자열, 뒤 문자열]}`
  - ctx 는 실행 파일 안에서 바로 앞뒤에 있던 문자열(참고용, 번역 대상 아님).
- 출력: `{"<id>": "번역문", ...}` JSON 객체(UTF-8, ensure_ascii=False). **모든 id를 빠짐없이** 넣는다.
- 번역하지 않고 원문 그대로 둘 항목은 원문을 그대로 넣는다(빈 문자열 금지).

## 반드시 지킬 것 (어기면 게임 오류)
1. **글자 수**: 번역문 글자 수(한글 1음절 = 1글자, 영문·숫자·기호·공백 = 1글자)가 `max` 이하. 넘으면 줄인다.
2. **화면 폭**: 한글 1음절은 영문 소문자 약 2자 폭이다. 버튼·메뉴·표 머리·짧은 라벨은 **원문 글자 수의 60% 이하**로 짧게. 문장(팝업·설명)은 자동 줄바꿈되므로 자연스럽게.
3. **서식 지정자** `%s %d %i %u %lu %02d %c %%` 등은 **개수와 순서를 그대로** 유지(순서 바꾸기 금지 — 인자 순서가 고정). 어순이 어색해도 순서는 지킨다.
   - 영어 복수 접미사를 붙이는 `%s`(예: `yard%s`, `safet%s`, `punt%s`)는 그 자리에서 **`%.0s`** 로 바꾼다(아무것도 출력하지 않고 인자만 소비). 예: `%d yard%s` → `%d야드%.0s`
4. **태그·제어 문자**: `|REG|`, `|TM|`, `|ANALOG|`, `|X|` `|O|` 같은 `|...|` 버튼/기호 태그, `|B|...|/B|`, `|U|...|/U|`, `<p>` 등 HTML 태그, `\n`(줄바꿈), `\t` 는 원문과 같은 개수로 유지(위치는 한국어 어순에 맞게 옮겨도 됨, 단 버튼 태그는 해당 동작 단어 옆에).
5. 사용 가능한 문자: 한글 완성형(가~힣), ASCII. 그 밖의 문자(한자, 자모 단독, …, ·, 전각 기호, 이모지, ~ 물결표) 금지. 말줄임은 `...`.
6. 앞뒤 공백, 맨 앞/끝 콜론(`:`) 등 원문 서식은 유지.

## 번역하지 않는 것 (원문 그대로)
- 내부 키·식별자로 보이는 것: 공백 없는 영문 코드, 파일명, 대문자+숫자 조합(BOOT2), 디버그·개발용 문자열(`[%4lu] %s DATA...`, 메모리·주소 출력, 테스트 문자열), 의미 없는 더미.
- 사람 이름(선수·코치·해설자·실존 인물), 팀 별칭(49ers, Bears, Rams…), 도시명, 경기장명, 방송사·회사·상표(ESPN, SEGA, NFL, Sports Center, SportsCenter, NFL Films, Visual Concepts, PlayStation, DUALSHOCK, memory card 등은 아래 용어집 참고).
- 통계·포지션 약어(표 머리): QB HB FB WR TE LT LG C RG RT DE DT LB MLB OLB ILB CB SS FS K P KR PR, ATT COMP YDS TD INT FUM REC SACK AVG PCT LNG FG XP PAT TFL PD QBR RTG W L T PF PA OVR, YPC, KR PR 등 2~4자 약어는 그대로.

## 문체
- 메뉴·버튼·제목·라벨: 짧은 명사형. (QUICK GAME → 빠른 경기, Options → 옵션, Accept → 확인)
- 설명·도움말·시스템 안내: 합니다체. ("~합니다.", "~할 수 있습니다.", 질문은 "~하시겠습니까?")
- 원문이 전부 대문자면 한국어는 그냥 일반 표기(대문자 개념 없음).
- 조각 문자열(다른 문자열과 이어 붙는 경우: "Round %d: ", "Against %s, %s")은 이어 붙었을 때 자연스럽게.
- 실황 자막·뉴스 헤드라인 느낌의 문장은 간결한 기사체("~했다", 명사형 종결)도 가능.

## 용어집 (일관성)
| 영어 | 한국어 |
|---|---|
| Quick Game / Exhibition | 빠른 경기 / 시범 경기 |
| Game Modes | 게임 모드 |
| Season / Franchise | 시즌 / 프랜차이즈 |
| Tournament / Practice | 토너먼트 / 연습 |
| The Crib | 더 크립 (게임 내 '나만의 공간' 모드 이름) |
| VIP (Virtual Identity Profile) | VIP(가상 신원 프로필) |
| Features / Extras / Options / Settings | 부가 기능 / 엑스트라 / 옵션 / 설정 |
| Load / Save / Delete | 불러오기 / 저장 / 삭제 |
| Main Menu / Back / Accept / Select / Cancel / Exit / Help | 메인 메뉴 / 뒤로 / 확인 / 선택 / 취소 / 나가기 / 도움말 |
| Yes / No / OK | 예 / 아니요 / 확인 |
| Memory Card (8MB)(for PlayStation|REG|2) | 메모리 카드(8MB)(PlayStation|REG|2용) |
| analog controller (DUALSHOCK|REG|2) | 아날로그 컨트롤러(DUALSHOCK|REG|2) |
| MEMORY CARD slot 1 | MEMORY CARD 슬롯 1 |
| Online / Network | 온라인 / 네트워크 |
| Roster / Depth Chart / Lineup | 로스터 / 뎁스 차트 / 라인업 |
| Playbook / Play / Formation / Audible / Hot Route | 플레이북 / 플레이 / 포메이션 / 오디블 / 핫 루트 |
| Offense / Defense / Special Teams | 공격 / 수비 / 스페셜 팀 |
| Quarterback / Halfback / Fullback / Running Back | 쿼터백 / 하프백 / 풀백 / 러닝백 |
| Wide Receiver / Tight End / Offensive Line | 와이드 리시버 / 타이트 엔드 / 오펜시브 라인 |
| Tackle / Guard / Center | 태클 / 가드 / 센터 |
| Defensive End / Defensive Tackle / Linebacker | 디펜시브 엔드 / 디펜시브 태클 / 라인배커 |
| Cornerback / Safety / Strong Safety / Free Safety | 코너백 / 세이프티 / 스트롱 세이프티 / 프리 세이프티 |
| Kicker / Punter / Kick Returner / Punt Returner / Long Snapper | 키커 / 펀터 / 킥 리터너 / 펀트 리터너 / 롱 스내퍼 |
| Touchdown / Field Goal / Extra Point / Two-Point Conversion | 터치다운 / 필드골 / 추가 득점(PAT) / 2점 컨버전 |
| Safety (득점) | 세이프티 |
| Kickoff / Punt / Onside Kick / Fair Catch / Touchback | 킥오프 / 펀트 / 온사이드 킥 / 페어 캐치 / 터치백 |
| First Down / 3rd and 5 / Down | 퍼스트 다운 / 3rd 다운 5야드 / 다운 |
| Yards / Yard Line / End Zone / Red Zone | 야드 / 야드 라인 / 엔드존 / 레드존 |
| Pass / Run / Rush / Reception / Completion | 패스 / 러닝 / 러싱 / 리시브 / 패스 성공 |
| Interception / Fumble / Sack / Turnover | 인터셉션 / 펌블 / 색 / 턴오버 |
| Tackle (동작) / Block / Blitz / Coverage | 태클 / 블록 / 블리츠 / 커버리지 |
| Penalty / Holding / False Start / Offside / Pass Interference | 반칙 / 홀딩 / 폴스 스타트 / 오프사이드 / 패스 방해 |
| Challenge / Timeout / Two-Minute Warning | 챌린지 / 타임아웃 / 2분 경고 |
| Quarter / Half / Halftime / Overtime | 쿼터 / 하프 / 하프타임 / 연장전 |
| Snap / Huddle / Hike | 스냅 / 허들 / 스냅 |
| Coin Toss / Heads / Tails / Kick / Receive | 동전 던지기 / 앞면 / 뒷면 / 킥 / 리시브 |
| Draft / Free Agent / Trade / Contract / Salary Cap / Release / Re-sign | 드래프트 / FA / 트레이드 / 계약 / 샐러리 캡 / 방출 / 재계약 |
| Rookie / Veteran / Pro Bowl / Super Bowl / Playoffs / Wild Card | 루키 / 베테랑 / 프로볼 / 슈퍼볼 / 플레이오프 / 와일드카드 |
| Division / Conference / AFC / NFC / Standings / Schedule | 디비전 / 컨퍼런스 / AFC / NFC / 순위 / 일정 |
| Stats / Leaders / Records | 기록 / 리더 / 기록 |
| Coach / Head Coach / Coordinator / Owner / GM | 코치 / 감독 / 코디네이터 / 구단주 / 단장 |
| Injury / Injured Reserve / Questionable / Doubtful / Out | 부상 / 부상자 명단 / 출전 불투명 / 출전 의문 / 결장 |
| Ratings / Overall / Attributes / Potential | 능력치 / 종합 / 능력 / 잠재력 |
| Speed / Strength / Agility / Awareness / Stamina | 스피드 / 근력 / 민첩성 / 판단력 / 체력 |
| Difficulty / Rookie / Pro / All-Pro / Hall of Fame (난이도) | 난이도 / 루키 / 프로 / 올프로 / 명예의 전당 |
| Replay / Instant Replay / Highlight | 리플레이 / 즉시 리플레이 / 하이라이트 |
| Camera / Audio / Sound / Music / Volume / Commentary | 카메라 / 오디오 / 사운드 / 음악 / 볼륨 / 해설 |
| Weather / Rain / Snow / Wind / Clear | 날씨 / 비 / 눈 / 바람 / 맑음 |
| Home / Away / Visitor | 홈 / 원정 / 원정 |
| User / CPU / Player (사람 플레이어) | 사용자 / CPU / 플레이어 |
| Achievement / Unlock / Reward / Points | 업적 / 해금 / 보상 / 포인트 |
| Trivia | 퀴즈 |
| Mini-camp / Practice / Drill | 미니캠프 / 연습 / 훈련 |
| First and Goal | 퍼스트 앤드 골 |
