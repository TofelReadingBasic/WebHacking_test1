"""Mini Web Wargame 30 - local HTTP server.

Run:
    python server.py

Then open http://127.0.0.1:8000.
"""

from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import sys
import urllib.parse
from html import escape as esc
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import challenges
import config

SESSIONS: dict[str, dict] = {}


class Handler(BaseHTTPRequestHandler):
    server_version = "MiniWargame/1.0"

    # Keep the terminal quiet; the challenge output is in the browser.
    def log_message(self, fmt, *args):
        return

    # -- request entry points -------------------------------------------------

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def _handle(self, method: str) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        path = re.sub(r"/{2,}", "/", path) or "/"
        self.query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        self.new_sid = None
        try:
            if path == "/":
                self.render_landing()
                return
            # The documented hidden path is /c/robots/secret/. Also accept
            # common manual URL variants so editing the address still works.
            lowered = path.rstrip("/").lower()
            if lowered in ("/robots/secret", "/robots.txt/secret"):
                self.redirect("/c/robots/secret/")
                return
            # The challenge is titled "robots.txt"; accept that as a slug too.
            match = re.match(r"^/c/robots\.txt(/.*)?$", path, re.IGNORECASE)
            if match:
                suffix = match.group(1) or "/"
                target = "/c/robots/secret/" if suffix.rstrip("/") == "/secret" else "/c/robots/"
                self.redirect(target)
                return
            if path == "/robots.txt":
                self.send_text("User-agent: *\nDisallow: /c/robots/secret/\n")
                return
            if path == "/internal/flag":
                if self.headers.get("X-Internal-Token") == challenges.INTERNAL_TOKEN:
                    self.send_text(config.FLAGS[19])
                else:
                    self.send_text("forbidden", 403)
                return
            if path == "/devtools/request":
                self.send_json(
                    {
                        "method": self.command,
                        "path": self.path,
                        "client": self.client_address[0],
                        "cookies": self.cookies(),
                        "headers": list(self.headers.items()),
                    }
                )
                return
            if path.startswith("/static/"):
                self.serve_static(path)
                return
            if path == "/submit":
                self.handle_submit(method)
                return
            match = re.match(r"^/challenge/(\d+)/?$", path)
            if match:
                challenge = config.CHALLENGES_BY_ID.get(int(match.group(1)))
                if challenge:
                    self.redirect(f"/c/{challenge['slug']}/")
                else:
                    self.send_not_found(path)
                return
            match = re.match(r"^/c/([a-z0-9-]+)(/.*)?$", path, re.IGNORECASE)
            if match:
                slug = match.group(1).lower()
                rest = match.group(2) or "/"
                handler = challenges.HANDLERS.get(slug)
                if handler:
                    handler(self, rest, self.query)
                else:
                    self.send_not_found(path)
                return
            self.send_not_found(path)
        except BrokenPipeError:
            return
        except Exception as exc:  # keep the server alive on a single bad request
            try:
                self.send_html(
                    self.page("오류", f"<p>서버 오류:</p><pre>{esc(str(exc))}</pre>"),
                    500,
                )
            except Exception:
                pass

    # -- sessions and cookies -------------------------------------------------

    def cookies(self) -> dict[str, str]:
        raw = self.headers.get("Cookie", "")
        result: dict[str, str] = {}
        for part in raw.split(";"):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                result[key] = value
        return result

    def ensure_session(self) -> dict:
        if getattr(self, "session", None) is not None:
            return self.session
        current = self.cookies().get("sid")
        if current and current in SESSIONS:
            self.sid = current
            self.session = SESSIONS[current]
            return self.session
        sid = secrets.token_hex(16)
        session = {"solved": set()}
        SESSIONS[sid] = session
        self.sid = sid
        self.session = session
        self.new_sid = sid
        return session

    def read_body(self) -> str:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b""
        return raw.decode("utf-8", "replace")

    def form(self) -> dict:
        return urllib.parse.parse_qs(self.read_body(), keep_blank_values=True)

    # -- responses ------------------------------------------------------------

    def _start_response(self, status: int, content_type: str, length: int, cookies=None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        if getattr(self, "new_sid", None):
            self.send_header(
                "Set-Cookie",
                f"sid={self.new_sid}; Path=/; HttpOnly; SameSite=Lax",
            )
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def send_html(self, html: str, status: int = 200, cookies=None) -> None:
        payload = html.encode("utf-8")
        self._start_response(status, "text/html; charset=utf-8", len(payload), cookies)
        self.wfile.write(payload)

    def send_text(self, text: str, status: int = 200, cookies=None) -> None:
        payload = text.encode("utf-8")
        self._start_response(status, "text/plain; charset=utf-8", len(payload), cookies)
        self.wfile.write(payload)

    def send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def redirect(self, location: str, cookies=None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        if getattr(self, "new_sid", None):
            self.send_header(
                "Set-Cookie",
                f"sid={self.new_sid}; Path=/; HttpOnly; SameSite=Lax",
            )
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def serve_static(self, path: str) -> None:
        name = path[len("/static/"):]
        if "/" in name or "\\" in name or name in ("", ".", ".."):
            self.send_text("not found", 404)
            return
        target = config.STATIC / name
        if not target.is_file():
            self.send_text("not found", 404)
            return
        if name.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif name.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        else:
            content_type = "text/plain; charset=utf-8"
        payload = target.read_bytes()
        self._start_response(200, content_type, len(payload))
        self.wfile.write(payload)

    def send_not_found(self, path: str) -> None:
        body = (
            "<h1>404</h1>"
            "<p>요청한 주소를 찾을 수 없습니다.</p>"
            f"<pre>{esc(path)}</pre>"
            '<p><a href="/">전체 문제 목록으로 돌아가기</a></p>'
        )
        self.send_html(self.page("404", body), 404)

    # -- shared page shell ----------------------------------------------------

    def page(self, title: str, body: str) -> str:
        session = self.ensure_session()
        solved = session.get("solved", set())
        score = sum(config.CHALLENGES_BY_ID[cid]["points"] for cid in solved if cid in config.CHALLENGES_BY_ID)
        return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · Mini Web Wargame</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="/">Mini Web Wargame</a>
    <div class="topbar-actions">
      <span class="progress">해결 {len(solved)}/30 · {score}/600점</span>
      <button type="button" class="devtools-button" id="devtools-open" aria-haspopup="dialog">개발자 도구</button>
    </div>
  </header>
  <main>
{body}
  </main>
  <footer>로컬 학습용 워게임 · 실제 서비스 공격에 사용하지 마세요.</footer>
  <dialog class="devtools-dialog" id="devtools-dialog" aria-labelledby="devtools-title">
    <div class="devtools-head">
      <h2 id="devtools-title">개발자 도구</h2>
      <form method="dialog">
        <button type="submit" class="devtools-close" aria-label="닫기">&times;</button>
      </form>
    </div>
    <p>브라우저 보안 정책상 웹 페이지가 개발자 도구를 직접 열 수는 없습니다. 아래 단축키로 열거나, 현재 페이지의 HTML을 바로 확인하세요.</p>
    <table class="shortcuts">
      <thead>
        <tr><th>기능</th><th>Windows / Linux</th><th>macOS</th></tr>
      </thead>
      <tbody>
        <tr><td>개발자 도구</td><td><kbd>F12</kbd> / <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>I</kbd></td><td><kbd>Cmd</kbd>+<kbd>Option</kbd>+<kbd>I</kbd></td></tr>
        <tr><td>페이지 소스</td><td><kbd>Ctrl</kbd>+<kbd>U</kbd></td><td><kbd>Cmd</kbd>+<kbd>Option</kbd>+<kbd>U</kbd></td></tr>
        <tr><td>Console</td><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>J</kbd></td><td><kbd>Cmd</kbd>+<kbd>Option</kbd>+<kbd>J</kbd></td></tr>
        <tr><td>요소 검사</td><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>C</kbd></td><td><kbd>Cmd</kbd>+<kbd>Option</kbd>+<kbd>C</kbd></td></tr>
      </tbody>
    </table>
    <div class="devtools-actions">
      <button type="button" class="devtools-link" id="load-source">현재 페이지 소스 보기</button>
      <button type="button" class="devtools-secondary" id="load-request">쿠키 / 요청 헤더 보기</button>
      <button type="button" class="devtools-secondary" id="copy-url">현재 URL 복사</button>
    </div>
    <pre id="devtools-source" class="devtools-source" hidden></pre>
    <pre id="devtools-request-info" class="devtools-source" hidden></pre>
    <p class="devtools-note">Network 탭에서 요청과 응답, Application 탭에서 쿠키와 스토리지를 확인할 수 있습니다.</p>
    <p class="devtools-note">HttpOnly 쿠키는 <code>document.cookie</code>에는 안 보이지만, 서버가 받은 Cookie 헤더에는 표시됩니다.</p>
  </dialog>
  <script src="/static/devtools.js" defer></script>
</body>
</html>"""

    # -- landing / challenge shell -------------------------------------------

    def render_landing(self) -> None:
        session = self.ensure_session()
        solved = session.get("solved", set())
        score = sum(config.CHALLENGES_BY_ID[cid]["points"] for cid in solved if cid in config.CHALLENGES_BY_ID)
        body = [
            "<h1>Mini Web Wargame</h1>",
            "<p>하 10개, 중 10개, 상 10개로 구성된 로컬 웹 해킹 워게임입니다. "
            "각 문제의 플래그를 찾아 제출하세요.</p>",
            f'<div class="progress-card"><strong>{len(solved)}/30</strong> 해결 · '
            f'<strong>{score}/600</strong>점</div>',
        ]
        labels = {"하": "하 (10)", "중": "중 (10)", "상": "상 (10)"}
        for difficulty in config.DIFFICULTIES:
            rows = []
            for challenge in config.CHALLENGES:
                if challenge["difficulty"] != difficulty:
                    continue
                done = challenge["id"] in solved
                status = '<span class="ok">해결</span>' if done else '<span class="todo">미해결</span>'
                rows.append(
                    "<tr>"
                    f'<td class="num">{challenge["id"]:02d}</td>'
                    f'<td><a href="/c/{challenge["slug"]}/">{esc(challenge["title"])}</a></td>'
                    f'<td>{challenge["points"]}점</td>'
                    f"<td>{status}</td>"
                    "</tr>"
                )
            body.append(f"<h2>{labels[difficulty]}</h2>")
            body.append(
                '<table class="levels"><thead><tr><th>#</th><th>문제</th><th>점수</th><th>상태</th></tr></thead>'
                f"<tbody>{''.join(rows)}</tbody></table>"
            )
        self.send_html(self.page("홈", "\n".join(body)))

    def render_challenge(self, cid: int, inner: str, status: int = 200, cookies=None) -> None:
        challenge = config.CHALLENGES_BY_ID[cid]
        session = self.ensure_session()
        solved = cid in session.get("solved", set())
        message = (self.query.get("msg") or [""])[0]
        banner = ""
        if solved or message == "correct":
            banner = '<div class="banner success">정답입니다. 해결 완료!</div>'
        elif message == "wrong":
            banner = '<div class="banner error">플래그가 틀렸습니다.</div>'
        diff_class = {"하": "easy", "중": "medium", "상": "hard"}[challenge["difficulty"]]
        body = f"""
<p class="breadcrumb"><a href="/">← 전체 목록</a></p>
<div class="ch-head">
  <span class="badge {diff_class}">{challenge['difficulty']}</span>
  <h1>{challenge['id']:02d}. {esc(challenge['title'])}</h1>
  <span class="points">{challenge['points']}점</span>
</div>
<p class="desc">{esc(challenge['desc'])}</p>
<details class="hint"><summary>힌트</summary><p>{esc(challenge['hint'])}</p></details>
{banner}
<section class="challenge">
{inner}
</section>
<section class="submit">
  <h2>플래그 제출</h2>
  <form method="post" action="/submit">
    <input type="hidden" name="id" value="{cid}">
    <p><label>FLAG<br><input name="flag" placeholder="FLAG{{...}}" autocomplete="off" size="50"></label></p>
    <p><button type="submit">제출</button></p>
  </form>
</section>
"""
        self.send_html(self.page(f"{challenge['id']:02d}. {challenge['title']}", body), status, cookies)

    def handle_submit(self, method: str) -> None:
        if method != "POST":
            self.send_text("method not allowed", 405)
            return
        params = self.form()
        raw_id = (params.get("id") or [""])[0]
        try:
            cid = int(raw_id)
        except ValueError:
            self.send_text("invalid challenge", 400)
            return
        challenge = config.CHALLENGES_BY_ID.get(cid)
        if not challenge:
            self.send_text("invalid challenge", 400)
            return
        submitted = (params.get("flag") or [""])[0].strip()
        session = self.ensure_session()
        if hmac.compare_digest(submitted, config.FLAGS[cid]):
            session.setdefault("solved", set()).add(cid)
            self.redirect(f"/c/{challenge['slug']}/?msg=correct")
        else:
            self.redirect(f"/c/{challenge['slug']}/?msg=wrong")


def prepare() -> None:
    """Create files/DBs, reset mutable state, and make relative paths stable."""
    os.chdir(config.BASE)
    config.prepare()
    challenges.prepare()
    SESSIONS.clear()


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("PORT", "8000"))
    except ValueError:
        port = 8000
    # Some runner environments export PORT=0. Use the documented default
    # instead of silently binding to an ephemeral port.
    if port <= 0:
        port = 8000
    prepare()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Mini Web Wargame 30: http://{host}:{server.server_address[1]}")
    print("종료하려면 Ctrl+C를 누르세요.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
