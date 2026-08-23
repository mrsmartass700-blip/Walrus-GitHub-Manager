# -*- coding: utf-8 -*-
"""GitHub REST API client — everything sent to GitHub is in English."""
import base64
import json
import os
import requests
from requests.adapters import HTTPAdapter, Retry

API = "https://api.github.com"


class GitHubError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


class GitHubClient:
    def __init__(self, token: str = ""):
        self.token = token.strip()
        self.user = None
        # Одна сессия на всё приложение: keep-alive соединения (быстрее)
        # + автоматические повторы при сетевых сбоях (стабильнее)
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.4,
                      status_forcelist=(500, 502, 503, 504),
                      allowed_methods=("GET", "PUT", "POST", "PATCH", "DELETE"))
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16,
                              pool_maxsize=16)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # ---------- core ----------
    def _headers(self, extra=None):
        h = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if extra:
            h.update(extra)
        return h

    def _req(self, method, path, payload=None, params=None, ok=(200, 201, 202, 204)):
        url = path if path.startswith("http") else API + path
        r = self.session.request(
            method, url, headers=self._headers(),
            json=payload, params=params, timeout=(10, 30),
        )
        if r.status_code not in ok:
            try:
                msg = r.json().get("message", r.text[:200])
            except Exception:
                msg = r.text[:200]
            raise GitHubError(r.status_code, msg)
        if r.status_code == 204 or not r.text:
            return None
        return r.json()

    def get(self, path, params=None):
        return self._req("GET", path, params=params)

    def post(self, path, payload):
        return self._req("POST", path, payload)

    def patch(self, path, payload):
        return self._req("PATCH", path, payload)

    def put(self, path, payload=None):
        return self._req("PUT", path, payload)

    def delete(self, path):
        return self._req("DELETE", path)

    # ---------- auth / user ----------
    def login(self):
        self.user = self.get("/user")
        return self.user

    def update_profile(self, **fields):
        clean = {k: v for k, v in fields.items() if v is not None}
        self.user = self.patch("/user", clean)
        return self.user

    # ---------- repos ----------
    def list_repos(self, per_page=100):
        repos, page = [], 1
        while True:
            batch = self.get("/user/repos", params={
                "per_page": per_page, "page": page,
                "sort": "updated", "affiliation": "owner",
            })
            repos += batch
            if len(batch) < per_page:
                return repos
            page += 1

    def create_repo(self, **cfg):
        return self.post("/user/repos", cfg)

    def update_repo(self, owner, repo, **cfg):
        return self.patch(f"/repos/{owner}/{repo}", cfg)

    def delete_repo(self, owner, repo):
        return self.delete(f"/repos/{owner}/{repo}")

    def set_topics(self, owner, repo, topics):
        return self.put(f"/repos/{owner}/{repo}/topics", {"names": topics})

    def rename_branch(self, owner, repo, old, new):
        return self.post(f"/repos/{owner}/{repo}/branches/{old}/rename",
                         {"new_name": new})

    # ---------- traffic ----------
    def traffic_views(self, owner, repo):
        return self.get(f"/repos/{owner}/{repo}/traffic/views")

    def traffic_clones(self, owner, repo):
        return self.get(f"/repos/{owner}/{repo}/traffic/clones")

    def traffic_referrers(self, owner, repo):
        return self.get(f"/repos/{owner}/{repo}/traffic/popular/referrers")

    def traffic_paths(self, owner, repo):
        return self.get(f"/repos/{owner}/{repo}/traffic/popular/paths")

    # ---------- files ----------
    def put_file(self, owner, repo, path, content_bytes, message, branch=None):
        payload = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode(),
        }
        if branch:
            payload["branch"] = branch
        # if file exists, need sha
        try:
            existing = self.get(f"/repos/{owner}/{repo}/contents/{path}",
                                params={"ref": branch} if branch else None)
            if isinstance(existing, dict) and existing.get("sha"):
                payload["sha"] = existing["sha"]
        except GitHubError:
            pass
        return self.put(f"/repos/{owner}/{repo}/contents/{path}", payload)

    # ---------- labels ----------
    def create_label(self, owner, repo, name, color, description):
        try:
            return self.post(f"/repos/{owner}/{repo}/labels", {
                "name": name, "color": color, "description": description,
            })
        except GitHubError as e:
            if e.status == 422:  # already exists
                return None
            raise

    # ---------- readme ----------
    def get_readme(self, owner, repo):
        """Вернуть (текст, sha) README или (None, None), если его нет."""
        try:
            data = self.get(f"/repos/{owner}/{repo}/readme")
            text = base64.b64decode(data["content"]).decode("utf-8", "replace")
            return text, data["sha"]
        except GitHubError:
            return None, None

    # ---------- misc ----------
    def rate_limit(self):
        return self.get("/rate_limit")

    def notifications(self):
        return self.get("/notifications")

    def list_followers(self):
        return self.get("/user/followers", params={"per_page": 100})

    def list_gitignore_templates(self):
        return self.get("/gitignore/templates")

    def list_licenses(self):
        return [l["key"] for l in self.get("/licenses")]


# ---------- token storage ----------
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".github_manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def save_config(data: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
