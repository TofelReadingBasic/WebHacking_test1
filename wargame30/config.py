"""Mini Web Wargame 30 - metadata, flags, and challenge data bootstrap."""

from __future__ import annotations

import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
STATIC = BASE / "static"

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------

FLAGS: dict[int, str] = {
    1: "FLAG{view_source_comment}",
    2: "FLAG{robots_txt_leak}",
    3: "FLAG{directory_listing}",
    4: "FLAG{cookie_tampering}",
    5: "FLAG{referer_spoofing}",
    6: "FLAG{hidden_input_debug}",
    7: "FLAG{client_side_secret}",
    8: "FLAG{base64_cookie}",
    9: "FLAG{path_traversal_basic}",
    10: "FLAG{user_agent_gate}",
    11: "FLAG{sqli_login_bypass}",
    12: "FLAG{sqli_union_extract}",
    13: "FLAG{blind_boolean_sqli}",
    14: "FLAG{command_injection_ping}",
    15: "FLAG{lfi_filter_bypass}",
    16: "FLAG{jwt_none_alg}",
    17: "FLAG{idor_user_object}",
    18: "FLAG{mass_assignment_role}",
    19: "FLAG{ssrf_internal_access}",
    20: "FLAG{parameter_pollution}",
    21: "FLAG{ssti_template_injection}",
    22: "FLAG{pickle_deserialization}",
    23: "FLAG{jwt_weak_secret}",
    24: "FLAG{xxe_file_read}",
    25: "FLAG{race_condition_coupon}",
    26: "FLAG{jwt_kid_traversal}",
    27: "FLAG{sqli_waf_case_bypass}",
    28: "FLAG{nosql_operator_injection}",
    29: "FLAG{chain_idor_password_reset}",
    30: "FLAG{oauth_redirect_bypass}",
}

# ---------------------------------------------------------------------------
# Challenge catalogue
# ---------------------------------------------------------------------------

CHALLENGES: list[dict] = [
    {
        "id": 1,
        "slug": "source-comment",
        "title": "숨겨진 주석",
        "difficulty": "하",
        "points": 10,
        "desc": "페이지 화면에는 보이지 않는 곳에 플래그가 숨겨져 있습니다.",
        "hint": "브라우저에서 Ctrl+U를 누르거나 개발자도구의 Elements 탭을 확인하세요.",
    },
    {
        "id": 2,
        "slug": "robots",
        "title": "robots.txt",
        "difficulty": "하",
        "points": 10,
        "desc": "검색엔진 크롤러에게 숨긴 경로가 있습니다. 사이트 루트의 정책 파일을 확인하세요.",
        "hint": "/robots.txt를 열어 Disallow 경로를 찾아보세요.",
    },
    {
        "id": 3,
        "slug": "files",
        "title": "디렉터리 목록",
        "difficulty": "하",
        "points": 10,
        "desc": "파일 목록이 그대로 노출된 디렉터리가 있습니다.",
        "hint": "/c/files/에서 숨겨진 파일을 찾아보세요.",
    },
    {
        "id": 4,
        "slug": "cookie",
        "title": "쿠키 변조",
        "difficulty": "하",
        "points": 10,
        "desc": "관리자 여부를 쿠키 값 하나로 판단합니다.",
        "hint": "개발자도구 Application/Storage에서 admin 쿠키를 1로 바꿔 보세요.",
    },
    {
        "id": 5,
        "slug": "referer",
        "title": "Referer 검사",
        "difficulty": "하",
        "points": 10,
        "desc": "특정 페이지에서 온 요청만 플래그를 보여줍니다.",
        "hint": "curl -H 'Referer: ...' 또는 Burp Repeater로 헤더를 바꿔 보세요.",
    },
    {
        "id": 6,
        "slug": "hidden",
        "title": "숨겨진 input",
        "difficulty": "하",
        "points": 10,
        "desc": "폼에 숨겨진 디버그 값이 권한을 결정합니다.",
        "hint": "개발자도구에서 hidden input을 찾아 값을 1로 바꿔 보세요.",
    },
    {
        "id": 7,
        "slug": "js",
        "title": "클라이언트 사이드 검사",
        "difficulty": "하",
        "points": 10,
        "desc": "비밀번호 검사가 브라우저 자바스크립트에서만 이루어집니다.",
        "hint": "페이지 소스에서 script 안의 FLAG 변수를 찾아보세요.",
    },
    {
        "id": 8,
        "slug": "base64",
        "title": "Base64 쿠키",
        "difficulty": "하",
        "points": 10,
        "desc": "역할 쿠키가 Base64로 인코딩되어 있습니다.",
        "hint": "guest와 admin을 각각 Base64로 인코딩해 쿠키를 바꿔 보세요.",
    },
    {
        "id": 9,
        "slug": "traversal",
        "title": "경로 탐색",
        "difficulty": "하",
        "points": 10,
        "desc": "file 파라미터로 파일을 읽습니다. files/ 밖의 파일도 읽을 수 있는지 확인하세요.",
        "hint": "../flag.txt를 시도해 보세요.",
    },
    {
        "id": 10,
        "slug": "ua",
        "title": "User-Agent",
        "difficulty": "하",
        "points": 10,
        "desc": "특정 User-Agent만 접근할 수 있습니다.",
        "hint": "curl -A 'WargameBot/1.0'으로 요청해 보세요.",
    },
    {
        "id": 11,
        "slug": "sqli-login",
        "title": "SQL Injection 로그인",
        "difficulty": "중",
        "points": 20,
        "desc": "로그인 쿼리가 사용자 입력을 그대로 이어 붙입니다.",
        "hint": "username에 ' OR 1=1 -- 를 넣어 보세요.",
    },
    {
        "id": 12,
        "slug": "sqli-union",
        "title": "UNION SQL Injection",
        "difficulty": "중",
        "points": 20,
        "desc": "상품 조회 쿼리의 id가 그대로 들어갑니다.",
        "hint": "UNION SELECT로 secrets 테이블을 읽어 보세요. 컬럼은 2개입니다.",
    },
    {
        "id": 13,
        "slug": "blind",
        "title": "Blind SQL Injection",
        "difficulty": "중",
        "points": 20,
        "desc": "쿼리 결과는 존재 여부만 알려줍니다.",
        "hint": "substr(flag, n, 1)과 참/거짓 조건으로 한 글자씩 추출하세요.",
    },
    {
        "id": 14,
        "slug": "ping",
        "title": "커맨드 인젝션",
        "difficulty": "중",
        "points": 20,
        "desc": "ping 명령에 호스트 입력이 그대로 들어갑니다.",
        "hint": "셸 메타문자로 flag.txt를 읽어 보세요. Windows는 & type, Linux는 ; cat.",
    },
    {
        "id": 15,
        "slug": "lfi",
        "title": "LFI 필터 우회",
        "difficulty": "중",
        "points": 20,
        "desc": "page 파라미터로 pages/ 안의 파일을 읽습니다. ../ 필터를 우회해 보세요.",
        "hint": "필터는 ../를 한 번만 제거합니다. ....//를 시도해 보세요.",
    },
    {
        "id": 16,
        "slug": "jwt-none",
        "title": "JWT alg:none",
        "difficulty": "중",
        "points": 20,
        "desc": "JWT의 alg 헤더를 검증 없이 신뢰합니다.",
        "hint": "alg를 none으로 바꾸고 role을 admin으로 만든 토큰을 보내 보세요.",
    },
    {
        "id": 17,
        "slug": "idor",
        "title": "IDOR",
        "difficulty": "중",
        "points": 20,
        "desc": "user 파라미터로 다른 사용자의 프로필을 조회할 수 있습니다.",
        "hint": "user=1에서 user=2로 바꿔 보세요.",
    },
    {
        "id": 18,
        "slug": "mass-assign",
        "title": "Mass Assignment",
        "difficulty": "중",
        "points": 20,
        "desc": "가입 폼의 모든 필드가 사용자 객체에 그대로 저장됩니다.",
        "hint": "role=admin을 추가로 보내 보세요.",
    },
    {
        "id": 19,
        "slug": "ssrf",
        "title": "SSRF",
        "difficulty": "중",
        "points": 20,
        "desc": "서버가 사용자가 준 URL을 대신 요청합니다.",
        "hint": "127.0.0.1의 /internal/flag를 요청해 보세요.",
    },
    {
        "id": 20,
        "slug": "hpp",
        "title": "HTTP Parameter Pollution",
        "difficulty": "중",
        "points": 20,
        "desc": "role 파라미터를 여러 번 보낼 수 있습니다. WAF와 백엔드가 보는 값이 다릅니다.",
        "hint": "role=user&role=admin을 함께 보내 보세요.",
    },
    {
        "id": 21,
        "slug": "ssti",
        "title": "SSTI",
        "difficulty": "상",
        "points": 30,
        "desc": "name 파라미터가 템플릿으로 평가됩니다.",
        "hint": "{{7*7}}로 시작해 보세요.",
    },
    {
        "id": 22,
        "slug": "pickle",
        "title": "Pickle 역직렬화",
        "difficulty": "상",
        "points": 30,
        "desc": "data 쿠키를 pickle로 역직렬화합니다.",
        "hint": "role이 admin인 객체를 pickle로 직렬화해 Base64로 보내 보세요.",
    },
    {
        "id": 23,
        "slug": "jwt-weak",
        "title": "JWT 약한 비밀키",
        "difficulty": "상",
        "points": 30,
        "desc": "JWT가 약한 비밀키로 서명되어 있습니다.",
        "hint": "/static/wordlist.txt로 비밀키를 크래킹하세요.",
    },
    {
        "id": 24,
        "slug": "xxe",
        "title": "XXE",
        "difficulty": "상",
        "points": 30,
        "desc": "XML의 외부 엔티티가 처리됩니다.",
        "hint": "file://data/24/flag.txt를 엔티티로 불러와 보세요.",
    },
    {
        "id": 25,
        "slug": "race",
        "title": "Race Condition",
        "difficulty": "상",
        "points": 30,
        "desc": "쿠폰은 한 번만 사용할 수 있지만 동시 요청에 취약합니다.",
        "hint": "같은 세션으로 redeem을 여러 스레드에서 동시에 보내세요.",
    },
    {
        "id": 26,
        "slug": "jwt-kid",
        "title": "JWT kid 경로 탐색",
        "difficulty": "상",
        "points": 30,
        "desc": "JWT의 kid 헤더로 키 파일을 선택합니다.",
        "hint": "kid=../public.txt와 공개 키 public-key로 서명해 보세요.",
    },
    {
        "id": 27,
        "slug": "sqli-waf",
        "title": "SQLi WAF 우회",
        "difficulty": "상",
        "points": 30,
        "desc": "WAF가 소문자 union과 공백을 차단합니다.",
        "hint": "대문자 UNION과 /**/ 주석으로 우회하세요.",
    },
    {
        "id": 28,
        "slug": "nosql",
        "title": "NoSQL 연산자 주입",
        "difficulty": "상",
        "points": 30,
        "desc": "JSON 로그인이 MongoDB 스타일 연산자를 받습니다.",
        "hint": "password에 {\"$ne\": \"\"}를 넣어 보세요.",
    },
    {
        "id": 29,
        "slug": "chain",
        "title": "다단계 체인",
        "difficulty": "상",
        "points": 30,
        "desc": "게스트 로그인 → IDOR → 비밀번호 재설정 → 관리자 권한 순서로 이어집니다.",
        "hint": "프로필의 user 파라미터를 바꿔 다른 사용자의 reset_token을 확인하세요.",
    },
    {
        "id": 30,
        "slug": "oauth",
        "title": "OAuth redirect_uri 우회",
        "difficulty": "상",
        "points": 30,
        "desc": "관리자 봇이 redirect_uri를 따라갑니다. callback의 next 파라미터를 확인하세요.",
        "hint": "redirect_uri는 callback으로 시작해야 합니다. callback의 next를 leak으로 지정하세요.",
    },
]

CHALLENGES_BY_ID: dict[int, dict] = {c["id"]: c for c in CHALLENGES}
CHALLENGES_BY_SLUG: dict[str, dict] = {c["slug"]: c for c in CHALLENGES}
DIFFICULTIES = ("하", "중", "상")

# ---------------------------------------------------------------------------
# Files used by file-read / command-injection challenges
# ---------------------------------------------------------------------------

WORDS = [
    "password",
    "123456",
    "secret",
    "admin",
    "letmein",
    "qwerty",
    "wargame",
    "jwt",
    "changeme",
    "sunshine",
    "iloveyou",
    "monkey",
    "dragon",
    "master",
    "welcome",
    "login",
    "abc123",
    "football",
    "shadow",
    "superman",
]


def _write(relative: str, content: str) -> None:
    path = DATA / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def ensure_data() -> None:
    """Create the small files that the file-read challenges expose."""
    DATA.mkdir(parents=True, exist_ok=True)
    STATIC.mkdir(parents=True, exist_ok=True)

    _write(
        "03/files/readme.txt",
        "이 디렉터리는 예제 파일을 보관합니다.\n"
        "목록에 보이는 파일만 있는 것은 아닙니다.\n",
    )
    _write("03/files/hidden.txt", FLAGS[3] + "\n")

    _write("09/files/about.txt", "이 파일은 사이트 소개입니다.\n")
    _write("09/flag.txt", FLAGS[9] + "\n")

    _write("14/flag.txt", FLAGS[14] + "\n")
    _write("14/readme.txt", "ping 결과가 이 디렉터리에서 실행됩니다.\n")

    _write(
        "15/pages/home.html",
        "<h1>Home</h1>\n<p>페이지 목록 예제입니다.</p>\n"
        "<p><a href=\"about.html\">About</a></p>\n",
    )
    _write(
        "15/pages/about.html",
        "<h1>About</h1>\n<p>이 사이트는 LFI 연습용입니다.</p>\n",
    )
    _write("15/flag.txt", FLAGS[15] + "\n")

    _write("21/flag.txt", FLAGS[21] + "\n")
    _write("24/flag.txt", FLAGS[24] + "\n")

    # JWT kid: a public test key and a random private key.
    _write("26/public.txt", "public-key\n")
    key_dir = DATA / "26" / "keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / "key1").write_text("private-" + __import__("secrets").token_hex(16) + "\n", encoding="utf-8")

    (STATIC / "wordlist.txt").write_text("\n".join(WORDS) + "\n", encoding="utf-8")


def _reset_db(name: str) -> sqlite3.Connection:
    conn = sqlite3.connect(DATA / name)
    return conn


def init_dbs() -> None:
    """(Re)create the four SQLite databases used by the SQL challenges."""
    # 11: login bypass
    conn = _reset_db("11.db")
    conn.executescript(
        """
        DROP TABLE IF EXISTS users;
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", "admin-" + __import__("secrets").token_hex(16)),
    )
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("guest", "guest"),
    )
    conn.commit()
    conn.close()

    # 12: UNION SQLi
    conn = _reset_db("12.db")
    conn.executescript(
        """
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS secrets;
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
        CREATE TABLE secrets (flag TEXT NOT NULL);
        """
    )
    conn.executemany(
        "INSERT INTO products (id, name, description) VALUES (?, ?, ?)",
        [
            (1, "사과", "빨간 사과입니다."),
            (2, "바나나", "노란 바나나입니다."),
            (3, "포도", "보라색 포도입니다."),
        ],
    )
    conn.execute("INSERT INTO secrets (flag) VALUES (?)", (FLAGS[12],))
    conn.commit()
    conn.close()

    # 13: blind SQLi
    conn = _reset_db("13.db")
    conn.executescript(
        """
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS secrets;
        CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE secrets (flag TEXT NOT NULL);
        """
    )
    conn.executemany(
        "INSERT INTO products (id, name) VALUES (?, ?)",
        [(1, "사과"), (2, "바나나"), (3, "포도"), (4, "수박"), (5, "딸기")],
    )
    conn.execute("INSERT INTO secrets (flag) VALUES (?)", (FLAGS[13],))
    conn.commit()
    conn.close()

    # 27: SQLi with a deliberately flawed WAF
    conn = _reset_db("27.db")
    conn.executescript(
        """
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS secrets;
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
        CREATE TABLE secrets (flag TEXT NOT NULL);
        """
    )
    conn.executemany(
        "INSERT INTO products (id, name, description) VALUES (?, ?, ?)",
        [
            (1, "notebook", "A5 노트"),
            (2, "pen", "검정 볼펜"),
            (3, "eraser", "지우개"),
        ],
    )
    conn.execute("INSERT INTO secrets (flag) VALUES (?)", (FLAGS[27],))
    conn.commit()
    conn.close()


def prepare() -> None:
    ensure_data()
    init_dbs()
