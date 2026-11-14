"""Challenge handlers for Mini Web Wargame 30.

Each handler receives the HTTP handler (for rendering, cookies and
sessions), the sub-path below /c/<slug>, and the query-string dict.
The server owns the HTTP plumbing; this module owns the vulnerable
behaviour and the challenge-specific pages.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import pickle
import platform
import re
import secrets
import sqlite3
import subprocess
import time
import urllib.parse
import urllib.request
from html import escape as esc
from pathlib import Path
from types import SimpleNamespace

import config

# ---------------------------------------------------------------------------
# Runtime state / secrets
# ---------------------------------------------------------------------------

INTERNAL_TOKEN = secrets.token_hex(24)
OAUTH_ADMIN_TOKEN = secrets.token_hex(24)
JWT_NONE_SECRET = secrets.token_hex(24)
WEAK_SECRET = "secret"

NOSQL_USERS: dict[str, dict] = {}
CHAIN_USERS: dict[int, dict] = {}
OAUTH_LEAKS: list[str] = []


def prepare() -> None:
    """Reset per-run mutable state. Called once by the server."""
    global NOSQL_USERS, CHAIN_USERS, OAUTH_LEAKS
    NOSQL_USERS = {
        "admin": {"password": "admin-" + secrets.token_hex(12)},
        "guest": {"password": "guest"},
    }
    CHAIN_USERS = {
        1: {
            "username": "guest",
            "password": "guest",
            "reset_token": secrets.token_hex(8),
        },
        2: {
            "username": "admin",
            "password": "admin-" + secrets.token_hex(12),
            "reset_token": secrets.token_hex(8),
        },
    }
    OAUTH_LEAKS = []


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _one(q: dict, key: str, default: str = "") -> str:
    values = q.get(key)
    return values[0] if values else default


def _pre(value: str) -> str:
    return f"<pre>{esc(str(value))}</pre>"


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _jwt_encode(payload: dict, secret: str, alg: str = "HS256", extra: dict | None = None) -> str:
    header = {"alg": alg, "typ": "JWT"}
    if extra:
        header.update(extra)
    head = _b64e(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    body = _b64e(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signing_input = f"{head}.{body}".encode("ascii")
    if alg == "none":
        signature = ""
    else:
        signature = _b64e(hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest())
    return f"{head}.{body}.{signature}"


def _jwt_decode(token: str):
    parts = token.split(".")
    if len(parts) != 3:
        return None, None, None
    try:
        header = json.loads(_b64d(parts[0]).decode("utf-8"))
        payload = json.loads(_b64d(parts[1]).decode("utf-8"))
    except Exception:
        return None, None, None
    return header, payload, parts


def _jwt_signature_ok(parts: list[str], secret: str) -> bool:
    expected = _b64e(hmac.new(secret.encode("utf-8"), f"{parts[0]}.{parts[1]}".encode("ascii"), hashlib.sha256).digest())
    return hmac.compare_digest(expected, parts[2])


def _verify_none(token: str):
    header, payload, parts = _jwt_decode(token)
    if not header or not payload:
        return None
    if header.get("alg") == "none":
        return payload
    if header.get("alg") == "HS256" and _jwt_signature_ok(parts, JWT_NONE_SECRET):
        return payload
    return None


def _verify_hs256(token: str, secret: str):
    header, payload, parts = _jwt_decode(token)
    if not header or not payload or header.get("alg") != "HS256":
        return None
    if _jwt_signature_ok(parts, secret):
        return payload
    return None


def _verify_kid(token: str):
    header, payload, parts = _jwt_decode(token)
    if not header or not payload or header.get("alg") != "HS256":
        return None
    kid = str(header.get("kid", "key1"))
    try:
        key = (config.DATA / "26" / "keys" / kid).read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if _jwt_signature_ok(parts, key):
        return payload
    return None


def _mongo_match(value, condition) -> bool:
    """A tiny, deliberately naive MongoDB-like match helper."""
    if isinstance(condition, dict):
        if "$ne" in condition:
            return value != condition["$ne"]
        if "$gt" in condition:
            return value > condition["$gt"]
        if "$regex" in condition:
            try:
                return re.search(str(condition["$regex"]), str(value)) is not None
            except re.error:
                return False
    return value == condition


def _sqlite_rows(db: str, query: str):
    conn = sqlite3.connect(config.DATA / db)
    try:
        return conn.execute(query).fetchall()
    finally:
        conn.close()


def _sqlite_one(db: str, query: str):
    conn = sqlite3.connect(config.DATA / db)
    try:
        return conn.execute(query).fetchone()
    finally:
        conn.close()


def _xxe_parse(xml: str) -> str:
    """Intentionally vulnerable: resolve SYSTEM file:// entities."""
    entities = re.findall(r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"file://([^"]+)">', xml)
    for name, path in entities:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = config.BASE / candidate
        content = candidate.read_text(encoding="utf-8", errors="replace")
        xml = xml.replace(f"&{name};", content)
    match = re.search(r"<name>(.*?)</name>", xml, re.S)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Shared forms
# ---------------------------------------------------------------------------


def _login_form(action: str = "/c/sqli-login/", username: str = "", password: str = "") -> str:
    return (
        f'<form method="post" action="{action}">'
        f'<p><label>username<br><input name="username" value="{esc(username)}"></label></p>'
        f'<p><label>password<br><input name="password" type="password" value="{esc(password)}"></label></p>'
        '<p><button type="submit">로그인</button></p>'
        "</form>"
    )


def _query_form(action: str, name: str, value: str = "", label: str = "입력") -> str:
    return (
        f'<form method="get" action="{action}">'
        f'<p><label>{esc(label)}<br><input name="{esc(name)}" value="{esc(value)}"></label></p>'
        '<p><button type="submit">보내기</button></p>'
        "</form>"
    )


# ---------------------------------------------------------------------------
# Level 1-10: easy
# ---------------------------------------------------------------------------


def ch_source(h, rest: str, q: dict) -> None:
    inner = (
        "<p>이 페이지의 HTML을 확인해 보세요.</p>\n"
        f"<!-- {config.FLAGS[1]} -->"
    )
    h.render_challenge(1, inner)


def ch_robots(h, rest: str, q: dict) -> None:
    if rest.rstrip("/") == "/secret":
        inner = _pre(config.FLAGS[2])
    else:
        inner = "<p>이 페이지는 검색엔진에게 숨겨져 있습니다.</p>"
    h.render_challenge(2, inner)


def ch_files(h, rest: str, q: dict) -> None:
    base = config.DATA / "03" / "files"
    if rest in ("", "/"):
        names = sorted(p.name for p in base.iterdir() if p.is_file())
        links = "".join(
            f'<li><a href="/c/files/{urllib.parse.quote(name)}">{esc(name)}</a></li>'
            for name in names
        )
        inner = f"<p>파일 목록:</p><ul>{links}</ul>"
    else:
        name = rest.lstrip("/")
        path = base / name
        if path.is_file():
            inner = f"<p>파일: <code>{esc(name)}</code></p>{_pre(path.read_text(encoding='utf-8'))}"
        else:
            h.send_text("not found", 404)
            return
    h.render_challenge(3, inner)


def ch_cookie(h, rest: str, q: dict) -> None:
    cookies = h.cookies()
    admin = cookies.get("admin")
    extra = None
    if admin is None:
        admin = "0"
        extra = ["admin=0; Path=/"]
    if admin == "1":
        inner = _pre(config.FLAGS[4])
    else:
        inner = (
            f"<p>현재 admin 쿠키: <code>{esc(admin)}</code></p>"
            "<p>관리자만 플래그를 볼 수 있습니다.</p>"
        )
    h.render_challenge(4, inner, cookies=extra)


def ch_referer(h, rest: str, q: dict) -> None:
    referer = h.headers.get("Referer", "")
    if "/c/referer/portal" in referer:
        inner = _pre(config.FLAGS[5])
    else:
        inner = (
            f"<p>현재 Referer: <code>{esc(referer or '(없음)')}</code></p>"
            "<p>Referer가 <code>/c/referer/portal</code>인 요청만 허용됩니다.</p>"
        )
    h.render_challenge(5, inner)


def ch_hidden(h, rest: str, q: dict) -> None:
    if h.command == "POST":
        params = h.form()
        debug = _one(params, "debug", "0")
        if debug == "1":
            inner = _pre(config.FLAGS[6])
        else:
            inner = '<p>디버그 모드가 아닙니다. (debug=0)</p>'
    else:
        inner = (
            '<form method="post" action="/c/hidden/">'
            '<p><label>이름<br><input name="name" value="guest"></label></p>'
            '<input type="hidden" name="debug" value="0">'
            '<p><button type="submit">제출</button></p>'
            "</form>"
        )
    h.render_challenge(6, inner)


def ch_js(h, rest: str, q: dict) -> None:
    inner = """
<p>비밀번호를 입력하면 플래그가 표시됩니다.</p>
<input id="pw" type="password" placeholder="password">
<button type="button" onclick="check()">확인</button>
<p id="out"></p>
<script>
const FLAG = "__FLAG__";
function check() {
  if (document.getElementById("pw").value === "letmein") {
    document.getElementById("out").textContent = FLAG;
  } else {
    document.getElementById("out").textContent = "틀렸습니다.";
  }
}
</script>
""".replace("__FLAG__", config.FLAGS[7])
    h.render_challenge(7, inner)


def ch_base64(h, rest: str, q: dict) -> None:
    cookies = h.cookies()
    role_cookie = cookies.get("role")
    extra = None
    if role_cookie is None:
        role_cookie = base64.b64encode(b"guest").decode("ascii")
        extra = [f"role={role_cookie}; Path=/"]
    try:
        role = base64.b64decode(role_cookie).decode("utf-8")
    except Exception:
        role = "(invalid base64)"
    if role == "admin":
        inner = _pre(config.FLAGS[8])
    else:
        inner = (
            f"<p>현재 role: <code>{esc(role)}</code></p>"
            f"<p>쿠키 값: <code>{esc(role_cookie)}</code></p>"
            "<p>role이 admin이면 플래그를 볼 수 있습니다.</p>"
        )
    h.render_challenge(8, inner, cookies=extra)


def ch_traversal(h, rest: str, q: dict) -> None:
    name = _one(q, "file", "about.txt")
    base = config.DATA / "09" / "files"
    path = base / name
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        h.send_text("file not found", 404)
        return
    inner = (
        f"<p>file: <code>{esc(name)}</code></p>{_pre(content)}"
        '<p><a href="/c/traversal/?file=about.txt">about.txt</a></p>'
    )
    h.render_challenge(9, inner)


def ch_ua(h, rest: str, q: dict) -> None:
    ua = h.headers.get("User-Agent", "")
    if ua == "WargameBot/1.0":
        inner = _pre(config.FLAGS[10])
    else:
        inner = (
            f"<p>현재 User-Agent: <code>{esc(ua)}</code></p>"
            "<p><code>WargameBot/1.0</code>만 접근할 수 있습니다.</p>"
        )
    h.render_challenge(10, inner)


# ---------------------------------------------------------------------------
# Level 11-20: medium
# ---------------------------------------------------------------------------


def ch_sqli_login(h, rest: str, q: dict) -> None:
    form = _login_form()
    if h.command == "POST":
        params = h.form()
        username = _one(params, "username")
        password = _one(params, "password")
        try:
            row = _sqlite_one(
                "11.db",
                f"SELECT username FROM users WHERE username='{username}' AND password='{password}'",
            )
        except Exception as exc:
            inner = f"<p>SQL error:</p>{_pre(str(exc))}{form}"
        else:
            if row and row[0] == "admin":
                inner = _pre(config.FLAGS[11])
            else:
                inner = f"<p>로그인 실패</p>{form}"
    else:
        inner = form
    h.render_challenge(11, inner)


def ch_sqli_union(h, rest: str, q: dict) -> None:
    value = _one(q, "id", "1")
    form = _query_form("/c/sqli-union/", "id", value, "상품 id")
    try:
        rows = _sqlite_rows("12.db", f"SELECT name, description FROM products WHERE id = {value}")
    except Exception as exc:
        inner = f"{form}<p>SQL error:</p>{_pre(str(exc))}"
    else:
        if rows:
            body = "".join(
                f"<tr><td>{esc(str(row[0]))}</td><td>{esc(str(row[1]))}</td></tr>" for row in rows
            )
            table = f"<table><thead><tr><th>name</th><th>description</th></tr></thead><tbody>{body}</tbody></table>"
        else:
            table = "<p>결과가 없습니다.</p>"
        inner = f"{form}{table}<p><a href='/c/sqli-union/?id=1'>id=1</a> · <a href='/c/sqli-union/?id=2'>id=2</a> · <a href='/c/sqli-union/?id=3'>id=3</a></p>"
    h.render_challenge(12, inner)


def ch_blind(h, rest: str, q: dict) -> None:
    value = _one(q, "id", "1")
    form = _query_form("/c/blind/", "id", value, "id")
    try:
        row = _sqlite_one("13.db", f"SELECT id FROM products WHERE id = {value}")
    except Exception as exc:
        inner = f"{form}<p>SQL error:</p>{_pre(str(exc))}"
    else:
        inner = f"{form}<p>{'exists' if row else 'not exists'}</p>"
    h.render_challenge(13, inner)


def ch_ping(h, rest: str, q: dict) -> None:
    host = _one(q, "host", "")
    form = _query_form("/c/ping/", "host", host, "호스트")
    inner = form
    if host:
        if platform.system() == "Windows":
            command = f"ping -n 1 -w 1000 {host}"
        else:
            command = f"ping -c 1 -W 1 {host}"
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=config.DATA / "14",
                capture_output=True,
                text=True,
                errors="replace",
                timeout=8,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired:
            output = "timeout"
        except Exception as exc:
            output = str(exc)
        inner = f"{form}<p>실행한 명령:</p>{_pre(command)}<p>출력:</p>{_pre(output)}"
    h.render_challenge(14, inner)


def ch_lfi(h, rest: str, q: dict) -> None:
    page = _one(q, "page", "home.html")
    page = page.replace("../", "")
    path = config.DATA / "15" / "pages" / page
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        h.send_text("file not found", 404)
        return
    inner = (
        f"<p>page: <code>{esc(page)}</code></p>{_pre(content)}"
        '<p><a href="/c/lfi/?page=home.html">home.html</a> · '
        '<a href="/c/lfi/?page=about.html">about.html</a></p>'
    )
    h.render_challenge(15, inner)


def ch_jwt_none(h, rest: str, q: dict) -> None:
    token = h.cookies().get("jwt_token")
    extra = None
    if not token:
        token = _jwt_encode({"user": "guest", "role": "user"}, JWT_NONE_SECRET)
        extra = [f"jwt_token={token}; Path=/"]
    payload = _verify_none(token)
    if payload and payload.get("role") == "admin":
        inner = _pre(config.FLAGS[16])
    else:
        user = payload.get("user") if payload else "invalid token"
        inner = (
            f"<p>user: <code>{esc(str(user))}</code></p>"
            f"<p>현재 JWT:</p>{_pre(token)}"
            "<p>관리자 role을 가진 토큰을 만들어 보세요.</p>"
        )
    h.render_challenge(16, inner, cookies=extra)


def ch_idor(h, rest: str, q: dict) -> None:
    users = {
        1: {"username": "guest", "email": "guest@example.test"},
        2: {"username": "admin", "email": "admin@example.test", "flag": config.FLAGS[17]},
    }
    raw = _one(q, "user", "1")
    try:
        uid = int(raw)
    except ValueError:
        uid = 1
    user = users.get(uid)
    if user and "flag" in user:
        inner = _pre(user["flag"])
    elif user:
        inner = (
            f"<p>username: <code>{esc(user['username'])}</code></p>"
            f"<p>email: <code>{esc(user['email'])}</code></p>"
        )
    else:
        inner = "<p>사용자를 찾을 수 없습니다.</p>"
    inner += '<p><a href="/c/idor/?user=1">user=1</a></p>'
    h.render_challenge(17, inner)


def ch_mass_assign(h, rest: str, q: dict) -> None:
    form = (
        '<form method="post" action="/c/mass-assign/">'
        '<p><label>username<br><input name="username" value="newuser"></label></p>'
        '<p><label>password<br><input name="password" type="password" value="pass"></label></p>'
        '<p><button type="submit">가입</button></p>'
        "</form>"
    )
    if h.command == "POST":
        params = h.form()
        data = {
            "username": _one(params, "username"),
            "password": _one(params, "password"),
            "role": "user",
        }
        data.update({key: values[0] for key, values in params.items()})
        if data.get("role") == "admin":
            inner = _pre(config.FLAGS[18])
        else:
            inner = f"<p>가입 완료:</p>{_pre(str(data))}{form}"
    else:
        inner = form
    h.render_challenge(18, inner)


def ch_ssrf(h, rest: str, q: dict) -> None:
    url = _one(q, "url", "")
    form = _query_form("/c/ssrf/", "url", url, "URL")
    port = h.server.server_port
    inner = form
    if url:
        if not url.startswith(("http://", "https://")):
            inner = f"{form}<p>http:// 또는 https:// URL만 허용됩니다.</p>"
        else:
            request = urllib.request.Request(url, headers={"X-Internal-Token": INTERNAL_TOKEN})
            try:
                with urllib.request.urlopen(request, timeout=5) as response:
                    body = response.read(4096).decode("utf-8", "replace")
            except Exception as exc:
                body = f"error: {exc}"
            inner = f"{form}<p>응답:</p>{_pre(body)}"
    inner += f"<p>내부 서비스: <code>http://127.0.0.1:{port}/internal/flag</code></p>"
    h.render_challenge(19, inner)


def ch_hpp(h, rest: str, q: dict) -> None:
    form = (
        '<form method="post" action="/c/hpp/">'
        '<p><label>username<br><input name="username" value="guest"></label></p>'
        '<input type="hidden" name="role" value="user">'
        '<p><button type="submit">로그인</button></p>'
        "</form>"
    )
    if h.command == "POST":
        params = h.form()
        roles = params.get("role", ["user"])
        waf_role = roles[0]
        actual_role = roles[-1]
        if waf_role == "admin":
            inner = "<p>WAF가 admin role을 차단했습니다.</p>"
        elif actual_role == "admin":
            inner = _pre(config.FLAGS[20])
        else:
            inner = f"<p>role: <code>{esc(actual_role)}</code></p>"
    else:
        inner = form
    h.render_challenge(20, inner)


# ---------------------------------------------------------------------------
# Level 21-30: hard
# ---------------------------------------------------------------------------


def ch_ssti(h, rest: str, q: dict) -> None:
    name = _one(q, "name", "guest")
    form = _query_form("/c/ssti/", "name", name, "name")
    try:
        rendered = re.sub(
            r"\{\{(.*?)\}\}",
            lambda match: str(eval(match.group(1), {})),
            name,
            flags=re.S,
        )
    except Exception as exc:
        rendered = f"(오류: {exc})"
    inner = f"<p>Hello, {rendered}</p>{form}"
    h.render_challenge(21, inner)


def ch_pickle(h, rest: str, q: dict) -> None:
    token = h.cookies().get("data")
    extra = None
    if not token:
        default = SimpleNamespace(username="guest", role="user")
        token = base64.b64encode(pickle.dumps(default)).decode("ascii")
        extra = [f"data={token}; Path=/"]
    try:
        obj = pickle.loads(base64.b64decode(token))
        role = getattr(obj, "role", None)
        if role == "admin":
            inner = _pre(config.FLAGS[22])
        else:
            inner = f"<p>role: <code>{esc(str(role))}</code></p>"
    except Exception as exc:
        inner = f"<p>invalid pickle:</p>{_pre(str(exc))}"
    inner += f"<p>현재 data 쿠키:</p>{_pre(token)}"
    h.render_challenge(22, inner, cookies=extra)


def ch_jwt_weak(h, rest: str, q: dict) -> None:
    token = h.cookies().get("weak_token")
    extra = None
    if not token:
        token = _jwt_encode({"user": "guest", "role": "user"}, WEAK_SECRET)
        extra = [f"weak_token={token}; Path=/"]
    payload = _verify_hs256(token, WEAK_SECRET)
    if payload and payload.get("role") == "admin":
        inner = _pre(config.FLAGS[23])
    else:
        user = payload.get("user") if payload else "invalid token"
        inner = (
            f"<p>user: <code>{esc(str(user))}</code></p>"
            f"<p>현재 JWT:</p>{_pre(token)}"
            '<p>후보 목록: <a href="/static/wordlist.txt">wordlist.txt</a></p>'
        )
    h.render_challenge(23, inner, cookies=extra)


def ch_xxe(h, rest: str, q: dict) -> None:
    default_xml = (
        '<?xml version="1.0"?>\n'
        "<root><name>guest</name></root>"
    )
    form = (
        '<form method="post" action="/c/xxe/">'
        f'<p><label>XML<br><textarea name="xml" rows="8" cols="70">{esc(default_xml)}</textarea></label></p>'
        '<p><button type="submit">파싱</button></p>'
        "</form>"
    )
    if h.command == "POST":
        raw = h.read_body()
        # The textarea sends xml=<...>; accept both a raw body and a form field.
        parsed = urllib.parse.parse_qs(raw, keep_blank_values=True)
        xml = _one(parsed, "xml", raw)
        try:
            name = _xxe_parse(xml)
            inner = f"<p>Hello, {esc(name)}</p>{form}"
        except Exception as exc:
            inner = f"<p>XML error:</p>{_pre(str(exc))}{form}"
    else:
        inner = form
    h.render_challenge(24, inner)


def ch_race(h, rest: str, q: dict) -> None:
    session = h.ensure_session()
    session.setdefault("race_balance", 0)
    session.setdefault("race_redeemed", False)
    rest = rest.rstrip("/") or "/"
    if h.command == "POST" and rest == "/redeem":
        if session.get("race_redeemed"):
            inner = "<p>이미 사용한 쿠폰입니다.</p>"
        else:
            time.sleep(0.25)
            session["race_balance"] = session.get("race_balance", 0) + 100
            session["race_redeemed"] = True
            inner = f"<p>쿠폰 사용 완료. 잔액: {session['race_balance']}</p>"
    elif h.command == "POST" and rest == "/buy":
        if session.get("race_balance", 0) >= 150:
            inner = _pre(config.FLAGS[25])
        else:
            inner = f"<p>잔액 부족: {session.get('race_balance', 0)} / 150</p>"
    else:
        inner = f"<p>현재 잔액: {session.get('race_balance', 0)}</p>"
    inner += (
        '<form method="post" action="/c/race/redeem"><p><button type="submit">쿠폰 사용 (+100)</button></p></form>'
        '<form method="post" action="/c/race/buy"><p><button type="submit">플래그 구매 (150)</button></p></form>'
    )
    h.render_challenge(25, inner)


def ch_jwt_kid(h, rest: str, q: dict) -> None:
    token = h.cookies().get("kid_token")
    extra = None
    if not token:
        key1 = (config.DATA / "26" / "keys" / "key1").read_text(encoding="utf-8").strip()
        token = _jwt_encode({"user": "guest", "role": "user"}, key1, extra={"kid": "key1"})
        extra = [f"kid_token={token}; Path=/"]
    payload = _verify_kid(token)
    if payload and payload.get("role") == "admin":
        inner = _pre(config.FLAGS[26])
    else:
        inner = (
            f"<p>현재 JWT:</p>{_pre(token)}"
            "<p>공개 테스트 키: <code>data/26/public.txt</code> = <code>public-key</code></p>"
        )
    h.render_challenge(26, inner, cookies=extra)


def ch_sqli_waf(h, rest: str, q: dict) -> None:
    value = _one(q, "id", "1")
    form = _query_form("/c/sqli-waf/", "id", value, "id")
    inner = form
    if "union" in value or " " in value:
        inner = f"{form}<p>WAF: 차단되었습니다.</p>"
    else:
        try:
            rows = _sqlite_rows("27.db", f"SELECT name, description FROM products WHERE id = {value}")
        except Exception as exc:
            inner = f"{form}<p>SQL error:</p>{_pre(str(exc))}"
        else:
            if rows:
                body = "".join(
                    f"<tr><td>{esc(str(row[0]))}</td><td>{esc(str(row[1]))}</td></tr>"
                    for row in rows
                )
                inner = f"{form}<table><tbody>{body}</tbody></table>"
            else:
                inner = f"{form}<p>결과가 없습니다.</p>"
    h.render_challenge(27, inner)


def ch_nosql(h, rest: str, q: dict) -> None:
    default_json = '{"username": "guest", "password": "guest"}'
    form = (
        '<form method="post" action="/c/nosql/">'
        f'<p><label>JSON<br><textarea name="json" rows="8" cols="70">{esc(default_json)}</textarea></label></p>'
        '<p><button type="submit">로그인</button></p>'
        "</form>"
    )
    if h.command == "POST":
        raw = h.read_body()
        parsed = urllib.parse.parse_qs(raw, keep_blank_values=True)
        data_text = _one(parsed, "json", raw)
        try:
            data = json.loads(data_text)
        except Exception as exc:
            inner = f"<p>JSON 오류:</p>{_pre(str(exc))}{form}"
        else:
            username = data.get("username") if isinstance(data, dict) else None
            password = data.get("password") if isinstance(data, dict) else None
            user = NOSQL_USERS.get(username) if isinstance(username, str) else None
            if user and _mongo_match(user["password"], password):
                inner = _pre(config.FLAGS[28])
            else:
                inner = f"<p>로그인 실패</p>{form}"
    else:
        inner = form
    h.render_challenge(28, inner)


def _chain_login_form() -> str:
    return (
        '<form method="post" action="/c/chain/">'
        '<p><label>username<br><input name="username" value="guest"></label></p>'
        '<p><label>password<br><input name="password" type="password" value="guest"></label></p>'
        '<p><button type="submit">로그인</button></p>'
        "</form>"
    )


def ch_chain(h, rest: str, q: dict) -> None:
    session = h.ensure_session()
    rest = rest.rstrip("/") or "/"

    if rest == "/" and h.command == "POST":
        params = h.form()
        username = _one(params, "username")
        password = _one(params, "password")
        for uid, user in CHAIN_USERS.items():
            if user["username"] == username and user["password"] == password:
                session["chain_user"] = uid
                h.redirect("/c/chain/")
                return
        h.render_challenge(29, f"<p>로그인 실패</p>{_chain_login_form()}")
        return

    uid = session.get("chain_user")

    if rest == "/":
        if uid and uid in CHAIN_USERS:
            user = CHAIN_USERS[uid]
            inner = (
                f"<p>로그인: <code>{esc(user['username'])}</code></p>"
                f'<p><a href="/c/chain/profile?user={uid}">내 프로필</a> · '
                '<a href="/c/chain/admin">관리자 페이지</a> · '
                '<a href="/c/chain/logout">로그아웃</a></p>'
            )
        else:
            inner = _chain_login_form()
    elif rest == "/profile":
        if not uid:
            h.redirect("/c/chain/")
            return
        raw = _one(q, "user", str(uid))
        try:
            target = int(raw)
        except ValueError:
            target = uid
        user = CHAIN_USERS.get(target)
        if not user:
            inner = "<p>사용자를 찾을 수 없습니다.</p>"
        else:
            inner = (
                f"<p>username: <code>{esc(user['username'])}</code></p>"
                f"<p>reset_token: <code>{esc(user['reset_token'])}</code></p>"
                '<form method="post" action="/c/chain/reset">'
                f'<input type="hidden" name="user" value="{target}">'
                f'<input type="hidden" name="token" value="{esc(user["reset_token"])}">'
                '<p><label>새 비밀번호<br><input name="newpass" value="newpass"></label></p>'
                '<p><button type="submit">비밀번호 재설정</button></p>'
                "</form>"
                '<p><a href="/c/chain/profile?user=1">user=1</a> · '
                '<a href="/c/chain/profile?user=2">user=2</a></p>'
            )
    elif rest == "/reset":
        if h.command != "POST":
            h.redirect("/c/chain/")
            return
        params = h.form()
        raw = _one(params, "user", "0")
        token = _one(params, "token")
        newpass = _one(params, "newpass")
        try:
            target = int(raw)
        except ValueError:
            target = 0
        user = CHAIN_USERS.get(target)
        if user and newpass and hmac.compare_digest(user["reset_token"], token):
            user["password"] = newpass
            inner = "<p>비밀번호가 변경되었습니다. 새 비밀번호로 로그인하세요.</p>"
        else:
            inner = "<p>토큰이 올바르지 않습니다.</p>"
    elif rest == "/admin":
        if uid == 2:
            inner = _pre(config.FLAGS[29])
        else:
            inner = "<p>관리자만 접근할 수 있습니다.</p>"
    elif rest == "/logout":
        session.pop("chain_user", None)
        h.redirect("/c/chain/")
        return
    else:
        h.send_text("not found", 404)
        return

    h.render_challenge(29, inner)


def ch_oauth(h, rest: str, q: dict) -> None:
    rest = rest.rstrip("/") or "/"
    port = h.server.server_port
    base = f"http://127.0.0.1:{port}"

    if rest == "/":
        inner = (
            "<p>관리자 봇에게 URL을 방문시키세요.</p>"
            '<form method="post" action="/c/oauth/report">'
            '<p><label>URL<br><input name="url" size="90" placeholder="http://127.0.0.1:..."></label></p>'
            '<p><button type="submit">봇 방문</button></p>'
            "</form>"
            '<p><a href="/c/oauth/inbox">수신함</a></p>'
        )
    elif rest == "/report":
        if h.command != "POST":
            h.redirect("/c/oauth/")
            return
        params = h.form()
        url = _one(params, "url")
        if not (url.startswith(base + "/") or url.startswith(f"http://localhost:{port}/")):
            inner = "<p>127.0.0.1 또는 localhost URL만 허용됩니다.</p>"
        else:
            try:
                request = urllib.request.Request(
                    url,
                    headers={"Cookie": f"oauth_admin={OAUTH_ADMIN_TOKEN}"},
                )
                with urllib.request.urlopen(request, timeout=8) as response:
                    body = response.read(4096).decode("utf-8", "replace")
                inner = f"<p>봇 방문 완료.</p>{_pre(body)}"
            except Exception as exc:
                inner = f"<p>봇 오류:</p>{_pre(str(exc))}"
    elif rest == "/authorize":
        if h.cookies().get("oauth_admin") != OAUTH_ADMIN_TOKEN:
            h.send_text("forbidden", 403)
            return
        redirect_uri = _one(q, "redirect_uri")
        allowed = f"{base}/c/oauth/callback"
        if not redirect_uri.startswith(allowed):
            h.send_text("invalid redirect_uri", 400)
            return
        separator = "&" if "?" in redirect_uri else "?"
        h.redirect(f"{redirect_uri}{separator}code={urllib.parse.quote(config.FLAGS[30])}")
        return
    elif rest == "/callback":
        code = _one(q, "code")
        next_url = _one(q, "next", f"{base}/c/oauth/leak")
        if next_url.startswith("/"):
            next_url = base + next_url
        separator = "&" if "?" in next_url else "?"
        h.redirect(f"{next_url}{separator}code={urllib.parse.quote(code)}")
        return
    elif rest == "/leak":
        code = _one(q, "code")
        if code:
            OAUTH_LEAKS.append(code)
        h.render_challenge(30, "<p>코드를 수신했습니다.</p>")
        return
    elif rest == "/inbox":
        if OAUTH_LEAKS:
            inner = f"<p>최근 수신한 코드:</p>{_pre(OAUTH_LEAKS[-1])}"
        else:
            inner = "<p>아직 수신된 코드가 없습니다.</p>"
    else:
        h.send_text("not found", 404)
        return

    h.render_challenge(30, inner)


# ---------------------------------------------------------------------------
# Route table
# ---------------------------------------------------------------------------

HANDLERS = {
    "source-comment": ch_source,
    "robots": ch_robots,
    "files": ch_files,
    "cookie": ch_cookie,
    "referer": ch_referer,
    "hidden": ch_hidden,
    "js": ch_js,
    "base64": ch_base64,
    "traversal": ch_traversal,
    "ua": ch_ua,
    "sqli-login": ch_sqli_login,
    "sqli-union": ch_sqli_union,
    "blind": ch_blind,
    "ping": ch_ping,
    "lfi": ch_lfi,
    "jwt-none": ch_jwt_none,
    "idor": ch_idor,
    "mass-assign": ch_mass_assign,
    "ssrf": ch_ssrf,
    "hpp": ch_hpp,
    "ssti": ch_ssti,
    "pickle": ch_pickle,
    "jwt-weak": ch_jwt_weak,
    "xxe": ch_xxe,
    "race": ch_race,
    "jwt-kid": ch_jwt_kid,
    "sqli-waf": ch_sqli_waf,
    "nosql": ch_nosql,
    "chain": ch_chain,
    "oauth": ch_oauth,
}
