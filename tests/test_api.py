# -*- coding: utf-8 -*-
"""Полный прогон всех функций api.py + templates + логики публикации."""
import base64
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mock_github
import api

mock_github.start(8765)
api.API = "http://127.0.0.1:8765"

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  ✓ {name}")
    except Exception as e:
        FAIL.append((name, e))
        print(f"  ✗ {name}: {e}")


c = api.GitHubClient("ghp_faketoken123")

print("== API-клиент ==")
check("login (получение пользователя)", lambda: (
    c.login(), 1/0 if c.user["login"] != "testuser" else None))

def t_bad_token():
    bad = api.GitHubClient("")
    try:
        bad.login()
        raise AssertionError("должен был отклонить пустой токен")
    except api.GitHubError as e:
        assert e.status == 401
check("отказ при неверном токене (401)", t_bad_token)

def t_profile():
    u = c.update_profile(name="New Name", bio="new bio", company="ACME",
                         blog="https://x.dev", location="Moscow", hireable=True)
    assert u["name"] == "New Name" and u["bio"] == "new bio"
    assert u["hireable"] is True
check("update_profile (настройки аккаунта)", t_profile)

def t_create_repo():
    r = c.create_repo(name="proj1", description="Test project", private=True,
                      has_issues=True, has_wiki=False, has_projects=False,
                      has_discussions=False, auto_init=True,
                      allow_squash_merge=True, allow_merge_commit=True,
                      allow_rebase_merge=False, delete_branch_on_merge=True,
                      gitignore_template="Python", license_template="mit",
                      homepage="https://proj.dev")
    assert r["name"] == "proj1" and r["private"] is True
    assert r["html_url"].endswith("/proj1")
check("create_repo (все настройки)", t_create_repo)

check("list_repos", lambda: (
    None if any(r["name"] == "proj1" for r in c.list_repos())
    else 1/0))

def t_update_repo():
    r = c.update_repo("testuser", "proj1", private=False, description="Upd")
    assert r["private"] is False and r["description"] == "Upd"
check("update_repo (смена видимости/описания)", t_update_repo)

def t_topics():
    r = c.set_topics("testuser", "proj1", ["python", "gui", "tools"])
    assert r["names"] == ["python", "gui", "tools"]
check("set_topics (топики)", t_topics)

check("traffic_views (трекер посещений)", lambda: (
    None if c.traffic_views("testuser", "proj1")["count"] == 42 else 1/0))
check("traffic_clones (трекер скачиваний)", lambda: (
    None if c.traffic_clones("testuser", "proj1")["uniques"] == 17 else 1/0))
check("traffic_referrers", lambda: c.traffic_referrers("testuser", "proj1"))
check("traffic_paths", lambda: c.traffic_paths("testuser", "proj1"))

def t_put_file():
    r = c.put_file("testuser", "proj1", "README.md",
                   "# Hello".encode(), "Add README")
    assert r["content"]["path"] == "README.md"
    # повторная запись — должен подставить sha существующего файла
    r2 = c.put_file("testuser", "proj1", "README.md",
                    "# Hello v2".encode(), "Update README")
    assert r2["content"]["path"] == "README.md"
    stored = mock_github.STATE["files"]["README.md"]
    assert base64.b64decode(stored["content"]).decode() == "# Hello v2"
check("put_file (создание + перезапись с sha)", t_put_file)

def t_labels():
    r = c.create_label("testuser", "proj1", "bug", "d73a4a", "Something broken")
    assert r["name"] == "bug"
    dup = c.create_label("testuser", "proj1", "bug", "d73a4a", "dup")
    assert dup is None  # 422 обработан тихо
check("create_label (+повтор без ошибки)", t_labels)

check("rate_limit (лимиты API)", lambda: (
    None if c.rate_limit()["resources"]["core"]["remaining"] == 4999 else 1/0))
check("notifications (уведомления)", lambda: (
    None if c.notifications() == [] else 1/0))
check("list_followers (подписчики)", lambda: (
    None if len(c.list_followers()) == 2 else 1/0))
check("gitignore templates", lambda: (
    None if "Python" in c.list_gitignore_templates() else 1/0))
check("licenses", lambda: (
    None if "mit" in c.list_licenses() else 1/0))

def t_delete():
    c.delete_repo("testuser", "proj1")
    assert not any(r["name"] == "proj1" for r in c.list_repos())
check("delete_repo (удаление)", t_delete)

print("\n== Хранение конфига ==")
def t_config():
    api.save_config({"token": "ghp_secret"})
    assert api.load_config()["token"] == "ghp_secret"
    api.save_config({})
    assert api.load_config() == {}
check("save/load config (запоминание токена)", t_config)

print("\n== Английские шаблоны (валидность) ==")
import templates_en as T

def t_yaml():
    try:
        import yaml
        yaml.safe_load(T.BUG_REPORT_YML)
        yaml.safe_load(T.FEEDBACK_YML)
        yaml.safe_load(T.ISSUE_CONFIG_YML.format(owner="o", repo="r"))
    except ImportError:
        # минимальная проверка структуры
        assert "name:" in T.BUG_REPORT_YML and "body:" in T.BUG_REPORT_YML
check("YAML-шаблоны issue-форм валидны", t_yaml)

def t_english():
    import re
    for name, text in [("bug", T.BUG_REPORT_YML), ("feedback", T.FEEDBACK_YML),
                       ("contributing", T.CONTRIBUTING_MD),
                       ("coc", T.CODE_OF_CONDUCT_MD), ("pr", T.PR_TEMPLATE_MD),
                       ("readme", T.README_TEMPLATE),
                       ("security", T.SECURITY_MD),
                       ("funding", T.FUNDING_YML),
                       ("changelog", T.CHANGELOG_MD),
                       ("editorconfig", T.EDITORCONFIG),
                       ("ci", T.CI_WORKFLOW_YML),
                       ("dependabot", T.DEPENDABOT_YML),
                       ("codeowners", T.CODEOWNERS),
                       ("badges", T.BADGES)]:
        assert not re.search(r"[а-яА-Я]", text), f"кириллица в {name}!"
    for n, _, d in T.LABELS:
        assert not re.search(r"[а-яА-Я]", n + d)
check("во ВСЕХ 14 шаблонах и лейблах НЕТ русского — только английский",
      t_english)

check("README форматируется", lambda: T.README_TEMPLATE.format(
    name="x", owner="y", description="d"))

def t_build_readme():
    txt = T.build_readme("proj", "owner1", "Cool app", badges=True,
                         image_names=["a.png", "b.png"])
    assert "img.shields.io" in txt, "нет бейджей"
    assert "docs/images/a.png" in txt and "docs/images/b.png" in txt
    assert "## Screenshots" in txt
    import re
    assert not re.search(r"[а-яА-Я]", txt)
check("build_readme: бейджи + картинки, всё на английском", t_build_readme)

def t_rename_branch():
    c.create_repo(name="br-test", description="x")
    r = c.rename_branch("testuser", "br-test", "master", "main")
    assert r["name"] == "main"
    assert mock_github.STATE["repos"]["br-test"]["default_branch"] == "main"
    c.delete_repo("testuser", "br-test")
check("rename_branch (своё имя главной ветки)", t_rename_branch)

def t_get_readme():
    mock_github.STATE["files"]["README.md"] = {
        "content": base64.b64encode(b"# Hello").decode(), "message": "x"}
    text, sha = c.get_readme("testuser", "any")
    assert text == "# Hello" and sha == "readme-sha"
    del mock_github.STATE["files"]["README.md"]
    text, sha = c.get_readme("testuser", "any")
    assert text is None and sha is None
check("get_readme (чтение существующего README)", t_get_readme)

print("\n== Итог ==")
print(f"Пройдено: {len(PASS)}, Провалено: {len(FAIL)}")
if FAIL:
    for n, e in FAIL:
        print(f"  FAIL: {n}: {e}")
    sys.exit(1)
