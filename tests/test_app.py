# -*- coding: utf-8 -*-
"""Прогон логики приложения: UI-экраны, фишки, публикация папки через git."""
import base64
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mock_github
import api
mock_github.start(8766)
api.API = "http://127.0.0.1:8766"

import app as appmod

PASS, FAIL = [], []
def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  ✓ {name}")
    except Exception as e:
        FAIL.append((name, e))
        print(f"  ✗ {name}: {e}")

client = api.GitHubClient("ghp_faketoken")
client.login()

print("== UI: запуск и все экраны ==")
a = appmod.App()

def wait_bg(sec=3):
    end = time.time() + sec
    while time.time() < end:
        a.update()
        time.sleep(0.05)

def t_login_screen():
    a.show_login()
    a.update()
check("экран входа строится", t_login_screen)

def t_token_prefill():
    api.save_config({"token": "ghp_saved_token_123"})
    a.show_login()
    wait_bg(0.5)
    frame = [w for w in a.winfo_children()
             if isinstance(w, appmod.LoginFrame)][0]
    val = frame.token_entry.get()
    api.save_config({})
    assert val == "ghp_saved_token_123", f"в поле: '{val}'"
check("сохранённый токен подставляется при старте", t_token_prefill)

def t_paste_button():
    frame = [w for w in a.winfo_children()
             if isinstance(w, appmod.LoginFrame)][0]
    a.clipboard_clear()
    a.clipboard_append("  ghp_from_clipboard  ")
    frame._paste()
    assert frame.token_entry.get() == "ghp_from_clipboard"
check("кнопка «Вставить» из буфера обмена (+trim)", t_paste_button)

def t_eye_toggle():
    frame = [w for w in a.winfo_children()
             if isinstance(w, appmod.LoginFrame)][0]
    assert frame.token_entry.cget("show") == "•"
    frame._toggle_show()
    assert frame.token_entry.cget("show") == ""
    frame._toggle_show()
    assert frame.token_entry.cget("show") == "•"
check("глазок 👁 показать/скрыть токен", t_eye_toggle)

def t_hotkey_ru():
    # симуляция Ctrl+V на русской раскладке (keysym 'м')
    class Ev:
        state = 0x4
        keysym = "м"
        keycode = 86
        char = "м"
    frame = [w for w in a.winfo_children()
             if isinstance(w, appmod.LoginFrame)][0]
    fired = []
    Ev.widget = type("W", (), {"event_generate":
                               lambda self, ev: fired.append(ev)})()
    res = appmod._hotkey_fix(Ev)
    assert fired == ["<<Paste>>"] and res == "break"
    # английская раскладка — не вмешиваемся (иначе будет двойная вставка)
    Ev2 = type("E2", (), dict(state=0x4, keysym="v", keycode=86, char="v",
                              widget=Ev.widget))
    assert appmod._hotkey_fix(Ev2) is None
check("Ctrl+V работает на русской раскладке (без двойной вставки на EN)",
      t_hotkey_ru)

def t_main():
    a.on_login(client)
    a.update()
check("вход + главный экран (sidebar, toast)", t_main)

def t_views():
    for key in ["account", "repos", "publish", "settings"]:
        a.show_view(key)
        a.update()
        time.sleep(0.3)
        a.update()
check("все 4 вкладки строятся и переключаются", t_views)

print("== Аккаунт ==")
acc = a.views["account"]
def t_traffic():
    client.create_repo(name="traf", description="x")
    acc.load_traffic()
    wait_bg(3)
    assert acc.sc_views.value_lbl.cget("text") != "…", "трафик не загрузился"
check("кнопка «Обновить трекер» (посещения/клоны)", t_traffic)

def t_save_profile():
    acc.f_name.delete(0, "end"); acc.f_name.insert(0, "Ivan Tester")
    acc.save_profile()
    wait_bg(2)
    assert mock_github.STATE["user"]["name"] == "Ivan Tester"
check("сохранение профиля с экрана", t_save_profile)

def t_rate():
    acc.show_rate(); wait_bg(2)
    assert "4999" in acc.tools_out.cget("text")
check("кнопка «Лимиты API»", t_rate)

def t_notif():
    acc.show_notifications(); wait_bg(2)
    assert "уведомлен" in acc.tools_out.cget("text").lower()
check("кнопка «Уведомления»", t_notif)

print("== Репозитории ==")
rv = a.views["repos"]
def t_repo_list():
    rv.refresh(); wait_bg(2)
    assert len(rv.list_frame.winfo_children()) >= 1
check("список репозиториев рендерится", t_repo_list)

def t_search():
    rv.search.delete(0, "end"); rv.search.insert(0, "нет-такого")
    rv.render()
    rv.search.delete(0, "end"); rv.render()
check("поиск по репозиториям", t_search)

def t_visibility():
    r = mock_github.STATE["repos"]["traf"]
    was = r.get("private", False)
    rv.toggle_visibility({"owner": {"login": "testuser"}, "name": "traf",
                          "private": was})
    wait_bg(2)
    assert mock_github.STATE["repos"]["traf"]["private"] != was
check("смена видимости (приват/публичный)", t_visibility)

print("== Фишки (push_goodies) ==")
def t_goodies():
    mock_github.STATE["files"].clear()
    mock_github.STATE["labels"].clear()
    # тестовая картинка
    imgdir = tempfile.mkdtemp()
    img1 = os.path.join(imgdir, "screen shot.png")
    with open(img1, "wb") as f:
        f.write(b"\x89PNG fake image data")
    a.push_goodies("testuser", "traf", bug=True, feedback=True, labels=True,
                   contributing=True, coc=True, pr=True, readme=True,
                   badges=True, security=True, funding=True, changelog=True,
                   editorconfig=True, ci=True, dependabot=True,
                   codeowners=True, images=[img1], repo_desc="Great app")
    f = mock_github.STATE["files"]
    expected = [".github/ISSUE_TEMPLATE/bug_report.yml",
                ".github/ISSUE_TEMPLATE/feedback.yml",
                ".github/ISSUE_TEMPLATE/config.yml",
                "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
                ".github/PULL_REQUEST_TEMPLATE.md", "README.md",
                "SECURITY.md", ".github/FUNDING.yml", "CHANGELOG.md",
                ".editorconfig", ".github/workflows/ci.yml",
                ".github/dependabot.yml", ".github/CODEOWNERS",
                "docs/images/screen-shot.png"]
    import re
    for path in expected:
        assert path in f, f"нет {path}"
        if not path.startswith("docs/images"):
            text = base64.b64decode(f[path]["content"]).decode()
            assert not re.search(r"[а-яА-Я]", text), f"кириллица в {path}"
        assert not re.search(r"[а-яА-Я]", f[path]["message"]), "русский коммит!"
    readme = base64.b64decode(f["README.md"]["content"]).decode()
    assert "img.shields.io" in readme, "нет бейджей в README"
    assert "docs/images/screen-shot.png" in readme, "картинка не в README"
    assert "## Screenshots" in readme
    assert len(mock_github.STATE["labels"]) == 10, "не все лейблы"
check("все 15 фишек + картинка в docs/images + README (бейджи, Screenshots)",
      t_goodies)

def t_append_readme():
    # README-каркас выключен, но есть картинки → дополняем существующий
    mock_github.STATE["files"].clear()
    mock_github.STATE["files"]["README.md"] = {
        "content": base64.b64encode(b"# My repo\nHand-written docs").decode(),
        "message": "x"}
    imgdir = tempfile.mkdtemp()
    img = os.path.join(imgdir, "demo.png")
    with open(img, "wb") as fh:
        fh.write(b"png")
    a.push_goodies("testuser", "traf", images=[img], badges=True)
    readme = base64.b64decode(
        mock_github.STATE["files"]["README.md"]["content"]).decode()
    assert "Hand-written docs" in readme, "существующий README затёрт!"
    assert "docs/images/demo.png" in readme and "img.shields.io" in readme
check("картинки+бейджи ДОБАВЛЯЮТСЯ в существующий README без затирания",
      t_append_readme)

def t_goodies_dialog():
    repo = {"name": "traf", "owner": {"login": "testuser"},
            "description": "d"}
    dlg = appmod.GoodiesDialog(a, repo)
    wait_bg(0.5)
    assert len(dlg.switches) == len(appmod.GOODIES)
    assert not dlg.switches["readme"].get(), \
        "README-каркас должен быть выключен для существующего репо"
    # выбираем только security и применяем
    for k, s in dlg.switches.items():
        s.deselect()
    dlg.switches["security"].select()
    mock_github.STATE["files"].pop("SECURITY.md", None)
    dlg.apply()
    wait_bg(2)
    assert "SECURITY.md" in mock_github.STATE["files"]
check("диалог «Фишки» для существующего репо (объяснения + выбор)",
      t_goodies_dialog)

print("== Публикация локальной папки через git ==")
def t_push_local():
    tmp = tempfile.mkdtemp()
    with open(os.path.join(tmp, "main.py"), "w") as f:
        f.write("print('hello')\n")
    os.makedirs(os.path.join(tmp, "src"))
    with open(os.path.join(tmp, "src", "util.py"), "w") as f:
        f.write("x = 1\n")
    # git недоступен для push на мок-сервер (нет git-протокола),
    # поэтому проверяем ветку API-загрузки: спрячем git из PATH
    logs = []
    real_run = subprocess.run
    def no_git(cmd, *a, **k):
        if cmd and cmd[0] == "git":
            raise FileNotFoundError("git hidden for test")
        return real_run(cmd, *a, **k)
    subprocess.run = no_git
    try:
        a.push_local_folder("testuser", "traf", tmp, logs.append)
    finally:
        subprocess.run = real_run
    f = mock_github.STATE["files"]
    assert "main.py" in f and "src/util.py" in f
    assert any("Uploaded 2 files" in l for l in logs), logs
check("upload папки через API (fallback без git)", t_push_local)

def t_git_branch():
    # проверка git-ветки: init/add/commit локально (без push)
    tmp = tempfile.mkdtemp()
    with open(os.path.join(tmp, "a.txt"), "w") as f:
        f.write("hi")
    def git(*args):
        r = subprocess.run(["git"] + list(args), cwd=tmp,
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout
    git("init", "-b", "main")
    git("add", "-A")
    git("-c", "user.name=GitHub Manager",
        "-c", "user.email=manager@users.noreply.github.com",
        "commit", "-m", "Initial commit")
    out = git("log", "--oneline")
    assert "Initial commit" in out
check("git-ветка: init → add → commit (Initial commit, EN)", t_git_branch)

print("== Публикация: полный сценарий с экрана ==")
pub = a.views["publish"]
def t_publish_flow():
    a.show_view("publish"); a.update()
    pub.f_name.delete(0, "end"); pub.f_name.insert(0, "full-flow-repo")
    pub.f_desc.delete(0, "end"); pub.f_desc.insert(0, "End to end test repo")
    pub.f_topics.delete(0, "end"); pub.f_topics.insert(0, "python, test")
    pub.s_open.deselect()  # не открывать браузер
    mock_github.STATE["files"].clear()
    pub.create()
    wait_bg(5)
    assert "full-flow-repo" in mock_github.STATE["repos"], "репо не создан"
    r = mock_github.STATE["repos"]["full-flow-repo"]
    assert r["topics"] == ["python", "test"]
    assert r["default_branch"] == "main", "ветка не переименована в main"
    assert r["is_template"] is False and r["allow_auto_merge"] is False
    assert ".github/ISSUE_TEMPLATE/bug_report.yml" in mock_github.STATE["files"]
    readme = base64.b64decode(
        mock_github.STATE["files"]["README.md"]["content"]).decode()
    assert "img.shields.io" in readme, "бейджи по умолчанию не добавлены"
    log = pub.log.get("1.0", "end")
    assert "Done!" in log, log
check("кнопка «Создать и опубликовать» — весь пайплайн (13 настроек + ветка)",
      t_publish_flow)

def t_publish_validation():
    pub.f_name.delete(0, "end")
    pub.create()
    a.update()
check("валидация пустого имени", t_publish_validation)

print("== Настройки ==")
def t_theme():
    s = a.views["settings"]
    a.show_view("settings"); a.update()
    s.change_theme("☀️ Светлая"); a.update()
    import api as api_mod
    assert api_mod.load_config().get("theme") == "light", "тема не сохранена"
    s.change_theme("🌙 Тёмная"); a.update()
    assert api_mod.load_config().get("theme") == "dark"
check("темы: переключение + сохранение в конфиг", t_theme)

def t_scaling():
    s = a.views["settings"]
    s.change_scaling("110%"); a.update()
    import api as api_mod
    assert api_mod.load_config().get("scaling") == 1.1
    s.change_scaling("100%"); a.update()
check("масштаб интерфейса: применение + сохранение", t_scaling)

def t_traffic_setting():
    s = a.views["settings"]
    s.change_traffic(55)
    import api as api_mod
    assert api_mod.load_config().get("traffic_limit") == 55
    s.change_traffic(30)
check("настройка лимита трекера сохраняется", t_traffic_setting)

def t_ping():
    s = a.views["settings"]
    s.ping(); wait_bg(2)
    assert "GitHub доступен" in s.diag_lbl.cget("text")
check("кнопка «Проверить соединение»", t_ping)

def t_cfg_merge():
    import app as app_mod
    app_mod.cfg_set(theme="dark")
    app_mod.cfg_set(token="tok123")
    import api as api_mod
    c = api_mod.load_config()
    assert c.get("theme") == "dark" and c.get("token") == "tok123", \
        "cfg_set затёр другие ключи!"
    app_mod.cfg_set(token="")
check("конфиг: токен и тема не затирают друг друга", t_cfg_merge)

a.destroy()
print("\n== Итог ==")
print(f"Пройдено: {len(PASS)}, Провалено: {len(FAIL)}")
if FAIL:
    for n, e in FAIL:
        print(f"  FAIL: {n}: {e}")
    sys.exit(1)
