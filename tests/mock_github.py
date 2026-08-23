# -*- coding: utf-8 -*-
"""Мок-сервер GitHub API для полного тестирования всех функций."""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {"repos": {}, "files": {}, "labels": {}, "user": {
    "login": "testuser", "name": "Test User", "bio": "old bio",
    "company": "", "blog": "", "location": "", "hireable": False,
    "public_repos": 1, "followers": 5,
    "created_at": "2020-01-01T00:00:00Z",
    "html_url": "https://github.com/testuser",
}}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def _send(self, code, obj=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if obj is not None:
            self.wfile.write(json.dumps(obj).encode())

    def _auth(self):
        return self.headers.get("Authorization", "").startswith("Bearer ")

    def do_GET(self):
        p = self.path.split("?")[0]
        if not self._auth():
            return self._send(401, {"message": "Requires authentication"})
        if p == "/user":
            return self._send(200, STATE["user"])
        if p == "/user/repos":
            return self._send(200, list(STATE["repos"].values()))
        if p == "/rate_limit":
            return self._send(200, {"resources": {"core": {
                "remaining": 4999, "limit": 5000, "reset": 1750000000}}})
        if p == "/notifications":
            return self._send(200, [])
        if p == "/user/followers":
            return self._send(200, [{"login": "f1"}, {"login": "f2"}])
        if p == "/gitignore/templates":
            return self._send(200, ["Python", "Node"])
        if p == "/licenses":
            return self._send(200, [{"key": "mit"}])
        m = re.match(r"^/repos/([^/]+)/([^/]+)/traffic/(views|clones)$", p)
        if m:
            key = "count"
            return self._send(200, {"count": 42, "uniques": 17, m.group(3): []})
        m = re.match(r"^/repos/([^/]+)/([^/]+)/traffic/popular/(referrers|paths)$", p)
        if m:
            return self._send(200, [])
        m = re.match(r"^/repos/([^/]+)/([^/]+)/readme$", p)
        if m:
            f = STATE["files"].get("README.md")
            if f:
                return self._send(200, {"content": f["content"],
                                        "sha": "readme-sha"})
            return self._send(404, {"message": "Not Found"})
        m = re.match(r"^/repos/([^/]+)/([^/]+)/contents/(.+)$", p)
        if m:
            f = STATE["files"].get(m.group(3))
            if f:
                return self._send(200, {"sha": "abc123", "path": m.group(3)})
            return self._send(404, {"message": "Not Found"})
        return self._send(404, {"message": f"Not Found: {p}"})

    def do_POST(self):
        p = self.path.split("?")[0]
        b = self._body()
        if p == "/user/repos":
            name = b["name"]
            repo = dict(b)
            repo.update({
                "owner": {"login": "testuser"}, "full_name": f"testuser/{name}",
                "html_url": f"https://github.com/testuser/{name}",
                "stargazers_count": 0, "forks_count": 0,
                "open_issues_count": 0, "private": b.get("private", False),
                "default_branch": "master",
            })
            STATE["repos"][name] = repo
            return self._send(201, repo)
        m = re.match(r"^/repos/([^/]+)/([^/]+)/labels$", p)
        if m:
            key = f"{m.group(2)}/{b['name']}"
            if key in STATE["labels"]:
                return self._send(422, {"message": "already_exists"})
            STATE["labels"][key] = b
            return self._send(201, b)
        m = re.match(r"^/repos/([^/]+)/([^/]+)/branches/([^/]+)/rename$", p)
        if m:
            if m.group(2) in STATE["repos"]:
                STATE["repos"][m.group(2)]["default_branch"] = b["new_name"]
            return self._send(201, {"name": b["new_name"]})
        return self._send(404, {"message": "Not Found"})

    def do_PATCH(self):
        p = self.path.split("?")[0]
        b = self._body()
        if p == "/user":
            STATE["user"].update(b)
            return self._send(200, STATE["user"])
        m = re.match(r"^/repos/([^/]+)/([^/]+)$", p)
        if m and m.group(2) in STATE["repos"]:
            STATE["repos"][m.group(2)].update(b)
            return self._send(200, STATE["repos"][m.group(2)])
        return self._send(404, {"message": "Not Found"})

    def do_PUT(self):
        p = self.path.split("?")[0]
        b = self._body()
        m = re.match(r"^/repos/([^/]+)/([^/]+)/topics$", p)
        if m:
            STATE["repos"].setdefault(m.group(2), {})["topics"] = b["names"]
            return self._send(200, {"names": b["names"]})
        m = re.match(r"^/repos/([^/]+)/([^/]+)/contents/(.+)$", p)
        if m:
            path = m.group(3)
            existed = path in STATE["files"]
            if existed and "sha" not in b:
                return self._send(409, {"message": "sha required"})
            STATE["files"][path] = {"content": b["content"],
                                    "message": b["message"]}
            return self._send(200 if existed else 201,
                              {"content": {"path": path}})
        return self._send(404, {"message": "Not Found"})

    def do_DELETE(self):
        p = self.path.split("?")[0]
        m = re.match(r"^/repos/([^/]+)/([^/]+)$", p)
        if m and m.group(2) in STATE["repos"]:
            del STATE["repos"][m.group(2)]
            return self._send(204)
        return self._send(404, {"message": "Not Found"})


def start(port=8765):
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    start()
    import time
    while True:
        time.sleep(1)
