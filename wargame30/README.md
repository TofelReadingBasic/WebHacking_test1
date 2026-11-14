# Mini Web Wargame 30

로컬에서 실행하는 웹 해킹 워게임입니다. 난이도 **하 10개, 중 10개, 상 10개**로 총 30개의 문제가 들어 있습니다. 각 문제의 플래그를 찾아 제출하면 진행도와 점수가 올라갑니다.

- 하: 10문제 × 10점 = 100점
- 중: 10문제 × 20점 = 200점
- 상: 10문제 × 30점 = 300점
- 총점: 600점

## 실행

Python 3.10 이상이 필요합니다. 외부 패키지는 사용하지 않습니다.

```bash
cd wargame30
python server.py
```

브라우저에서 <http://127.0.0.1:8000> 을 엽니다.

포트를 바꾸고 싶으면 `PORT` 환경 변수를 지정합니다.

```bash
# Git Bash / PowerShell
PORT=8080 python server.py

# Windows cmd
set PORT=8080
python server.py
```

서버는 기본적으로 `127.0.0.1`에만 바인딩됩니다. 종료하려면 터미널에서 `Ctrl+C`를 누릅니다.

## 진행 방식

1. 목록에서 문제를 고릅니다.
2. 문제 페이지의 힌트와 동작을 관찰합니다. 상단의 **개발자 도구** 버튼에서 단축키와 현재 페이지 HTML을 확인할 수 있습니다.
3. 플래그를 찾으면 `FLAG{...}` 형식 그대로 플래그 제출 폼에 넣습니다.
4. 정답이면 진행도와 점수가 올라갑니다. 진행 상태는 서버 메모리에 저장되므로 서버를 재시작하면 초기화됩니다.

플래그는 문제 페이지에 직접 적혀 있지 않습니다. 소스, 쿠키, 헤더, 데이터베이스, 파일, 세션, JWT, 직렬화 데이터 등을 이용해 찾아야 합니다.

## 개발자 도구

상단의 **개발자 도구** 버튼은 브라우저 개발자 도구를 직접 실행하지는 않습니다. 웹 페이지는 보안 정책상 브라우저 개발자 도구를 강제로 열 수 없기 때문입니다. 대신 Windows/Linux와 macOS 단축키, **현재 페이지 소스 보기**(HTML 원문 표시), **쿠키 / 요청 헤더 보기**, 현재 URL 복사 기능을 한곳에 모아 둡니다.

1번처럼 소스 주석을 찾는 문제는 **개발자 도구 → 현재 페이지 소스 보기**로 바로 확인할 수 있습니다. 표시된 HTML에서 `<section class="challenge">` 안의 `<!-- ... -->`를 찾아보세요.

**쿠키 / 요청 헤더 보기**는 브라우저에서 읽을 수 있는 `document.cookie`와 서버가 실제로 받은 요청 헤더를 함께 표시합니다. `HttpOnly` 세션 쿠키는 `document.cookie`에는 안 보이지만 서버가 받은 `Cookie` 헤더에는 표시됩니다.

## 문제 구성

| 난이도 | 번호 | 주제 |
|---|---|---|
| 하 | 01–10 | 소스 주석, robots.txt, 디렉터리 목록, 쿠키, Referer, hidden input, 클라이언트 JS, Base64, 경로 탐색, User-Agent |
| 중 | 11–20 | SQL Injection, UNION SQLi, Blind SQLi, 커맨드 인젝션, LFI 필터 우회, JWT alg:none, IDOR, Mass Assignment, SSRF, HTTP Parameter Pollution |
| 상 | 21–30 | SSTI, Pickle 역직렬화, JWT 약한 비밀키, XXE, Race Condition, JWT kid 경로 탐색, SQLi WAF 우회, NoSQL 연산자 주입, 다단계 체인, OAuth redirect_uri 우회 |

## 파일 구조

```text
wargame30/
├── server.py          # HTTP 서버, 세션, 랜딩 페이지, 플래그 제출
├── config.py          # 30개 문제 메타데이터, 플래그, 파일/DB 초기화
├── challenges.py      # 30개 취약 로직과 문제별 라우팅
├── test_challenges.py # 30개 문제 자동 풀이 테스트
├── ANSWERS.md         # 정답 및 풀이 (스포일러)
├── README.md
├── static/
│   ├── style.css
│   ├── devtools.js    # 소스/쿠키/헤더 확인 창 동작
│   └── wordlist.txt   # JWT 약한 비밀키 문제용 후보 목록 (자동 생성)
└── data/              # 문제용 파일과 SQLite DB (첫 실행 시 자동 생성)
```

`data/`와 `static/wordlist.txt`는 서버를 처음 실행할 때 자동으로 만들어집니다. `data/`에는 LFI·경로 탐색·커맨드 인젝션·XXE 문제가 읽는 플래그 파일과 SQL 문제용 SQLite DB가 들어 있습니다.

## 초기화

- 진행도 초기화: 서버를 재시작합니다.
- 파일/DB까지 초기화: 서버를 멈추고 `data/` 폴더를 삭제한 뒤 다시 실행합니다.
- 플래그 자체를 바꾸려면 `config.py`의 `FLAGS`를 수정합니다. 파일과 DB는 다음 실행 때 다시 생성됩니다.

## 테스트

전체 문제를 실제 HTTP 요청으로 풀어 보는 테스트가 포함되어 있습니다.

```bash
cd wargame30
python test_challenges.py
```

정상이라면 마지막에 `30/30 challenges solved`가 출력됩니다. 테스트는 별도 포트에서 임시 서버를 띄우고 종료합니다.

## 주의

이 프로젝트는 **학습용으로 의도적으로 취약하게 만든 로컬 애플리케이션**입니다. 커맨드 인젝션, SSTI, Pickle 역직렬화, XXE, Race Condition, SSRF 같은 위험한 기능이 실제로 동작합니다.

- 기본 바인딩인 `127.0.0.1`을 그대로 사용하세요.
- `HOST=0.0.0.0`으로 외부에 노출하지 마세요.
- 실제 서비스나 다른 사람의 시스템에 같은 기법을 사용하지 마세요.
- 정답이 필요하면 [ANSWERS.md](ANSWERS.md)를 여세요. 스포일러가 포함되어 있습니다.
