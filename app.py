# -*- coding: utf-8 -*-
"""
GitHub Manager — красивое минималистичное приложение для управления GitHub.
UI на русском, всё что отправляется на GitHub — строго на английском.
"""
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

from api import GitHubClient, GitHubError, load_config, save_config
import templates_en as T

# ---------------------------------------------------------------- theme ----
_cfg = load_config()
ctk.set_appearance_mode(_cfg.get("theme", "dark"))
ctk.set_default_color_theme("blue")
try:
    ctk.set_widget_scaling(float(_cfg.get("scaling", 1.0)))
except Exception:
    pass

ACCENT = "#6C8CFF"
ACCENT_HOVER = "#5A78E8"
CARD = ("#f2f3f7", "#1b1d24")
CARD2 = ("#e9eaf0", "#232633")
TEXT_DIM = ("#6b7280", "#9aa0b0")
OK_COLOR = "#3ddc84"
ERR_COLOR = "#ff6b6b"
RADIUS = 18

FONT = "Segoe UI"
APP_NAME = "Walrus GitHub"
APP_TITLE = "Walrus GitHub Manager --by. MrSmartAss"
AUTHOR_URL = "https://github.com/mrsmartass700-blip"

# --------- Каталог настроек репозитория (ключ, заголовок, вкл, объяснение) --
REPO_OPTS = [
    ("private", "🔒 Приватный репозиторий", False,
     "Код увидите только вы и приглашённые. Публичный виден всем в "
     "интернете и попадает в поиск GitHub."),
    ("issues", "⚠️ Issues (задачи)", True,
     "Раздел для баг-репортов и предложений. Без него формы Bug Report "
     "и Feedback работать не будут — рекомендуем оставить включённым."),
    ("wiki", "📖 Wiki", False,
     "Отдельные страницы документации. Полезно для больших проектов, "
     "маленьким обычно хватает README."),
    ("projects", "📋 Projects (доски)", False,
     "Kanban-доски для планирования задач, как Trello, прямо в репозитории."),
    ("discussions", "💬 Discussions (обсуждения)", False,
     "Форум сообщества: вопросы-ответы, идеи, объявления. Хорошо для "
     "проектов с активными пользователями."),
    ("autoinit", "📄 Создать README при инициализации", True,
     "GitHub сразу создаст первый коммит с README. Отключайте, только "
     "если публикуете локальную папку со своим README."),
    ("squash", "🔀 Разрешить Squash merge", True,
     "Все коммиты pull request склеиваются в один аккуратный коммит — "
     "история остаётся чистой. Самый популярный вариант."),
    ("merge", "➡️ Разрешить Merge commit", True,
     "Классическое слияние с отдельным merge-коммитом. Сохраняет полную "
     "историю ветки."),
    ("rebase", "📐 Разрешить Rebase merge", True,
     "Коммиты PR переносятся в main без merge-коммита — линейная история."),
    ("delbranch", "🧹 Удалять ветки после merge", True,
     "После слияния pull request его ветка удаляется автоматически — "
     "репозиторий не зарастает мёртвыми ветками."),
    ("is_template", "🧬 Сделать репозиторием-шаблоном", False,
     "Другие смогут нажать «Use this template» и создать свой проект "
     "на основе вашего — удобно для стартеров и бойлерплейтов."),
    ("automerge", "🤖 Разрешить авто-merge", False,
     "PR можно пометить «слить автоматически», как только пройдут все "
     "проверки CI — не нужно ждать и жать кнопку вручную."),
    ("updatebranch", "⬆️ Предлагать обновление веток PR", False,
     "GitHub будет предлагать подтянуть свежий main в устаревшие PR "
     "одной кнопкой — меньше конфликтов при слиянии."),
]

# --------- Каталог фишек (ключ, заголовок, вкл, объяснение) -----------------
GOODIES = [
    ("bug", "🐞 Шаблон Bug Report", True,
     "Красивая форма для баг-репортов: описание, шаги воспроизведения, "
     "ожидаемое поведение, версия, ОС и чек-лист. Пользователи заполняют "
     "поля вместо пустого листа — вы получаете понятные отчёты."),
    ("feedback", "💜 Шаблон Feedback / Feature Request", True,
     "Форма отзывов и предложений с выбором типа (идея, улучшение, "
     "благодарность) и оценкой проекта звёздами от 1 до 5."),
    ("labels", "🏷 Набор лейблов", True,
     "10 готовых цветных меток: bug, feedback, enhancement, needs-triage, "
     "good first issue, priority и др. Помогают сортировать задачи."),
    ("contributing", "🤝 CONTRIBUTING.md", True,
     "Инструкция для желающих помочь проекту: как форкнуть, создать "
     "ветку, оформить коммиты и открыть pull request."),
    ("coc", "📜 Code of Conduct", True,
     "Кодекс поведения сообщества. GitHub показывает его наличие в "
     "разделе Community Standards — проект выглядит серьёзнее."),
    ("pr", "🔀 Шаблон Pull Request", True,
     "При открытии PR автор видит чек-лист: тип изменений, самопроверка, "
     "тесты, документация. Дисциплинирует контрибьюторов."),
    ("readme", "📄 README-каркас", True,
     "Стартовый README: название, описание, установка, использование, "
     "ссылки на контрибьютинг и лицензию. Сюда же добавятся бейджи и "
     "загруженные картинки."),
    ("badges", "🎖 Бейджи в README", True,
     "Живые значки shields.io в шапке README: звёзды, открытые issues, "
     "лицензия, дата последнего коммита. Обновляются сами."),
    ("security", "🛡 SECURITY.md", False,
     "Политика безопасности: как приватно сообщить об уязвимости, не "
     "раскрывая её публично. GitHub покажет её в разделе Security."),
    ("funding", "💰 FUNDING.yml (кнопка Sponsor)", False,
     "Добавляет кнопку «Sponsor» в шапку репозитория со ссылкой на ваш "
     "GitHub Sponsors — способ принимать поддержку от пользователей."),
    ("changelog", "📆 CHANGELOG.md", False,
     "Журнал изменений по стандарту Keep a Changelog — пользователи "
     "видят, что нового в каждой версии."),
    ("editorconfig", "🧹 .editorconfig", False,
     "Единый стиль кода (отступы, кодировка, переводы строк) для всех "
     "редакторов и IDE автоматически — меньше «шумных» диффов."),
    ("ci", "⚙️ GitHub Actions CI", False,
     "Готовый workflow: при каждом push и PR код автоматически "
     "проверяется на ошибки компиляции. Зелёная галочка у коммитов."),
    ("dependabot", "🔄 Dependabot", False,
     "GitHub будет сам открывать PR с обновлениями зависимостей и "
     "экшенов раз в неделю — безопасность без ручной рутины."),
    ("codeowners", "👑 CODEOWNERS", False,
     "Вы автоматически назначаетесь ревьюером всех pull request — ни "
     "один PR не пройдёт мимо вас."),
]


# Потокобезопасная доставка колбеков в UI-поток:
# tkinter нельзя дёргать из фоновых потоков, поэтому фоновые задачи кладут
# результат в очередь, а главный цикл разбирает её каждые 50 мс.
UI_QUEUE: "queue.Queue" = queue.Queue()


def ui_call(fn):
    UI_QUEUE.put(fn)


def cfg_get(key, default=None):
    return load_config().get(key, default)


def cfg_set(**kw):
    """Обновить настройки, не затирая остальные ключи."""
    c = load_config()
    c.update(kw)
    save_config(c)


def resource_path(rel):
    """Путь к ресурсу и в исходниках, и внутри onefile-exe (PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# --- Буфер обмена: работает на ЛЮБОЙ раскладке (русской тоже) -----------
# На русской раскладке Ctrl+V даёт keysym 'м'/'Cyrillic_em', и tkinter
# «не видит» вставку. Ловим Ctrl+клавишу и генерируем нужное событие сами.
_VK_MAP = {86: "<<Paste>>", 67: "<<Copy>>", 88: "<<Cut>>", 65: "SELECT_ALL"}
_CYR_MAP = {
    "м": "<<Paste>>", "cyrillic_em": "<<Paste>>",
    "с": "<<Copy>>", "cyrillic_es": "<<Copy>>",
    "ч": "<<Cut>>", "cyrillic_che": "<<Cut>>",
    "ф": "SELECT_ALL", "cyrillic_ef": "SELECT_ALL",
}


def _select_all(w):
    try:
        w.select_range(0, "end")
        w.icursor("end")
    except Exception:
        try:
            w.tag_add("sel", "1.0", "end")
        except Exception:
            pass


def _hotkey_fix(event):
    if not (event.state & 0x4):  # только с Ctrl
        return
    keysym = (event.keysym or "").lower()
    if keysym in ("v", "c", "x", "a"):
        return  # английская раскладка — tkinter справится сам
    action = _CYR_MAP.get(keysym)
    if action is None and sys.platform == "win32":
        # На Windows keycode — это виртуальная клавиша, не зависит от раскладки
        action = _VK_MAP.get(event.keycode)
    if action == "SELECT_ALL":
        _select_all(event.widget)
        return "break"
    if action:
        event.widget.event_generate(action)
        return "break"


def attach_context_menu(root):
    """Правый клик по любому полю ввода → меню Вырезать/Копировать/Вставить.
    Цвета меню подстраиваются под текущую тему (тёмную/светлую)."""
    menu = tk.Menu(root, tearoff=0, font=(FONT, 11), bd=0)

    def popup(event):
        dark = ctk.get_appearance_mode() == "Dark"
        menu.configure(
            bg="#232633" if dark else "#f2f3f7",
            fg="#eeeeee" if dark else "#1a1a1a",
            activebackground=ACCENT, activeforeground="#ffffff")
        w = event.widget
        menu.entryconfigure(0, command=lambda: w.event_generate("<<Cut>>"))
        menu.entryconfigure(1, command=lambda: w.event_generate("<<Copy>>"))
        menu.entryconfigure(2, command=lambda: w.event_generate("<<Paste>>"))
        menu.entryconfigure(4, command=lambda: _select_all(w))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    menu.add_command(label="  ✂  Вырезать ")
    menu.add_command(label="  📄  Копировать ")
    menu.add_command(label="  📋  Вставить ")
    menu.add_separator()
    menu.add_command(label="  ⬚  Выделить всё ")

    for cls in ("Entry", "TEntry", "Text"):
        root.bind_class(cls, "<Button-3>", popup)
    root.bind_all("<Control-KeyPress>", _hotkey_fix)


def run_bg(fn, on_done=None, on_error=None, widget=None):
    """Запуск функции в фоне, коллбеки — в UI-потоке (через очередь)."""
    def worker():
        try:
            result = fn()
            if on_done:
                ui_call(lambda: on_done(result))
        except Exception as e:
            if on_error:
                ui_call(lambda err=e: on_error(err))
    threading.Thread(target=worker, daemon=True).start()


# ---------------------------------------------------------------- widgets --
class Card(ctk.CTkFrame):
    def __init__(self, master, **kw):
        kw.setdefault("corner_radius", RADIUS)
        kw.setdefault("fg_color", CARD)
        super().__init__(master, **kw)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text, **kw):
        kw.setdefault("font", (FONT, 20, "bold"))
        super().__init__(master, text=text, anchor="w", **kw)


class Hint(ctk.CTkLabel):
    def __init__(self, master, text, **kw):
        kw.setdefault("font", (FONT, 12))
        kw.setdefault("text_color", TEXT_DIM)
        super().__init__(master, text=text, anchor="w", justify="left", **kw)


class RoundButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("corner_radius", 14)
        kw.setdefault("height", 40)
        kw.setdefault("font", (FONT, 14, "bold"))
        kw.setdefault("fg_color", ACCENT)
        kw.setdefault("hover_color", ACCENT_HOVER)
        super().__init__(master, **kw)


class GhostButton(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("corner_radius", 14)
        kw.setdefault("height", 36)
        kw.setdefault("font", (FONT, 13))
        kw.setdefault("fg_color", "transparent")
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", ACCENT)
        kw.setdefault("text_color", (ACCENT, ACCENT))
        kw.setdefault("hover_color", CARD2)
        super().__init__(master, **kw)


class Entry(ctk.CTkEntry):
    def __init__(self, master, **kw):
        kw.setdefault("corner_radius", 12)
        kw.setdefault("height", 38)
        kw.setdefault("font", (FONT, 13))
        kw.setdefault("border_width", 0)
        kw.setdefault("fg_color", CARD2)
        super().__init__(master, **kw)


class Switch(ctk.CTkSwitch):
    def __init__(self, master, **kw):
        kw.setdefault("font", (FONT, 13))
        kw.setdefault("progress_color", ACCENT)
        super().__init__(master, **kw)


class HintSwitch(ctk.CTkFrame):
    """Переключатель с подробным объяснением под ним."""
    def __init__(self, master, text, hint, on=False, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.sw = Switch(self, text=text)
        if on:
            self.sw.select()
        self.sw.pack(anchor="w")
        Hint(self, hint, wraplength=430).pack(anchor="w", padx=(48, 0),
                                              pady=(1, 0))

    def get(self):
        return self.sw.get()

    def select(self):
        self.sw.select()

    def deselect(self):
        self.sw.deselect()


class StatCard(Card):
    def __init__(self, master, title, value="—", emoji=""):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=f"{emoji}  {title}", font=(FONT, 13),
                     text_color=TEXT_DIM, anchor="w").grid(
            row=0, column=0, sticky="ew", padx=18, pady=(14, 0))
        self.value_lbl = ctk.CTkLabel(self, text=str(value),
                                      font=(FONT, 28, "bold"), anchor="w")
        self.value_lbl.grid(row=1, column=0, sticky="ew", padx=18, pady=(2, 14))

    def set(self, value):
        self.value_lbl.configure(text=str(value))


class Toast(ctk.CTkFrame):
    """Всплывающее уведомление снизу."""
    def __init__(self, master):
        super().__init__(master, corner_radius=14, fg_color=CARD2)
        self.lbl = ctk.CTkLabel(self, text="", font=(FONT, 13), padx=18, pady=10)
        self.lbl.pack()
        self._job = None

    def show(self, text, ok=True):
        self.lbl.configure(text=("✅  " if ok else "⚠️  ") + text,
                           text_color=OK_COLOR if ok else ERR_COLOR)
        self.place(relx=0.5, rely=0.96, anchor="s")
        self.lift()
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(4000, self.place_forget)


# ---------------------------------------------------------------- login ----
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login):
        super().__init__(master, fg_color="transparent")
        self.on_login = on_login

        card = Card(self, width=460)
        card.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=40)

        ctk.CTkLabel(inner, text="🦭", font=(FONT, 52)).pack(pady=(0, 4))
        ctk.CTkLabel(inner, text="Walrus GitHub",
                     font=(FONT, 26, "bold")).pack()
        Hint(inner, "by MrSmartAss").pack()
        Hint(inner, "Управление аккаунтом и репозиториями\nв одном красивом месте"
             ).pack(pady=(4, 22))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(pady=(0, 8))
        self.token_entry = Entry(row, width=250, show="•",
                                 placeholder_text="Personal Access Token (ghp_…)")
        self.token_entry.pack(side="left")
        self.token_entry.bind("<Return>", lambda e: self._login())
        self.eye_btn = GhostButton(row, text="👁", width=40,
                                   command=self._toggle_show)
        self.eye_btn.pack(side="left", padx=(6, 0))
        GhostButton(row, text="📋 Вставить", width=44,
                    command=self._paste).pack(side="left", padx=(6, 0))

        self.remember = Switch(inner, text="Запомнить токен на этом ПК")
        self.remember.select()
        self.remember.pack(pady=(4, 14))

        self.btn = RoundButton(inner, text="Войти", width=340,
                               command=self._login)
        self.btn.pack()

        self.status = Hint(inner, "")
        self.status.pack(pady=(10, 0))

        GhostButton(inner, text="🔑 Создать токен на GitHub", width=340,
                    command=lambda: webbrowser.open(
                        "https://github.com/settings/tokens/new"
                        "?scopes=repo,user,delete_repo&description=GitHub%20Manager")
                    ).pack(pady=(12, 0))
        Hint(inner, "Нужны права: repo, user (и delete_repo — по желанию)\n"
                    "Вставка: Ctrl+V (любая раскладка), правый клик или кнопка 📋"
             ).pack(pady=(6, 0))

        # Надёжное автозаполнение сохранённого токена (после отрисовки поля,
        # иначе CTkEntry с placeholder может «съесть» вставленный текст)
        self.after(150, self._prefill)

    def _prefill(self):
        cfg = load_config()
        token = cfg.get("token")
        if token:
            self.token_entry.focus_set()
            self.token_entry.delete(0, "end")
            self.token_entry.insert(0, token)
            if cfg.get("autologin"):
                self.status.configure(text="Автовход…", text_color=OK_COLOR)
                self._login()
            else:
                self.status.configure(text="Токен загружен — нажмите «Войти»",
                                      text_color=OK_COLOR)
        else:
            self.token_entry.focus_set()

    def _toggle_show(self):
        showing = self.token_entry.cget("show") == ""
        self.token_entry.configure(show="•" if showing else "")
        self.eye_btn.configure(text="👁" if showing else "🙈")

    def _paste(self):
        try:
            text = self.clipboard_get().strip()
        except Exception:
            self.status.configure(text="Буфер обмена пуст",
                                  text_color=ERR_COLOR)
            return
        self.token_entry.delete(0, "end")
        self.token_entry.insert(0, text)
        self.status.configure(text="Токен вставлен ✓", text_color=OK_COLOR)

    def _login(self):
        token = self.token_entry.get().strip()
        if not token:
            self.status.configure(text="Введите токен", text_color=ERR_COLOR)
            return
        self.btn.configure(state="disabled", text="Проверяю…")
        client = GitHubClient(token)

        def done(user):
            if self.remember.get():
                cfg_set(token=token)
            self.on_login(client)

        def err(e):
            self.btn.configure(state="normal", text="Войти")
            self.status.configure(text=f"Ошибка: {e}", text_color=ERR_COLOR)

        run_bg(client.login, done, err, self)


# ------------------------------------------------------------- account -----
class AccountView(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self._built = False

    def build(self):
        if self._built:
            return
        self._built = True
        u = self.app.client.user

        # --- шапка профиля ---
        head = Card(self)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text="👤", font=(FONT, 40)).grid(
            row=0, column=0, rowspan=2, padx=(22, 14), pady=18)
        ctk.CTkLabel(head, text=u.get("name") or u["login"],
                     font=(FONT, 22, "bold"), anchor="w").grid(
            row=0, column=1, sticky="sw", pady=(18, 0))
        Hint(head, f"@{u['login']}  ·  на GitHub с "
             f"{u['created_at'][:10]}").grid(row=1, column=1, sticky="nw",
                                             pady=(0, 18))
        GhostButton(head, text="Открыть профиль ↗",
                    command=lambda: webbrowser.open(u["html_url"])).grid(
            row=0, column=2, rowspan=2, padx=22)

        # --- статистика ---
        SectionTitle(self, "📊 Статистика и трекер").grid(
            row=1, column=0, sticky="ew", pady=(4, 10))
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew")
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1, uniform="s")

        self.sc_repos = StatCard(stats, "Репозитории", u["public_repos"], "📦")
        self.sc_followers = StatCard(stats, "Подписчики", u["followers"], "❤️")
        self.sc_stars = StatCard(stats, "Звёзды (всего)", "…", "⭐")
        self.sc_forks = StatCard(stats, "Форки (всего)", "…", "🍴")
        for i, c in enumerate([self.sc_repos, self.sc_followers,
                               self.sc_stars, self.sc_forks]):
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))

        traffic = ctk.CTkFrame(self, fg_color="transparent")
        traffic.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        for i in range(4):
            traffic.grid_columnconfigure(i, weight=1, uniform="t")
        self.sc_views = StatCard(traffic, "Посещения (14 дн)", "…", "👀")
        self.sc_uviews = StatCard(traffic, "Уник. посетители", "…", "🧑‍💻")
        self.sc_clones = StatCard(traffic, "Скачивания (клоны)", "…", "⬇️")
        self.sc_uclones = StatCard(traffic, "Уник. клонеры", "…", "🧲")
        for i, c in enumerate([self.sc_views, self.sc_uviews,
                               self.sc_clones, self.sc_uclones]):
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        RoundButton(row, text="🔄 Обновить трекер",
                    command=self.load_traffic).pack(side="left")
        Hint(row, "  Данные трафика GitHub отдаёт за последние 14 дней"
             ).pack(side="left")

        self.traffic_detail = Card(self)
        self.traffic_detail.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        self.traffic_box = ctk.CTkTextbox(
            self.traffic_detail, height=150, corner_radius=14,
            fg_color=CARD2, font=("Consolas", 12), wrap="none")
        self.traffic_box.pack(fill="both", expand=True, padx=14, pady=14)
        self.traffic_box.insert("1.0", "Нажмите «Обновить трекер», чтобы увидеть "
                                       "посещения и клоны по каждому репозиторию…")
        self.traffic_box.configure(state="disabled")

        # --- настройки профиля ---
        SectionTitle(self, "⚙️ Настройки аккаунта").grid(
            row=6, column=0, sticky="ew", pady=(22, 10))
        pcard = Card(self)
        pcard.grid(row=7, column=0, sticky="ew")
        pcard.grid_columnconfigure((1, 3), weight=1)

        def field(label, key, r, c):
            ctk.CTkLabel(pcard, text=label, font=(FONT, 13),
                         anchor="w").grid(row=r, column=c, sticky="w",
                                          padx=(22, 8), pady=8)
            e = Entry(pcard)
            e.grid(row=r, column=c + 1, sticky="ew", padx=(0, 22), pady=8)
            if u.get(key):
                e.insert(0, u[key])
            return e

        self.f_name = field("Имя", "name", 0, 0)
        self.f_company = field("Компания", "company", 0, 2)
        self.f_blog = field("Сайт / блог", "blog", 1, 0)
        self.f_location = field("Локация", "location", 1, 2)
        ctk.CTkLabel(pcard, text="Bio", font=(FONT, 13), anchor="w").grid(
            row=2, column=0, sticky="nw", padx=(22, 8), pady=8)
        self.f_bio = ctk.CTkTextbox(pcard, height=70, corner_radius=12,
                                    fg_color=CARD2, font=(FONT, 13))
        self.f_bio.grid(row=2, column=1, columnspan=3, sticky="ew",
                        padx=(0, 22), pady=8)
        if u.get("bio"):
            self.f_bio.insert("1.0", u["bio"])
        self.f_hireable = Switch(pcard, text="Открыт к предложениям работы (hireable)")
        if u.get("hireable"):
            self.f_hireable.select()
        self.f_hireable.grid(row=3, column=0, columnspan=2, sticky="w",
                             padx=22, pady=(4, 14))
        RoundButton(pcard, text="💾 Сохранить профиль",
                    command=self.save_profile).grid(
            row=3, column=3, sticky="e", padx=22, pady=(4, 14))

        # --- полезные функции ---
        SectionTitle(self, "🧰 Полезное").grid(row=8, column=0, sticky="ew",
                                               pady=(22, 10))
        tools = Card(self)
        tools.grid(row=9, column=0, sticky="ew", pady=(0, 20))
        trow = ctk.CTkFrame(tools, fg_color="transparent")
        trow.pack(fill="x", padx=16, pady=14)
        GhostButton(trow, text="📈 Лимиты API",
                    command=self.show_rate).pack(side="left", padx=(0, 8))
        GhostButton(trow, text="🔔 Уведомления",
                    command=self.show_notifications).pack(side="left", padx=8)
        GhostButton(trow, text="⭐ Мои звёзды ↗", command=lambda: webbrowser.open(
            f"https://github.com/{u['login']}?tab=stars")).pack(side="left", padx=8)
        GhostButton(trow, text="🔑 Токены ↗", command=lambda: webbrowser.open(
            "https://github.com/settings/tokens")).pack(side="left", padx=8)
        self.tools_out = Hint(tools, "")
        self.tools_out.pack(fill="x", padx=22, pady=(0, 12))

        self.load_overview()

    # ---------- data ----------
    def load_overview(self):
        def work():
            repos = self.app.client.list_repos()
            self.app.repos_cache = repos
            stars = sum(r["stargazers_count"] for r in repos)
            forks = sum(r["forks_count"] for r in repos)
            return stars, forks, len(repos)

        def done(res):
            stars, forks, n = res
            self.sc_stars.set(stars)
            self.sc_forks.set(forks)
            self.sc_repos.set(n)

        run_bg(work, done, lambda e: self.app.toast.show(str(e), False), self)

    def load_traffic(self):
        self.app.toast.show("Собираю данные трафика…")

        def work():
            c = self.app.client
            repos = self.app.repos_cache or c.list_repos()
            limit = int(cfg_get("traffic_limit", 30))
            repos = repos[:limit]

            def fetch(r):
                try:
                    v = c.traffic_views(r["owner"]["login"], r["name"])
                    cl = c.traffic_clones(r["owner"]["login"], r["name"])
                    return (r["name"], v["count"], v["uniques"],
                            cl["count"], cl["uniques"])
                except GitHubError:
                    return None

            # Параллельно (8 потоков) — быстрее в ~8 раз, чем по одному
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = [x for x in pool.map(fetch, repos) if x]

            tv = sum(x[1] for x in results)
            tuv = sum(x[2] for x in results)
            tc = sum(x[3] for x in results)
            tuc = sum(x[4] for x in results)
            rows = [x for x in results if x[1] or x[3]]
            rows.sort(key=lambda x: -x[1])
            return tv, tuv, tc, tuc, rows

        def done(res):
            tv, tuv, tc, tuc, rows = res
            self.sc_views.set(tv); self.sc_uviews.set(tuv)
            self.sc_clones.set(tc); self.sc_uclones.set(tuc)
            self.traffic_box.configure(state="normal")
            self.traffic_box.delete("1.0", "end")
            if rows:
                self.traffic_box.insert(
                    "end", f"{'Репозиторий':28} {'Views':>7} {'Uniq':>6} "
                           f"{'Clones':>7} {'Uniq':>6}\n" + "─" * 60 + "\n")
                for n, v, uv, cl, ucl in rows:
                    self.traffic_box.insert(
                        "end", f"{n[:28]:28} {v:>7} {uv:>6} {cl:>7} {ucl:>6}\n")
            else:
                self.traffic_box.insert("end", "Пока нет данных трафика "
                                               "(нужны права владельца/push).")
            self.traffic_box.configure(state="disabled")
            self.app.toast.show("Трекер обновлён")

        run_bg(work, done, lambda e: self.app.toast.show(str(e), False), self)

    def save_profile(self):
        payload = dict(
            name=self.f_name.get(), company=self.f_company.get(),
            blog=self.f_blog.get(), location=self.f_location.get(),
            bio=self.f_bio.get("1.0", "end").strip(),
            hireable=bool(self.f_hireable.get()),
        )
        run_bg(lambda: self.app.client.update_profile(**payload),
               lambda _: self.app.toast.show("Профиль обновлён"),
               lambda e: self.app.toast.show(str(e), False), self)

    def show_rate(self):
        def done(r):
            core = r["resources"]["core"]
            reset = datetime.fromtimestamp(core["reset"]).strftime("%H:%M")
            self.tools_out.configure(
                text=f"API: осталось {core['remaining']} из {core['limit']} "
                     f"запросов · сброс в {reset}")
        run_bg(self.app.client.rate_limit, done,
               lambda e: self.app.toast.show(str(e), False), self)

    def show_notifications(self):
        def done(n):
            self.tools_out.configure(
                text=f"🔔 Непрочитанных уведомлений: {len(n)}" if n
                else "🔕 Нет новых уведомлений — всё чисто!")
        run_bg(self.app.client.notifications, done,
               lambda e: self.app.toast.show(str(e), False), self)


# --------------------------------------------------------------- repos -----
class ReposView(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self._built = False

    def build(self):
        if self._built:
            self.refresh()
            return
        self._built = True

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        head.grid_columnconfigure(0, weight=1)
        SectionTitle(head, "📦 Мои репозитории").grid(row=0, column=0, sticky="w")
        self.sort_box = ctk.CTkComboBox(
            head, corner_radius=12, width=180, font=(FONT, 13),
            values=["По дате обновления", "По звёздам", "По имени"],
            command=lambda _: self.render())
        self.sort_box.set("По дате обновления")
        self.sort_box.grid(row=0, column=1, padx=(8, 0))
        GhostButton(head, text="🔄 Обновить", command=self.refresh).grid(
            row=0, column=2, padx=(8, 0))

        self.search = Entry(self, placeholder_text="🔍 Поиск по репозиториям…")
        self.search.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._search_job = None
        self.search.bind("<KeyRelease>", self._debounced_render)

        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.grid(row=2, column=0, sticky="ew")
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.refresh()

    def _debounced_render(self, _event=None):
        """Перерисовка через 250 мс после последнего нажатия — быстрее UI."""
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(250, self.render)

    def refresh(self):
        def done(repos):
            self.app.repos_cache = repos
            self.render()
        run_bg(self.app.client.list_repos, done,
               lambda e: self.app.toast.show(str(e), False), self)

    def render(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        q = (self.search.get() or "").lower()
        repos = [r for r in (self.app.repos_cache or [])
                 if q in r["name"].lower()]
        sort = getattr(self, "sort_box", None)
        mode = sort.get() if sort else "По дате обновления"
        if mode == "По звёздам":
            repos.sort(key=lambda r: -r.get("stargazers_count", 0))
        elif mode == "По имени":
            repos.sort(key=lambda r: r["name"].lower())
        if not repos:
            Hint(self.list_frame, "Ничего не найдено…").grid(row=0, column=0)
            return
        for i, r in enumerate(repos):
            self._repo_card(r).grid(row=i, column=0, sticky="ew",
                                    pady=(0, 10))

    def _repo_card(self, r):
        card = Card(self.list_frame)
        card.grid_columnconfigure(1, weight=1)
        icon = "🔒" if r["private"] else "🌐"
        ctk.CTkLabel(card, text=icon, font=(FONT, 22)).grid(
            row=0, column=0, rowspan=2, padx=(18, 12), pady=14)
        ctk.CTkLabel(card, text=r["name"], font=(FONT, 16, "bold"),
                     anchor="w").grid(row=0, column=1, sticky="sw",
                                      pady=(12, 0))
        desc = r.get("description") or "Без описания"
        Hint(card, f"{desc[:80]}   ·   ⭐ {r['stargazers_count']}  "
             f"🍴 {r['forks_count']}  ⚠️ {r['open_issues_count']} issues"
             ).grid(row=1, column=1, sticky="nw", pady=(0, 12))

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=2, padx=16)
        GhostButton(btns, text="↗ Открыть", width=90, command=lambda:
                    webbrowser.open(r["html_url"])).pack(side="left", padx=4)
        GhostButton(btns, text="📋 Clone", width=80, command=lambda:
                    self.copy_clone_url(r)).pack(side="left", padx=4)
        GhostButton(btns, text="✨ Фишки", width=90, command=lambda:
                    self.add_goodies(r)).pack(side="left", padx=4)
        vis_text = "🌐 Открыть доступ" if r["private"] else "🔒 Сделать приватным"
        GhostButton(btns, text=vis_text, width=140, command=lambda:
                    self.toggle_visibility(r)).pack(side="left", padx=4)
        del_btn = GhostButton(btns, text="🗑", width=40,
                              border_color=ERR_COLOR, text_color=ERR_COLOR,
                              command=lambda: self.delete_repo(r))
        del_btn.pack(side="left", padx=4)
        return card

    def copy_clone_url(self, r):
        url = r.get("clone_url") or f"{r['html_url']}.git"
        self.clipboard_clear()
        self.clipboard_append(url)
        self.app.toast.show(f"Ссылка скопирована: {url}")

    def toggle_visibility(self, r):
        run_bg(lambda: self.app.client.update_repo(
                   r["owner"]["login"], r["name"], private=not r["private"]),
               lambda _: (self.app.toast.show("Видимость изменена"),
                          self.refresh()),
               lambda e: self.app.toast.show(str(e), False), self)

    def add_goodies(self, r):
        """Окно выбора фишек (с объяснениями) для существующего репозитория."""
        GoodiesDialog(self.app, r)

    def delete_repo(self, r):
        dlg = ctk.CTkInputDialog(
            text=f"Введите имя репозитория «{r['name']}» для удаления.\n"
                 f"Это действие необратимо!",
            title="Удаление репозитория")
        if dlg.get_input() != r["name"]:
            self.app.toast.show("Удаление отменено", False)
            return
        run_bg(lambda: self.app.client.delete_repo(r["owner"]["login"], r["name"]),
               lambda _: (self.app.toast.show("Репозиторий удалён"), self.refresh()),
               lambda e: self.app.toast.show(str(e), False), self)


# ------------------------------------------------------------- publish -----
class PublishView(ctk.CTkScrollableFrame):
    """Создание репозитория + автопубликация локального проекта."""
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.folder = None
        self._built = False

    def build(self):
        if self._built:
            return
        self._built = True

        SectionTitle(self, "🚀 Новый репозиторий и автопубликация").grid(
            row=0, column=0, sticky="ew", pady=(0, 12))

        # ---- основные настройки ----
        main = Card(self)
        main.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        main.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(main, text="Название*", font=(FONT, 13)).grid(
            row=0, column=0, sticky="w", padx=(22, 10), pady=(18, 6))
        self.f_name = Entry(main, placeholder_text="my-awesome-project")
        self.f_name.grid(row=0, column=1, sticky="ew", padx=(0, 22), pady=(18, 6))

        ctk.CTkLabel(main, text="Описание (EN)", font=(FONT, 13)).grid(
            row=1, column=0, sticky="w", padx=(22, 10), pady=6)
        self.f_desc = Entry(main, placeholder_text="A short description in English")
        self.f_desc.grid(row=1, column=1, sticky="ew", padx=(0, 22), pady=6)

        ctk.CTkLabel(main, text="Сайт проекта", font=(FONT, 13)).grid(
            row=2, column=0, sticky="w", padx=(22, 10), pady=6)
        self.f_home = Entry(main, placeholder_text="https://…")
        self.f_home.grid(row=2, column=1, sticky="ew", padx=(0, 22), pady=6)

        ctk.CTkLabel(main, text="Топики (через запятую)", font=(FONT, 13)).grid(
            row=3, column=0, sticky="w", padx=(22, 10), pady=6)
        self.f_topics = Entry(main, placeholder_text="python, gui, tools")
        self.f_topics.grid(row=3, column=1, sticky="ew", padx=(0, 22), pady=6)

        grid2 = ctk.CTkFrame(main, fg_color="transparent")
        grid2.grid(row=4, column=0, columnspan=2, sticky="ew",
                   padx=22, pady=(8, 6))
        ctk.CTkLabel(grid2, text=".gitignore:", font=(FONT, 13)).pack(
            side="left", padx=(0, 6))
        self.f_gitignore = ctk.CTkComboBox(
            grid2, corner_radius=12, width=170, font=(FONT, 13),
            values=["(нет)", "Python", "Node", "Go", "Rust", "Java", "C++",
                    "Unity", "VisualStudio", "Global/JetBrains"])
        self.f_gitignore.set("(нет)")
        self.f_gitignore.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(grid2, text="Лицензия:", font=(FONT, 13)).pack(
            side="left", padx=(0, 6))
        self.f_license = ctk.CTkComboBox(
            grid2, corner_radius=12, width=170, font=(FONT, 13),
            values=["(нет)", "mit", "apache-2.0", "gpl-3.0", "bsd-3-clause",
                    "mpl-2.0", "unlicense"])
        self.f_license.set("mit")
        self.f_license.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(grid2, text="Ветка:", font=(FONT, 13)).pack(
            side="left", padx=(0, 6))
        self.f_branch = Entry(grid2, width=110)
        self.f_branch.insert(0, "main")
        self.f_branch.pack(side="left")
        Hint(main, ".gitignore — какие файлы git будет игнорировать; "
                   "лицензия — что разрешено делать с вашим кодом "
                   "(MIT — самая свободная); ветка — имя главной ветки.",
             wraplength=900).grid(row=5, column=0, columnspan=2,
                                  sticky="w", padx=22, pady=(0, 14))

        # ---- настройки репозитория (с объяснениями) ----
        SectionTitle(self, "🛠 Настройки репозитория").grid(
            row=2, column=0, sticky="ew", pady=(8, 8))
        Hint(self, "Каждый пункт можно менять и после создания — "
                   "во вкладке «Репозитории» → «Открыть».").grid(
            row=3, column=0, sticky="w", pady=(0, 8))
        sw = Card(self)
        sw.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        swrow = ctk.CTkFrame(sw, fg_color="transparent")
        swrow.pack(fill="x", padx=22, pady=16)
        swrow.grid_columnconfigure((0, 1), weight=1, uniform="sw")

        self.opts = {}
        for i, (key, title, default, hint) in enumerate(REPO_OPTS):
            hs = HintSwitch(swrow, title, hint, on=default)
            hs.grid(row=i // 2, column=i % 2, sticky="new",
                    padx=(0, 14), pady=7)
            self.opts[key] = hs

        # ---- фишки (с объяснениями) ----
        SectionTitle(self, "✨ Фишки (всё уйдёт на GitHub на английском)"
                     ).grid(row=5, column=0, sticky="ew", pady=(8, 8))
        Hint(self, "Файлы сообщества, шаблоны для баг-репортов и отзывов, "
                   "автоматизация. Любой пункт можно добавить и в уже "
                   "существующий репозиторий: «Репозитории» → «✨ Фишки»."
             ).grid(row=6, column=0, sticky="w", pady=(0, 8))
        good = Card(self)
        good.grid(row=7, column=0, sticky="ew", pady=(0, 12))
        grow = ctk.CTkFrame(good, fg_color="transparent")
        grow.pack(fill="x", padx=22, pady=16)
        grow.grid_columnconfigure((0, 1), weight=1, uniform="gd")

        self.goodies = {}
        for i, (key, title, default, hint) in enumerate(GOODIES):
            hs = HintSwitch(grow, title, hint, on=default)
            hs.grid(row=i // 2, column=i % 2, sticky="new",
                    padx=(0, 14), pady=7)
            self.goodies[key] = hs

        # ---- картинки ----
        SectionTitle(self, "🖼 Картинки проекта").grid(
            row=8, column=0, sticky="ew", pady=(8, 8))
        imgs = Card(self)
        imgs.grid(row=9, column=0, sticky="ew", pady=(0, 12))
        irow = ctk.CTkFrame(imgs, fg_color="transparent")
        irow.pack(fill="x", padx=22, pady=(16, 6))
        GhostButton(irow, text="➕ Добавить картинки…",
                    command=self.pick_images).pack(side="left")
        GhostButton(irow, text="🧹 Очистить список",
                    command=self.clear_images).pack(side="left", padx=8)
        Hint(imgs, "Скриншоты и логотип проекта (PNG/JPG/GIF, до 10 МБ). "
                   "Они автоматически загрузятся в папку docs/images "
                   "репозитория и вставятся в раздел «Screenshots» README — "
                   "ничего прописывать вручную не нужно. Работает вместе с "
                   "фишкой «README-каркас».", wraplength=900).pack(
            fill="x", padx=22)
        self.images = []
        self.images_lbl = Hint(imgs, "Картинки не выбраны")
        self.images_lbl.pack(fill="x", padx=22, pady=(4, 14))

        # ---- локальная папка ----
        SectionTitle(self, "📁 Автопубликация локального проекта (необязательно)"
                     ).grid(row=10, column=0, sticky="ew", pady=(8, 8))
        loc = Card(self)
        loc.grid(row=11, column=0, sticky="ew", pady=(0, 12))
        lrow = ctk.CTkFrame(loc, fg_color="transparent")
        lrow.pack(fill="x", padx=22, pady=16)
        GhostButton(lrow, text="Выбрать папку…",
                    command=self.pick_folder).pack(side="left")
        self.folder_lbl = Hint(lrow, "  Папка не выбрана — будет создан пустой "
                                     "репозиторий")
        self.folder_lbl.pack(side="left")

        # ---- запуск ----
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=12, column=0, sticky="ew", pady=(4, 8))
        self.s_open = Switch(actions, text="🌍 Открыть в браузере после создания")
        if cfg_get("open_browser", True):
            self.s_open.select()
        self.s_open.pack(side="left")
        self.create_btn = RoundButton(actions, text="🚀 Создать и опубликовать",
                                      width=260, height=46,
                                      command=self.create)
        self.create_btn.pack(side="right")

        self.log = ctk.CTkTextbox(self, height=170, corner_radius=RADIUS,
                                  fg_color=CARD, font=("Consolas", 12))
        self.log.grid(row=13, column=0, sticky="ew", pady=(4, 20))
        self.log.insert("1.0", "Журнал публикации появится здесь…\n")
        self.log.configure(state="disabled")

    # ---------- helpers ----------
    def pick_images(self):
        paths = filedialog.askopenfilenames(
            title="Выберите картинки (скриншоты, логотип)",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif *.webp"),
                       ("Все файлы", "*.*")])
        for p in paths:
            if p not in self.images:
                if os.path.getsize(p) > 10 * 1024 * 1024:
                    self.app.toast.show(
                        f"{os.path.basename(p)} больше 10 МБ — пропущен", False)
                    continue
                self.images.append(p)
        self._update_images_lbl()

    def clear_images(self):
        self.images = []
        self._update_images_lbl()

    def _update_images_lbl(self):
        if self.images:
            names = ", ".join(os.path.basename(p) for p in self.images)
            self.images_lbl.configure(
                text=f"✅ Выбрано {len(self.images)}: {names}"[:200])
        else:
            self.images_lbl.configure(text="Картинки не выбраны")
    def pick_folder(self):
        path = filedialog.askdirectory(title="Выберите папку проекта")
        if path:
            self.folder = path
            self.folder_lbl.configure(text=f"  📂 {path}")

    def log_line(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def create(self):
        name = self.f_name.get().strip()
        if not name:
            self.app.toast.show("Укажите название репозитория", False)
            return
        self.create_btn.configure(state="disabled", text="Публикую…")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        o = {k: bool(v.get()) for k, v in self.opts.items()}
        cfg = dict(
            name=name,
            description=self.f_desc.get().strip(),
            homepage=self.f_home.get().strip(),
            private=o["private"],
            has_issues=o["issues"],
            has_wiki=o["wiki"],
            has_projects=o["projects"],
            has_discussions=o["discussions"],
            auto_init=o["autoinit"] or not self.folder,
            allow_squash_merge=o["squash"],
            allow_merge_commit=o["merge"],
            allow_rebase_merge=o["rebase"],
            delete_branch_on_merge=o["delbranch"],
            is_template=o["is_template"],
            allow_auto_merge=o["automerge"],
            allow_update_branch=o["updatebranch"],
        )
        gi = self.f_gitignore.get()
        if gi != "(нет)" and not self.folder:
            cfg["gitignore_template"] = gi
        lic = self.f_license.get()
        if lic != "(нет)":
            cfg["license_template"] = lic
        branch = (self.f_branch.get().strip() or "main")
        topics = [t.strip().lower().replace(" ", "-")
                  for t in self.f_topics.get().split(",") if t.strip()]
        goodies = {k: bool(v.get()) for k, v in self.goodies.items()}
        folder = self.folder
        images = list(self.images)
        ui = lambda msg: ui_call(lambda m=msg: self.log_line(m))

        def work():
            c = self.app.client
            owner = c.user["login"]
            ui(f"→ Creating repository '{name}'…")
            repo = c.create_repo(**cfg)
            ui(f"✓ Repository created: {repo['html_url']}")
            if branch and repo.get("default_branch") and \
                    branch != repo["default_branch"] and cfg["auto_init"]:
                try:
                    c.rename_branch(owner, name, repo["default_branch"], branch)
                    ui(f"✓ Default branch renamed to '{branch}'")
                except GitHubError as e:
                    ui(f"! Branch rename skipped: {e.message}")
            if topics:
                c.set_topics(owner, name, topics)
                ui(f"✓ Topics set: {', '.join(topics)}")
            if folder:
                ui(f"→ Publishing local folder: {folder}")
                self.app.push_local_folder(owner, name, folder, ui)
            self.app.push_goodies(owner, name, log=ui,
                                  repo_desc=cfg["description"],
                                  images=images, **goodies)
            ui("✓ Done! Everything pushed in English 🎉")
            return repo

        def done(repo):
            self.create_btn.configure(state="normal",
                                      text="🚀 Создать и опубликовать")
            self.app.toast.show(f"Репозиторий {repo['name']} готов!")
            if self.s_open.get():
                webbrowser.open(repo["html_url"])

        def err(e):
            self.create_btn.configure(state="normal",
                                      text="🚀 Создать и опубликовать")
            self.log_line(f"✗ Ошибка: {e}")
            self.app.toast.show(str(e), False)

        run_bg(work, done, err, self)


# ------------------------------------------------------- goodies dialog ----
class GoodiesDialog(ctk.CTkToplevel):
    """Добавление фишек и картинок в уже существующий репозиторий."""
    def __init__(self, app, repo):
        super().__init__(app)
        self.app = app
        self.repo = repo
        self.title(f"✨ Фишки — {repo['name']}")
        self.geometry("620x680")
        self.minsize(520, 480)
        self.transient(app)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(16, 4))
        ctk.CTkLabel(head, text=f"✨ Фишки для «{repo['name']}»",
                     font=(FONT, 18, "bold")).pack(anchor="w")
        Hint(head, "Выберите, что добавить. Всё будет отправлено на GitHub "
                   "на английском языке. Уже существующие файлы будут "
                   "аккуратно обновлены.", wraplength=560).pack(anchor="w")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10)

        self.switches = {}
        for key, title, default, hint in GOODIES:
            if key == "readme":
                # для существующего репо не переписываем README по умолчанию
                default = False
                hint += " ⚠️ Вкл. — существующий README будет ЗАМЕНЁН каркасом."
            hs = HintSwitch(body, title, hint, on=default)
            hs.pack(fill="x", padx=8, pady=6)
            self.switches[key] = hs

        # картинки
        img_card = Card(body)
        img_card.pack(fill="x", padx=8, pady=6)
        irow = ctk.CTkFrame(img_card, fg_color="transparent")
        irow.pack(fill="x", padx=14, pady=(12, 4))
        GhostButton(irow, text="🖼 Добавить картинки…",
                    command=self.pick_images).pack(side="left")
        self.images = []
        self.img_lbl = Hint(img_card,
                            "Картинки загрузятся в docs/images и сами "
                            "вставятся в раздел Screenshots README.",
                            wraplength=540)
        self.img_lbl.pack(fill="x", padx=14, pady=(2, 12))

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=18, pady=12)
        self.apply_btn = RoundButton(foot, text="🚀 Добавить выбранное",
                                     command=self.apply)
        self.apply_btn.pack(side="right")
        GhostButton(foot, text="Отмена", command=self.destroy).pack(
            side="right", padx=8)
        self.status = Hint(foot, "")
        self.status.pack(side="left")

    def pick_images(self):
        paths = filedialog.askopenfilenames(
            parent=self,
            title="Выберите картинки",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif *.webp"),
                       ("Все файлы", "*.*")])
        for p in paths:
            if p not in self.images and os.path.getsize(p) <= 10 * 1024 * 1024:
                self.images.append(p)
        if self.images:
            self.img_lbl.configure(text="✅ " + ", ".join(
                os.path.basename(p) for p in self.images)[:180])

    def apply(self):
        goodies = {k: bool(v.get()) for k, v in self.switches.items()}
        if not any(goodies.values()) and not self.images:
            self.status.configure(text="Ничего не выбрано", text_color=ERR_COLOR)
            return
        self.apply_btn.configure(state="disabled", text="Добавляю…")
        owner, name = self.repo["owner"]["login"], self.repo["name"]
        desc = self.repo.get("description") or ""
        images = list(self.images)

        def done(_):
            self.app.toast.show(f"Фишки добавлены в {name} (на английском)")
            self.destroy()

        def err(e):
            self.apply_btn.configure(state="normal",
                                     text="🚀 Добавить выбранное")
            self.status.configure(text=str(e), text_color=ERR_COLOR)

        run_bg(lambda: self.app.push_goodies(owner, name, images=images,
                                             repo_desc=desc, **goodies),
               done, err, self)


# ------------------------------------------------------------ settings -----
class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self._built = False

    def build(self):
        if self._built:
            return
        self._built = True
        SectionTitle(self, "🎨 Настройки приложения").grid(
            row=0, column=0, sticky="ew", pady=(0, 12))
        card = Card(self)
        card.grid(row=1, column=0, sticky="ew")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=18)

        # --- тема ---
        ctk.CTkLabel(inner, text="Тема оформления", font=(FONT, 14, "bold")
                     ).pack(anchor="w")
        Hint(inner, "Тёмная — приятна вечером и экономит заряд на OLED. "
                    "Светлая — лучше при ярком освещении. Системная — "
                    "приложение само повторяет тему Windows. Выбор "
                    "запоминается и применяется при следующем запуске.",
             wraplength=800).pack(anchor="w", pady=(2, 6))
        theme_map = {"dark": "🌙 Тёмная", "light": "☀️ Светлая",
                     "system": "🖥 Системная"}
        seg = ctk.CTkSegmentedButton(
            inner, values=list(theme_map.values()),
            corner_radius=12, font=(FONT, 13),
            command=self.change_theme)
        seg.set(theme_map.get(cfg_get("theme", "dark"), "🌙 Тёмная"))
        seg.pack(anchor="w", pady=(4, 18))

        # --- масштаб ---
        ctk.CTkLabel(inner, text="Масштаб интерфейса", font=(FONT, 14, "bold")
                     ).pack(anchor="w")
        Hint(inner, "Увеличьте, если текст кажется мелким (полезно на "
                    "экранах 2K/4K), или уменьшите, чтобы вместить больше. "
                    "Сохраняется и применяется сразу.",
             wraplength=800).pack(anchor="w", pady=(2, 6))
        scale_seg = ctk.CTkSegmentedButton(
            inner, values=["90%", "100%", "110%", "125%"],
            corner_radius=12, font=(FONT, 13),
            command=self.change_scaling)
        scale_seg.set(f"{int(float(cfg_get('scaling', 1.0)) * 100)}%")
        scale_seg.pack(anchor="w", pady=(4, 18))

        # --- трекер ---
        ctk.CTkLabel(inner, text="Трекер: сколько репозиториев сканировать",
                     font=(FONT, 14, "bold")).pack(anchor="w")
        Hint(inner, "Кнопка «Обновить трекер» опрашивает каждый репозиторий "
                    "(2 запроса на штуку). Больше репозиториев — полнее "
                    "картина, но дольше загрузка и выше расход лимита API "
                    "(5000 запросов/час).", wraplength=800).pack(
            anchor="w", pady=(2, 6))
        self.traffic_lbl = ctk.CTkLabel(
            inner, text=f"{int(cfg_get('traffic_limit', 30))} репозиториев",
            font=(FONT, 13))
        self.traffic_lbl.pack(anchor="w")
        slider = ctk.CTkSlider(inner, from_=5, to=100, number_of_steps=19,
                               width=300, progress_color=ACCENT,
                               command=self.change_traffic)
        slider.set(int(cfg_get("traffic_limit", 30)))
        slider.pack(anchor="w", pady=(4, 18))

        # --- поведение ---
        ctk.CTkLabel(inner, text="Поведение", font=(FONT, 14, "bold")).pack(
            anchor="w", pady=(0, 4))
        self.s_browser = HintSwitch(
            inner, "🌍 Открывать репозиторий в браузере после создания",
            "После успешной публикации новый репозиторий сразу откроется "
            "в браузере — удобно проверить результат. Настройка "
            "запоминается для вкладки «Публикация».",
            on=cfg_get("open_browser", True))
        self.s_browser.sw.configure(command=self.change_browser)
        self.s_browser.pack(anchor="w", fill="x", pady=(0, 6))
        self.s_autologin = HintSwitch(
            inner, "⚡ Входить автоматически при запуске",
            "Если токен сохранён, приложение сразу войдёт в аккаунт без "
            "нажатия кнопки «Войти» — быстрее старт.",
            on=cfg_get("autologin", False))
        self.s_autologin.sw.configure(command=self.change_autologin)
        self.s_autologin.pack(anchor="w", fill="x", pady=(0, 14))

        # --- диагностика ---
        ctk.CTkLabel(inner, text="Диагностика", font=(FONT, 14, "bold")).pack(
            anchor="w")
        Hint(inner, "Проверка связи с GitHub и остатка лимита API — если "
                    "что-то не работает, начните отсюда.",
             wraplength=800).pack(anchor="w", pady=(2, 6))
        drow = ctk.CTkFrame(inner, fg_color="transparent")
        drow.pack(anchor="w", pady=(0, 4))
        GhostButton(drow, text="📡 Проверить соединение",
                    command=self.ping).pack(side="left")
        self.diag_lbl = Hint(drow, "")
        self.diag_lbl.pack(side="left", padx=10)

        # --- аккаунт ---
        ctk.CTkLabel(inner, text="Аккаунт", font=(FONT, 14, "bold")).pack(
            anchor="w", pady=(14, 0))
        Hint(inner, f"Вы вошли как @{self.app.client.user['login']}. Выход "
                    "удалит сохранённый токен с этого компьютера (настройки "
                    "темы и масштаба останутся).", wraplength=800).pack(
            anchor="w", pady=(2, 8))
        GhostButton(inner, text="🚪 Выйти и забыть токен",
                    border_color=ERR_COLOR, text_color=ERR_COLOR,
                    command=self.logout).pack(anchor="w")

        # --- об авторе ---
        ctk.CTkLabel(inner, text="Об авторе", font=(FONT, 14, "bold")).pack(
            anchor="w", pady=(14, 0))
        Hint(inner, "Walrus GitHub Manager сделал MrSmartAss. Заглядывайте "
                    "на GitHub автора — там исходники, обновления и другие "
                    "проекты. Баг-репорты и идеи приветствуются!",
             wraplength=800).pack(anchor="w", pady=(2, 6))
        arow = ctk.CTkFrame(inner, fg_color="transparent")
        arow.pack(anchor="w", pady=(0, 4))
        GhostButton(arow, text="👽 Reddit",
                    command=lambda: webbrowser.open(AUTHOR_URL)).pack(
            side="left", padx=(0, 8))
        GhostButton(arow, text="🐙 GitHub автора ↗",
                    command=lambda: webbrowser.open(AUTHOR_URL)).pack(
            side="left")

        Hint(self, "\n🦭 Walrus GitHub Manager · by MrSmartAss\n"
                   "Все данные (issue-шаблоны, README, лейблы, коммиты) "
                   "отправляются на GitHub только на английском языке.").grid(
            row=2, column=0, sticky="w", pady=10)

    def change_theme(self, val):
        mode = {"🌙 Тёмная": "dark", "☀️ Светлая": "light",
                "🖥 Системная": "system"}[val]
        ctk.set_appearance_mode(mode)
        cfg_set(theme=mode)
        self.app.toast.show("Тема сохранена")

    def change_scaling(self, val):
        scale = int(val.rstrip("%")) / 100
        ctk.set_widget_scaling(scale)
        cfg_set(scaling=scale)

    def change_traffic(self, val):
        v = int(val)
        self.traffic_lbl.configure(text=f"{v} репозиториев")
        cfg_set(traffic_limit=v)

    def change_browser(self):
        cfg_set(open_browser=bool(self.s_browser.get()))

    def change_autologin(self):
        cfg_set(autologin=bool(self.s_autologin.get()))

    def ping(self):
        def work():
            r = self.app.client.rate_limit()
            core = r["resources"]["core"]
            return core

        def done(core):
            reset = datetime.fromtimestamp(core["reset"]).strftime("%H:%M")
            self.diag_lbl.configure(
                text=f"✅ GitHub доступен · API: {core['remaining']}/"
                     f"{core['limit']} · сброс в {reset}",
                text_color=OK_COLOR)

        self.diag_lbl.configure(text="Проверяю…")
        run_bg(work, done,
               lambda e: self.diag_lbl.configure(
                   text=f"⚠️ Нет связи: {e}", text_color=ERR_COLOR), self)

    def logout(self):
        cfg_set(token="")
        self.app.show_login()


# ----------------------------------------------------------------- app -----
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Walrus GitHub Manager --by. MrSmartAss")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self._set_icon()
        attach_context_menu(self)
        self.client = None
        self.repos_cache = []
        self.toast = Toast(self)
        self._pump_ui_queue()
        self.show_login()

    def _set_icon(self):
        """Иконка окна: морж + git (работает и из exe, и из исходников)."""
        try:
            if sys.platform == "win32":
                ico = resource_path(os.path.join("assets", "icon.ico"))
                if os.path.exists(ico):
                    self.iconbitmap(ico)
                    return
            png = resource_path(os.path.join("assets", "icon_64.png"))
            if os.path.exists(png):
                self._icon_img = tk.PhotoImage(file=png)
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _pump_ui_queue(self):
        """Разбор очереди колбеков из фоновых потоков (в UI-потоке)."""
        try:
            while True:
                fn = UI_QUEUE.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(50, self._pump_ui_queue)

    # ---------- screens ----------
    def clear(self):
        for w in self.winfo_children():
            if w is not self.toast:
                w.destroy()

    def show_login(self):
        self.clear()
        LoginFrame(self, self.on_login).pack(fill="both", expand=True)

    def on_login(self, client):
        self.client = client
        self.clear()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # sidebar
        side = ctk.CTkFrame(self, corner_radius=0, width=230, fg_color=CARD)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="🦭  Walrus\nGitHub", font=(FONT, 20, "bold"),
                     justify="left").pack(anchor="w", padx=24, pady=(28, 4))
        Hint(side, f"@{client.user['login']}").pack(anchor="w", padx=24,
                                                    pady=(0, 24))

        self.views = {}
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=(18, 18), pady=18)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.views["account"] = AccountView(content, self)
        self.views["repos"] = ReposView(content, self)
        self.views["publish"] = PublishView(content, self)
        self.views["settings"] = SettingsView(content, self)

        self.nav_btns = {}
        nav = [("account", "👤  Аккаунт"), ("repos", "📦  Репозитории"),
               ("publish", "🚀  Публикация"), ("settings", "⚙️  Настройки")]
        for key, label in nav:
            b = ctk.CTkButton(
                side, text=label, anchor="w", corner_radius=14, height=44,
                font=(FONT, 15), fg_color="transparent",
                text_color=("#111", "#eee"), hover_color=CARD2,
                command=lambda k=key: self.show_view(k))
            b.pack(fill="x", padx=14, pady=3)
            self.nav_btns[key] = b

        foot = ctk.CTkFrame(side, fg_color="transparent")
        foot.pack(side="bottom", pady=14)
        Hint(foot, "v1.0 · by MrSmartAss").pack()
        links = ctk.CTkFrame(foot, fg_color="transparent")
        links.pack(pady=(6, 0))
        GhostButton(links, text="👽 Reddit", width=86, height=30,
                    command=lambda: webbrowser.open(AUTHOR_URL)).pack(
            side="left", padx=3)
        GhostButton(links, text="🐙 GitHub", width=86, height=30,
                    command=lambda: webbrowser.open(AUTHOR_URL)).pack(
            side="left", padx=3)
        self.show_view("account")
        self.toast.show(f"Добро пожаловать, {client.user['login']}!")

    def show_view(self, key):
        for k, v in self.views.items():
            v.grid_forget()
            self.nav_btns[k].configure(fg_color="transparent",
                                       text_color=("#111111", "#eeeeee"))
        self.nav_btns[key].configure(fg_color=ACCENT,
                                     text_color=("#ffffff", "#ffffff"))
        view = self.views[key]
        view.grid(row=0, column=0, sticky="nsew")
        view.build()

    # ---------- shared operations ----------
    def push_goodies(self, owner, repo, bug=False, feedback=False,
                     labels=False, contributing=False, coc=False, pr=False,
                     readme=False, badges=False, security=False,
                     funding=False, changelog=False, editorconfig=False,
                     ci=False, dependabot=False, codeowners=False,
                     images=None, log=None, repo_desc=""):
        """Заливает английские шаблоны/файлы/картинки в репозиторий."""
        c = self.client
        log = log or (lambda m: None)
        images = images or []

        def put(path, text, msg):
            c.put_file(owner, repo, path, text.encode("utf-8"), msg)
            log(f"✓ Added {path}")

        # --- картинки: загружаем в docs/images ---
        image_names = []
        for p in images:
            base = os.path.basename(p).replace(" ", "-")
            try:
                with open(p, "rb") as fh:
                    c.put_file(owner, repo, f"docs/images/{base}", fh.read(),
                               f"Add image {base}")
                image_names.append(base)
                log(f"✓ Uploaded image docs/images/{base}")
            except Exception as e:
                log(f"! Image {base} failed: {e}")

        if bug:
            put(".github/ISSUE_TEMPLATE/bug_report.yml", T.BUG_REPORT_YML,
                "Add bug report issue template")
        if feedback:
            put(".github/ISSUE_TEMPLATE/feedback.yml", T.FEEDBACK_YML,
                "Add feedback / feature request template")
        if bug or feedback:
            put(".github/ISSUE_TEMPLATE/config.yml",
                T.ISSUE_CONFIG_YML.format(owner=owner, repo=repo),
                "Configure issue templates")
        if contributing:
            put("CONTRIBUTING.md", T.CONTRIBUTING_MD,
                "Add contributing guidelines")
        if coc:
            put("CODE_OF_CONDUCT.md", T.CODE_OF_CONDUCT_MD,
                "Add code of conduct")
        if pr:
            put(".github/PULL_REQUEST_TEMPLATE.md", T.PR_TEMPLATE_MD,
                "Add pull request template")
        if security:
            put("SECURITY.md", T.SECURITY_MD, "Add security policy")
        if funding:
            put(".github/FUNDING.yml", T.FUNDING_YML.format(owner=owner),
                "Add funding configuration")
        if changelog:
            put("CHANGELOG.md", T.CHANGELOG_MD, "Add changelog")
        if editorconfig:
            put(".editorconfig", T.EDITORCONFIG, "Add editorconfig")
        if ci:
            put(".github/workflows/ci.yml", T.CI_WORKFLOW_YML,
                "Add CI workflow")
        if dependabot:
            put(".github/dependabot.yml", T.DEPENDABOT_YML,
                "Add dependabot configuration")
        if codeowners:
            put(".github/CODEOWNERS", T.CODEOWNERS.format(owner=owner),
                "Add code owners")

        # --- README: каркас + бейджи + картинки ---
        if readme:
            put("README.md", T.build_readme(
                    repo, owner,
                    repo_desc or "Project description goes here.",
                    badges=badges, image_names=image_names),
                "Add README")
        elif image_names or badges:
            # README-каркас выключен — аккуратно дополняем существующий
            text, _sha = c.get_readme(owner, repo)
            if text is None:
                text = f"# {repo}\n"
            if badges and "img.shields.io" not in text:
                lines = text.split("\n")
                insert_at = 1 if lines and lines[0].startswith("#") else 0
                lines.insert(insert_at,
                             "\n" + T.BADGES.format(owner=owner, name=repo))
                text = "\n".join(lines)
            if image_names and "## Screenshots" not in text:
                text += T.screenshots_markdown(image_names)
            put("README.md", text, "Update README (badges / screenshots)")

        if labels:
            for name, color, desc in T.LABELS:
                c.create_label(owner, repo, name, color, desc)
            log(f"✓ Created {len(T.LABELS)} labels")

    def push_local_folder(self, owner, repo, folder, log):
        """Публикация локальной папки: git если есть, иначе через API."""
        token = self.client.token
        url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
        git_ok = False
        try:
            subprocess.run(["git", "--version"], capture_output=True,
                           check=True, timeout=10)
            git_ok = True
        except Exception:
            pass

        if git_ok:
            def git(*args, cwd=folder):
                r = subprocess.run(["git"] + list(args), cwd=cwd,
                                   capture_output=True, text=True, timeout=300)
                if r.returncode != 0:
                    raise RuntimeError(r.stderr.strip()[:300])
                return r.stdout

            if not os.path.isdir(os.path.join(folder, ".git")):
                git("init", "-b", "main")
                log("✓ git init")
            git("add", "-A")
            try:
                git("-c", "user.name=GitHub Manager",
                    "-c", "user.email=manager@users.noreply.github.com",
                    "commit", "-m", "Initial commit")
                log("✓ Commit created: 'Initial commit'")
            except RuntimeError as e:
                if "nothing to commit" not in str(e):
                    raise
            try:
                git("remote", "add", "origin", url)
            except RuntimeError:
                git("remote", "set-url", "origin", url)
            git("push", "-u", "origin", "HEAD:main", "--force")
            git("remote", "set-url", "origin",
                f"https://github.com/{owner}/{repo}.git")  # убрать токен
            log("✓ Pushed via git")
        else:
            log("… git не найден — загружаю файлы через API")
            skip_dirs = {".git", "node_modules", "__pycache__", ".venv",
                         "dist", "build", ".idea", ".vscode"}
            count = 0
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, folder).replace("\\", "/")
                    if os.path.getsize(full) > 25 * 1024 * 1024:
                        log(f"! Skipped (>25MB): {rel}")
                        continue
                    with open(full, "rb") as fh:
                        self.client.put_file(owner, repo, rel, fh.read(),
                                             f"Add {rel}")
                    count += 1
                    if count % 10 == 0:
                        log(f"… uploaded {count} files")
            log(f"✓ Uploaded {count} files via API")


if __name__ == "__main__":
    App().mainloop()
