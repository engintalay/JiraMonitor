#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jira Monitor - Bağımsız Masaüstü Uygulaması
Python + Tkinter ile hazırlanmıştır.
"""

__version__ = "1.1.3.202604030915"

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
import time
from datetime import datetime
import urllib.request
import urllib.parse
import base64


class JiraClient:
    """Jira REST API istemcisi"""
    
    def __init__(self, server_url, username, api_token):
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth_header = self._create_auth_header()
    
    def _create_auth_header(self):
        """Basic auth header oluştur"""
        credentials = f"{self.username}:{self.api_token}".encode('utf-8')
        encoded = base64.b64encode(credentials).decode('utf-8')
        return f"Basic {encoded}"
    
    def _make_request(self, endpoint, params=None):
        """HTTP isteği yap"""
        url = f"{self.server_url}{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        try:
            request = urllib.request.Request(url)
            request.add_header("Authorization", self.auth_header)
            request.add_header("Content-Type", "application/json")
            
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"error": f"Bağlantı hatası: {e.reason}"}
        except Exception as e:
            return {"error": f"Bilinmeyen hata: {str(e)}"}
    
    def search_issues(self, jql, start=0, max_results=100):
        """JQL ile issue arama"""
        params = {
            "jql": jql,
            "start": start,
            "maxResults": max_results,
            "fields": "summary,description,assignee,creator,project,status,created,updated,priority,components,labels,reporter,issuetype,updated"
        }
        return self._make_request("/rest/api/2/search", params)
    
    def get_issue(self, issue_key):
        """Tek issue detayı"""
        return self._make_request(f"/rest/api/2/issue/{issue_key}")
    
    def get_issue_comments(self, issue_key):
        """Issue yorumları"""
        return self._make_request(f"/rest/api/2/issue/{issue_key}?fields=comment")

    def add_comment(self, issue_key, body):
        """Yorum ekle"""
        url = f"{self.server_url}/rest/api/2/issue/{issue_key}/comment"
        data = json.dumps({"body": body}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", self.auth_header)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def update_comment(self, issue_key, comment_id, body):
        """Yorum güncelle"""
        url = f"{self.server_url}/rest/api/2/issue/{issue_key}/comment/{comment_id}"
        data = json.dumps({"body": body}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, method="PUT")
            req.add_header("Authorization", self.auth_header)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def get_attachments(self, issue_key):
        """Dosya eklerini getir"""
        result = self._make_request(f"/rest/api/2/issue/{issue_key}?fields=attachment")
        if "error" in result:
            return result
        return result.get("fields", {}).get("attachment", [])

    def get_current_user(self):
        """Giriş yapan kullanıcıyı getir"""
        return self._make_request("/rest/api/2/myself")

    def assign_issue(self, issue_key, username):
        """Issue'yu kullanıcıya ata"""
        url = f"{self.server_url}/rest/api/2/issue/{issue_key}/assignee"
        data = json.dumps({"name": username}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, method="PUT")
            req.add_header("Authorization", self.auth_header)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return {"ok": True}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def update_issue_description(self, issue_key, description):
        """Issue açıklamasını güncelle"""
        url = f"{self.server_url}/rest/api/2/issue/{issue_key}"
        data = json.dumps({"fields": {"description": description}}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, method="PUT")
            req.add_header("Authorization", self.auth_header)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return {"ok": True}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def download_attachment(self, url, dest_path):
        """Eki indir"""
        try:
            req = urllib.request.Request(url)
            req.add_header("Authorization", self.auth_header)
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(dest_path, "wb") as f:
                    f.write(resp.read())
            return None
        except Exception as e:
            return str(e)

    def get_transitions(self, issue_key):
        """Issue'nun geçiş yapabileceği durumları getir"""
        return self._make_request(f"/rest/api/2/issue/{issue_key}/transitions")

    def transition_issue(self, issue_key, transition_id):
        """Issue'yu yeni duruma geçir"""
        url = f"{self.server_url}/rest/api/2/issue/{issue_key}/transitions"
        data = json.dumps({"transition": {"id": transition_id}}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", self.auth_header)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return {"ok": True}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"error": str(e)}

    def get_issue_links(self, issue_key):
        """Issue'nun linkli issue'larını getir"""
        result = self._make_request(f"/rest/api/2/issue/{issue_key}?fields=issuelinks")
        if "error" in result:
            return []
        return result.get("fields", {}).get("issuelinks", [])


class ConfigManager:
    """Ayarları yöneten sınıf"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser("~"), ".jira_monitor_config.json")
        self.config = self._load_config()
    
    def _load_config(self):
        """Ayarları yükle"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            "server_url": "https://jira.gelirler.gov.tr",
            "username": "",
            "api_token": "",
            "refresh_interval": 120,
            "default_users": "haktan.atamer,ayse.aydogdu,yasarcan.tak,engin.talay,umutcan.hazir,furkan.yilmaz,sebnem.manav,feride.kepenek,yunus.akyildirim,ersen.gultepe,firat.ciftci,murat.kanbes",
            "default_projects": "EVDBS,EPDK,Vedop3_VT,KONF",
            "default_status": "OPEN,'In Progress',Reopened",
            "extra_projects": "",
            "extra_statuses": "",
            "assign_queue": [],
            "assign_queue_index": 0,
            "notifications_enabled": True,
            "column_widths": {}
        }
    
    def save_config(self, config):
        """Ayarları kaydet"""
        self.config = config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        """Ayar değeri al"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Ayar değeri set et"""
        self.config[key] = value


class SettingsDialog:
    """Ayarlar penceresi"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Jira Monitor - Ayarlar")
        self.dialog.geometry("650x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Modern stil
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Widget'ları oluştur"""
        # Ana frame
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Butonlar — her zaman altta görünür
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

        # Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Bağlantı sekmesi
        conn_frame = ttk.Frame(notebook, padding="15")
        notebook.add(conn_frame, text="  Bağlantı  ")
        
        ttk.Label(conn_frame, text="Jira Sunucu URL:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.server_url = ttk.Entry(conn_frame, width=60, font=('Segoe UI', 10))
        self.server_url.pack(fill=tk.X, pady=(0, 15))
        self.server_url.insert(0, self.config_manager.get("server_url", ""))
        
        ttk.Label(conn_frame, text="Kullanıcı Adı:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.username = ttk.Entry(conn_frame, width=60, font=('Segoe UI', 10))
        self.username.pack(fill=tk.X, pady=(0, 15))
        self.username.insert(0, self.config_manager.get("username", ""))
        
        ttk.Label(conn_frame, text="Şifre:", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.api_token = ttk.Entry(conn_frame, width=60, font=('Segoe UI', 10), show="*")
        self.api_token.pack(fill=tk.X, pady=(0, 15))
        self.api_token.insert(0, self.config_manager.get("api_token", ""))
        
        # Filtreler sekmesi
        filter_frame = ttk.Frame(notebook, padding="15")
        notebook.add(filter_frame, text="  Filtreler  ")
        
        # Kaydırılabilir canvas
        canvas = tk.Canvas(filter_frame, highlightthickness=0)
        vsb = ttk.Scrollbar(filter_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        ttk.Label(inner_frame, text="Yenileme Süresi (saniye):", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.refresh_interval = ttk.Entry(inner_frame, width=15, font=('Segoe UI', 10))
        self.refresh_interval.pack(anchor=tk.W, pady=(0, 15))
        self.refresh_interval.insert(0, str(self.config_manager.get("refresh_interval", 120)))
        
        ttk.Label(inner_frame, text="Varsayılan Kullanıcılar (virgülle ayırın):", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.default_users = scrolledtext.ScrolledText(inner_frame, width=60, height=5, font=('Segoe UI', 10))
        self.default_users.pack(fill=tk.X, pady=(0, 15))
        self.default_users.insert("1.0", self.config_manager.get("default_users", ""))
        
        ttk.Label(inner_frame, text="Varsayılan Projeler (virgülle ayırın):", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.default_projects = scrolledtext.ScrolledText(inner_frame, width=60, height=3, font=('Segoe UI', 10))
        self.default_projects.pack(fill=tk.X, pady=(0, 15))
        self.default_projects.insert("1.0", self.config_manager.get("default_projects", ""))
        
        ttk.Label(inner_frame, text="Varsayılan Status (virgülle ayırın):", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.default_status = ttk.Entry(inner_frame, width=60, font=('Segoe UI', 10))
        self.default_status.pack(anchor=tk.W, pady=(0, 15))
        self.default_status.insert(0, self.config_manager.get("default_status", ""))

        ttk.Label(inner_frame, text="Ek Projeler (combobox'ta görünür, virgülle ayırın):", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.extra_projects = ttk.Entry(inner_frame, width=60, font=('Segoe UI', 10))
        self.extra_projects.pack(fill=tk.X, pady=(0, 15))
        self.extra_projects.insert(0, self.config_manager.get("extra_projects", ""))

        ttk.Label(inner_frame, text="Ek Statuslar (combobox'ta görünür, virgülle ayırın):", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.extra_statuses = ttk.Entry(inner_frame, width=60, font=('Segoe UI', 10))
        self.extra_statuses.pack(fill=tk.X, pady=(0, 15))
        self.extra_statuses.insert(0, self.config_manager.get("extra_statuses", ""))

        # Bildirimler
        ttk.Label(inner_frame, text="Bildirimler:", style='Header.TLabel').pack(anchor=tk.W, pady=(15, 5))
        self.notifications_var = tk.BooleanVar(value=self.config_manager.get("notifications_enabled", True))
        ttk.Checkbutton(inner_frame, text="Yeni issue bildirimlerini göster", variable=self.notifications_var).pack(anchor=tk.W, pady=(0, 10))
        ttk.Button(inner_frame, text="Test Bildirimi Gönder", command=self._test_notification).pack(anchor=tk.W)

        # Atama Kuyruğu sekmesi
        queue_frame = ttk.Frame(notebook, padding="15")
        notebook.add(queue_frame, text="  Atama Kuyruğu  ")
        self._build_queue_tab(queue_frame)
        
        ttk.Button(button_frame, text="Kaydet", command=self._save, width=15).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="İptal", command=self._cancel, width=15).pack(side=tk.RIGHT, padx=5)
    
    def _save(self):
        """Kaydet butonu"""
        config = {
            "server_url": self.server_url.get().strip(),
            "username": self.username.get().strip(),
            "api_token": self.api_token.get().strip(),
            "refresh_interval": int(self.refresh_interval.get()),
            "default_users": self.default_users.get("1.0", tk.END).strip(),
            "default_projects": self.default_projects.get("1.0", tk.END).strip(),
            "default_status": self.default_status.get().strip(),
            "extra_projects": self.extra_projects.get().strip(),
            "extra_statuses": self.extra_statuses.get().strip(),
            "assign_queue": list(self.queue_listbox.get(0, tk.END)),
            "assign_queue_index": self.config_manager.get("assign_queue_index", 0),
            "notifications_enabled": self.notifications_var.get(),
        }
        self.config_manager.save_config(config)
        self.result = config
        self.dialog.destroy()

    def _cancel(self):
        """İptal butonu"""
        self.dialog.destroy()
    
    def _test_notification(self):
        """Test bildirimi gonder"""
        send_notification("Jira Monitor", "Bu bir test bildirimidir.")
        messagebox.showinfo("Bildirim", "Test bildirimi gonderildi!", parent=self.dialog)


    def _build_queue_tab(self, parent):
        ttk.Label(parent, text="Round-Robin Atama Listesi", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 8))

        # Mevcut sıra göstergesi
        idx = self.config_manager.get("assign_queue_index", 0)
        queue = self.config_manager.get("assign_queue", [])
        next_user = queue[idx % len(queue)] if queue else "-"
        self.lbl_next = ttk.Label(parent, text=f"Sıradaki: {next_user}", foreground="#0078d7")
        self.lbl_next.pack(anchor=tk.W, pady=(0, 8))

        # Liste + butonlar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.queue_listbox = tk.Listbox(list_frame, font=("Segoe UI", 10), height=10, selectmode=tk.SINGLE)
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.queue_listbox.yview)
        self.queue_listbox.configure(yscrollcommand=vsb.set)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.LEFT, fill=tk.Y)

        for u in queue:
            self.queue_listbox.insert(tk.END, u)

        btn_col = ttk.Frame(list_frame)
        btn_col.pack(side=tk.LEFT, padx=(8, 0), anchor=tk.N)
        ttk.Button(btn_col, text="▲ Yukarı", width=12, command=self._queue_up).pack(pady=2)
        ttk.Button(btn_col, text="▼ Aşağı", width=12, command=self._queue_down).pack(pady=2)
        ttk.Button(btn_col, text="✕ Sil", width=12, command=self._queue_remove).pack(pady=2)
        ttk.Button(btn_col, text="Sıfırla", width=12, command=self._queue_reset).pack(pady=(12, 2))

        # Kullanıcı ekle
        add_frame = ttk.Frame(parent)
        add_frame.pack(fill=tk.X, pady=(8, 0))
        default_users = [u.strip() for u in self.config_manager.get("default_users", "").split(",") if u.strip()]
        self.entry_queue_user = ttk.Combobox(add_frame, font=("Segoe UI", 10), values=default_users)
        self.entry_queue_user.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(add_frame, text="Ekle", command=self._queue_add).pack(side=tk.LEFT)

    def _queue_add(self):
        user = self.entry_queue_user.get().strip()
        if user:
            self.queue_listbox.insert(tk.END, user)
            self.entry_queue_user.delete(0, tk.END)

    def _queue_remove(self):
        sel = self.queue_listbox.curselection()
        if sel:
            self.queue_listbox.delete(sel[0])

    def _queue_up(self):
        sel = self.queue_listbox.curselection()
        if sel and sel[0] > 0:
            i = sel[0]
            val = self.queue_listbox.get(i)
            self.queue_listbox.delete(i)
            self.queue_listbox.insert(i - 1, val)
            self.queue_listbox.selection_set(i - 1)

    def _queue_down(self):
        sel = self.queue_listbox.curselection()
        if sel and sel[0] < self.queue_listbox.size() - 1:
            i = sel[0]
            val = self.queue_listbox.get(i)
            self.queue_listbox.delete(i)
            self.queue_listbox.insert(i + 1, val)
            self.queue_listbox.selection_set(i + 1)

    def _queue_reset(self):
        self.config_manager.set("assign_queue_index", 0)
        self.config_manager.save_config(self.config_manager.config)
        queue = list(self.queue_listbox.get(0, tk.END))
        next_user = queue[0] if queue else "-"
        self.lbl_next.config(text=f"Sıradaki: {next_user}")


def send_notification(title, message):
    """Cross-platform bildirim (Windows + Linux + macOS)"""
    import sys
    try:
        if sys.platform == "win32":
            # Windows: winsound bip + fallback popup
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
            # System tray balloon tip via ctypes
            try:
                import ctypes
                ctypes.windll.user32.MessageBeep(0x00000040)
            except Exception:
                pass
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{message}" with title "{title}"'],
                check=False, timeout=10
            )
        else:
            import subprocess
            subprocess.run(
                ["notify-send", title, message],
                check=False, timeout=10
            )
    except Exception:
        pass


def _jira_to_text(text):
    """Jira wiki markup / basit HTML'i okunabilir metne çevirir (fallback)"""
    if not text:
        return ""
    import re
    text = re.sub(r'\{color[^}]*\}(.*?)\{color\}', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\{[^}]+\}', '', text)
    text = re.sub(r'!([^|!]+)(?:\|[^!]*)!', r'[Görsel: \1]', text)
    text = re.sub(r'\[([^\|]+)\|([^\]]+)\]', r'\1 (\2)', text)
    text = re.sub(r'h[1-6]\.\s*', '', text)
    text = re.sub(r'\*\*?(.*?)\*\*?', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def render_jira_markup(widget, text):
    """
    Jira wiki markup'ı Tkinter Text widget'ına tag'lerle render eder.
    widget: tk.Text (NORMAL state'de olmalı)
    """
    import re, webbrowser

    widget.delete("1.0", tk.END)

    # Seçili metin disabled modda da okunabilsin
    widget.configure(selectbackground="#0078d7", selectforeground="white", inactiveselectbackground="#0078d7")

    # Tag tanımları
    widget.tag_configure("h1", font=("Segoe UI", 16, "bold"), spacing3=4)
    widget.tag_configure("h2", font=("Segoe UI", 14, "bold"), spacing3=3)
    widget.tag_configure("h3", font=("Segoe UI", 12, "bold"), spacing3=2)
    widget.tag_configure("bold", font=("Segoe UI", 10, "bold"))
    widget.tag_configure("italic", font=("Segoe UI", 10, "italic"))
    widget.tag_configure("underline", underline=True)
    widget.tag_configure("strike", overstrike=True)
    widget.tag_configure("code", font=("Courier New", 9), background="#f0f0f0")
    widget.tag_configure("bullet", lmargin1=20, lmargin2=30)
    widget.tag_configure("link", foreground="#0078d7", underline=True)
    widget.tag_configure("table_header", font=("Segoe UI", 10, "bold"), background="#e0e0e0")
    widget.tag_configure("table_cell", background="#f8f8f8")
    widget.tag_configure("table_alt", background="#ffffff")

    if not text:
        return

    # Görselleri kaldır
    text = re.sub(r'!\[?[^\]]*\]?(?:\|[^!]*)?!', '', text)
    text = re.sub(r'!\S+!', '', text)

    # Satır satır işle
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Kod bloğu {code} ... {code}
        if re.match(r'\{code[^}]*\}', line, re.IGNORECASE):
            i += 1
            code_lines = []
            while i < len(lines) and not re.match(r'\{code\}', lines[i], re.IGNORECASE):
                code_lines.append(lines[i])
                i += 1
            widget.insert(tk.END, "\n".join(code_lines) + "\n", "code")
            i += 1
            continue

        # Tablo satırı ||...|| veya |...|
        if line.strip().startswith("||") or (line.strip().startswith("|") and line.strip().endswith("|")):
            is_header = line.strip().startswith("||")
            cells = re.split(r'\|\||\|', line.strip())
            cells = [c for c in cells if c != ""]
            tag = "table_header" if is_header else ("table_cell" if i % 2 == 0 else "table_alt")
            for j, cell in enumerate(cells):
                widget.insert(tk.END, f" {cell.strip()} ", tag)
                if j < len(cells) - 1:
                    widget.insert(tk.END, " │ ", tag)
            widget.insert(tk.END, "\n")
            i += 1
            continue

        # Başlıklar h1. h2. h3.
        m = re.match(r'^h([1-3])\.\s*(.*)', line)
        if m:
            tag = f"h{m.group(1)}"
            widget.insert(tk.END, m.group(2) + "\n", tag)
            i += 1
            continue

        # Liste öğeleri * - #
        m = re.match(r'^([*#\-]+)\s+(.*)', line)
        if m:
            prefix = "• " if m.group(1)[0] in "*-" else f"{i}. "
            _insert_inline(widget, prefix + m.group(2) + "\n", "bullet")
            i += 1
            continue

        # Normal satır — inline markup işle
        _insert_inline(widget, line + "\n")
        i += 1


def _insert_inline(widget, text, base_tag=None):
    """Satır içi markup'ı (bold, italic, link vb.) parse edip ekler"""
    import re, webbrowser

    # Token pattern: bold, italic, underline, strike, monospace, link, plain
    pattern = re.compile(
        r'\*([^*]+)\*'           # *bold*
        r'|_([^_]+)_'            # _italic_
        r'|\+([^+]+)\+'          # +underline+
        r'|-([^-]+)-'            # -strike-
        r'|\{\{([^}]+)\}\}'      # {{monospace}}
        r'|\[([^\|]+)\|([^\]]+)\]'  # [text|url]
        r'|\[~([^\]]+)\]'        # [~username]
    )

    pos = 0
    for m in pattern.finditer(text):
        # Önceki düz metin
        if m.start() > pos:
            tags = (base_tag,) if base_tag else ()
            widget.insert(tk.END, text[pos:m.start()], tags)

        if m.group(1) is not None:
            tags = ("bold", base_tag) if base_tag else ("bold",)
            widget.insert(tk.END, m.group(1), tags)
        elif m.group(2) is not None:
            tags = ("italic", base_tag) if base_tag else ("italic",)
            widget.insert(tk.END, m.group(2), tags)
        elif m.group(3) is not None:
            tags = ("underline", base_tag) if base_tag else ("underline",)
            widget.insert(tk.END, m.group(3), tags)
        elif m.group(4) is not None:
            tags = ("strike", base_tag) if base_tag else ("strike",)
            widget.insert(tk.END, m.group(4), tags)
        elif m.group(5) is not None:
            tags = ("code", base_tag) if base_tag else ("code",)
            widget.insert(tk.END, m.group(5), tags)
        elif m.group(6) is not None and m.group(7) is not None:
            link_text, url = m.group(6), m.group(7)
            tag_name = f"link_{widget.index(tk.END).replace('.', '_')}"
            widget.tag_configure(tag_name, foreground="#0078d7", underline=True)
            widget.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
            widget.tag_bind(tag_name, "<Enter>", lambda e: widget.configure(cursor="hand2"))
            widget.tag_bind(tag_name, "<Leave>", lambda e: widget.configure(cursor="arrow"))
            widget.insert(tk.END, link_text, (tag_name, "link"))
        elif m.group(8) is not None:
            tags = ("bold", base_tag) if base_tag else ("bold",)
            widget.insert(tk.END, f"@{m.group(8)}", tags)

        pos = m.end()

    # Kalan düz metin
    if pos < len(text):
        tags = (base_tag,) if base_tag else ()
        widget.insert(tk.END, text[pos:], tags)


class IssueDetailDialog:
    """Issue detay penceresi — Detaylar / Yorumlar / Ekler tabları"""

    def __init__(self, parent, jira_client, issue_key, current_user=None, config_manager=None, issue_list=None):
        self.parent = parent
        self.jira_client = jira_client
        self.issue_key = issue_key
        self.current_user = current_user  # {"name": ..., "displayName": ...}
        self.current_user_name = (current_user or {}).get("name", "")
        self.config_manager = config_manager
        self._comments = []  # cache
        self._original_desc = ""  # ham markup
        self._assignee_name = ""  # Issue'nun atandığı kişinin kullanıcı adı
        self.issue_list = issue_list or []  # Tüm issue listesi
        self._current_index = 0

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Issue: {issue_key}")
        self.dialog.geometry("900x780")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())
        self.dialog.bind("<Left>", lambda e: self._prev_issue())
        self.dialog.bind("<Right>", lambda e: self._next_issue())

        self._create_widgets()
        self._load_all()

    # ------------------------------------------------------------------ UI --
    def _create_widgets(self):
        main = ttk.Frame(self.dialog, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Başlık satırı
        header_row = ttk.Frame(main)
        header_row.pack(fill=tk.X)
        self.lbl_key = ttk.Label(header_row, text="Yükleniyor…", font=("Segoe UI", 13, "bold"))
        self.lbl_key.pack(side=tk.LEFT)
        self.btn_nav_prev = ttk.Button(header_row, text="◀ Geri", command=self._prev_issue, width=8)
        self.btn_nav_prev.pack(side=tk.LEFT, padx=(15, 0))
        self.lbl_nav = ttk.Label(header_row, text="", font=("Segoe UI", 9))
        self.lbl_nav.pack(side=tk.LEFT, padx=5)
        self.btn_nav_next = ttk.Button(header_row, text="İleri ▶", command=self._next_issue, width=8)
        self.btn_nav_next.pack(side=tk.LEFT)
        ttk.Button(header_row, text="👤 Bana Ata", command=self._assign_to_me, width=12).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(header_row, text="👥 Ata", command=self._assign_from_dialog, width=10).pack(side=tk.RIGHT, padx=(5, 0))
        self.btn_update = ttk.Button(header_row, text="🔄 Güncelle", command=self._update_issue, width=12)
        self.btn_update.pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(header_row, text="🌐 Tarayıcıda Aç", command=self._open_in_browser).pack(side=tk.RIGHT)

        self.lbl_summary = ttk.Label(main, text="", font=("Segoe UI", 11), wraplength=820, justify=tk.LEFT)
        self.lbl_summary.pack(anchor=tk.W, pady=(2, 8))

        # Meta bilgiler (grid)
        meta = ttk.Frame(main)
        meta.pack(fill=tk.X, pady=(0, 8))
        labels = ["Status:", "Assignee:", "Reporter:", "Priority:", "Created:", "Updated:", "Components:", "Labels:"]
        self._meta_vars = {}
        for i, lbl in enumerate(labels):
            row, col = divmod(i, 2)
            ttk.Label(meta, text=lbl, font=("Segoe UI", 9, "bold")).grid(row=row, column=col*2, sticky=tk.W, padx=(0 if col==0 else 20, 4), pady=2)
            var = tk.StringVar()
            e = ttk.Entry(meta, textvariable=var, state="readonly", width=35, font=("Segoe UI", 9))
            e.grid(row=row, column=col*2+1, sticky=tk.W, pady=2)
            self._meta_vars[lbl] = var

        # Kapat — her zaman altta görünür
        ttk.Button(main, text="Kapat", command=self.dialog.destroy).pack(side=tk.BOTTOM, anchor=tk.E, pady=(6, 0))

        # Notebook
        self.nb = ttk.Notebook(main)
        self.nb.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        # --- Tab 1: Detaylar ---
        tab_detail = ttk.Frame(self.nb, padding=5)
        self.nb.add(tab_detail, text="  Detaylar  ")

        desc_header = ttk.Frame(tab_detail)
        desc_header.pack(fill=tk.X)
        ttk.Label(desc_header, text="Açıklama", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.btn_edit_desc = ttk.Button(desc_header, text="Düzenle", width=10, command=self._start_edit_desc)
        self.btn_edit_desc.pack(side=tk.RIGHT)

        self.txt_desc = tk.Text(tab_detail, wrap=tk.WORD, font=("Segoe UI", 10), state=tk.DISABLED, cursor="arrow")
        sb = ttk.Scrollbar(tab_detail, command=self.txt_desc.yview)
        self.txt_desc.configure(yscrollcommand=sb.set)
        self.txt_desc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Tab 2: Yorumlar ---
        tab_comments = ttk.Frame(self.nb, padding=5)
        self.nb.add(tab_comments, text="  Yorumlar  ")
        self._build_comments_tab(tab_comments)

        # --- Tab 3: Linkli İşler ---
        tab_links = ttk.Frame(self.nb, padding=5)
        self.nb.add(tab_links, text="  Linkli İşler  ")
        self._build_links_tab(tab_links)

        # --- Tab 4: Ekler ---
        tab_attach = ttk.Frame(self.nb, padding=5)
        self.nb.add(tab_attach, text="  Dosya Ekleri  ")
        self._build_attachments_tab(tab_attach)

        # --- Tab 5: Bağlı Dosyalar ---
        tab_files = ttk.Frame(self.nb, padding=5)
        self.nb.add(tab_files, text="  Bağlı Dosyalar  ")
        self._build_linked_files_tab(tab_files)

        # --- Tab 6: Durum Güncelle ---
        tab_status = ttk.Frame(self.nb, padding=5)
        self.nb.add(tab_status, text="  Durum Güncelle  ")
        self._build_status_tab(tab_status)

    def _build_comments_tab(self, parent):
        # Yorum listesi
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.comments_canvas = tk.Canvas(list_frame, highlightthickness=0)
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.comments_canvas.yview)
        self.comments_canvas.configure(yscrollcommand=vsb.set)
        self.comments_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.comments_inner = ttk.Frame(self.comments_canvas)
        self._canvas_window = self.comments_canvas.create_window((0, 0), window=self.comments_inner, anchor="nw")
        self.comments_inner.bind("<Configure>", lambda e: self.comments_canvas.configure(
            scrollregion=self.comments_canvas.bbox("all")))
        self.comments_canvas.bind("<Configure>", lambda e: self.comments_canvas.itemconfig(
            self._canvas_window, width=e.width))

        # Yeni yorum alanı
        sep = ttk.Separator(parent, orient="horizontal")
        sep.pack(fill=tk.X, pady=6)
        ttk.Label(parent, text="Yeni Yorum", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.txt_new_comment = tk.Text(parent, height=4, wrap=tk.WORD, font=("Segoe UI", 10))
        self.txt_new_comment.pack(fill=tk.X)
        ttk.Button(parent, text="Gönder", command=self._add_comment).pack(anchor=tk.E, pady=(4, 0))

    def _build_links_tab(self, parent):
        self.links_frame = ttk.Frame(parent)
        self.links_frame.pack(fill=tk.BOTH, expand=True)

    def _build_attachments_tab(self, parent):
        cols = ("Dosya Adı", "Boyut", "Yükleyen", "Tarih")
        self.attach_tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        for col in cols:
            self.attach_tree.heading(col, text=col)
        self.attach_tree.column("Dosya Adı", width=300)
        self.attach_tree.column("Boyut", width=80, anchor="center")
        self.attach_tree.column("Yükleyen", width=150)
        self.attach_tree.column("Tarih", width=130, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.attach_tree.yview)
        self.attach_tree.configure(yscrollcommand=vsb.set)
        self.attach_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._attach_urls = {}  # item_id -> {filename, content_url, mime_type}
        self.attach_tree.bind("<Double-1>", self._open_attachment)

    def _build_linked_files_tab(self, parent):
        """Bağlı dosyalar tab'ı - 19-20 karakterli, 20 ile başlayan dosya numaralarını bulur"""
        self.files_frame = ttk.Frame(parent)
        self.files_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.files_frame, text="İş veya yorum içinde geçen dosya numaraları", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

    def _find_and_show_linked_files(self, issue):
        """Dosya numaralarını bul ve butonları göster"""
        import re
        import webbrowser
        
        # Frame içini temizle
        for w in self.files_frame.winfo_children():
            w.destroy()
        
        # Issue description ve summary'den bul
        fields = issue.get("fields", {})
        text_parts = []
        
        summary = fields.get("summary", "") or ""
        description = fields.get("description", "") or ""
        
        text_parts.append(summary)
        text_parts.append(description)
        
        # Yorumlardan bul
        for comment in self._comments:
            body = comment.get("body", "") or ""
            text_parts.append(body)
        
        all_text = " ".join(str(t) for t in text_parts)
        
        found_items = []
        
        # 1. Jira link formatı: [numara|url]
        link_pattern = r'\[([^\]|]+)\|([^\]]+)\]'
        for label, url in re.findall(link_pattern, all_text):
            if "10.251.63.185" in url or "evdo" in url:
                found_items.append((label.strip(), url))
        
        # 2. TCKN: tc: 16150436736 (11 haneli)
        tckn_pattern = r'tc:\s*(\d{11})'
        for match in re.finditer(tckn_pattern, all_text, re.IGNORECASE):
            tckn = match.group(1)
            url = f"http://10.251.63.185/evdo/TakipGoruntule2.php?tckn={tckn}&opcode=TCKNSORGULA"
            found_items.append((f"TC: {tckn}", url))
        
        # 3. Hasar Belgesi: hb: 2024011164Elh0000014 (2024 ile başlayan, harf ve rakam içeren)
        hb_pattern = r'hb:\s*(\d{4}\d*[A-Za-z]\w+)'
        for match in re.finditer(hb_pattern, all_text, re.IGNORECASE):
            hb = match.group(1)
            url = f"http://10.251.63.185/evdo/TakipGoruntule2.php?vd=&ozelbelgeno={hb}&opcode=Serbest+Sorgula"
            found_items.append((f"HB: {hb}", url))
        
        if not found_items:
            ttk.Label(self.files_frame, text="Dosya numarası bulunamadı", foreground="#888").pack(anchor=tk.W, pady=10)
            return
        
        ttk.Label(self.files_frame, text=f"Bulunan dosya sayısı: {len(found_items)}", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(0, 5))
        
        for label, url in found_items:
            btn = ttk.Button(self.files_frame, text=f"📄 {label}", command=lambda u=url: webbrowser.open(u))
            btn.pack(anchor=tk.W, pady=2, fill=tk.X)

    def _build_status_tab(self, parent):
        ttk.Label(parent, text="Durum Değiştir:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        self.status_listbox = tk.Listbox(parent, font=("Segoe UI", 10), height=10)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.status_listbox.yview)
        self.status_listbox.configure(yscrollcommand=vsb.set)
        self.status_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        
        self._transitions = {}  # display_name -> id
        
        ttk.Button(parent, text="Değiştir", command=self._change_status).pack(anchor=tk.E, pady=(10, 0))

    # --------------------------------------------------------------- Load --
    def _load_all(self):
        def fetch():
            issue = self.jira_client.get_issue(self.issue_key)
            comments_resp = self.jira_client.get_issue_comments(self.issue_key)
            attachments = self.jira_client.get_attachments(self.issue_key)
            transitions = self.jira_client.get_transitions(self.issue_key)
            links = self.jira_client.get_issue_links(self.issue_key)
            self.dialog.after(0, lambda: self._populate(issue, comments_resp, attachments, transitions, links))
        threading.Thread(target=fetch, daemon=True).start()

    def _populate(self, issue, comments_resp, attachments, transitions=None, links=None):
        if "error" in issue:
            self.lbl_key.config(text=f"Hata: {issue['error']}")
            return

        fields = issue.get("fields", {})

        self.lbl_key.config(text=self.issue_key)
        self.lbl_summary.config(text=fields.get("summary", ""))

        def fmt_date(d):
            return d[:19].replace("T", " ") if d else ""

        components = ", ".join(c.get("name", "") for c in fields.get("components", []))
        labels = ", ".join(fields.get("labels", []))

        self._meta_vars["Status:"].set(fields.get("status", {}).get("name", ""))
        self._meta_vars["Assignee:"].set((fields.get("assignee") or {}).get("displayName", ""))
        self._meta_vars["Reporter:"].set((fields.get("reporter") or {}).get("displayName", ""))
        self._meta_vars["Priority:"].set((fields.get("priority") or {}).get("name", ""))
        self._meta_vars["Created:"].set(fmt_date(fields.get("created", "")))
        self._meta_vars["Updated:"].set(fmt_date(fields.get("updated", "")))
        self._meta_vars["Components:"].set(components)
        self._meta_vars["Labels:"].set(labels)

        # Güncelle düğmesini göster/gizle
        self._assignee_name = (fields.get("assignee") or {}).get("name", "")
        if self._assignee_name and self.current_user_name and self._assignee_name == self.current_user_name:
            self.btn_update.config(state=tk.NORMAL)
        else:
            self.btn_update.config(state=tk.DISABLED)

        # Açıklama
        self._original_desc = fields.get("description", "") or ""
        self.txt_desc.configure(state=tk.NORMAL)
        render_jira_markup(self.txt_desc, self._original_desc)
        self.txt_desc.configure(state=tk.DISABLED)

        # Yorumlar
        self._comments = []
        if "error" not in comments_resp:
            self._comments = comments_resp.get("fields", {}).get("comment", {}).get("comments", [])
        self._render_comments()

        # Bağlı dosyaları bul ve göster
        self._find_and_show_linked_files(issue)

        # Ekler
        for row in self.attach_tree.get_children():
            self.attach_tree.delete(row)
        self._attach_urls.clear()
        if isinstance(attachments, list):
            for a in attachments:
                size_kb = f"{a.get('size', 0) // 1024} KB"
                author = (a.get("author") or {}).get("displayName", "")
                created = fmt_date(a.get("created", ""))
                iid = self.attach_tree.insert("", tk.END, values=(a.get("filename", ""), size_kb, author, created))
                self._attach_urls[iid] = {
                    "filename": a.get("filename", ""),
                    "url": a.get("content", ""),
                    "mime": a.get("mimeType", "")
                }

        # Transitions (Durum Değişiklikleri)
        self.status_listbox.delete(0, tk.END)
        self._transitions.clear()
        if transitions and "error" not in transitions:
            for t in transitions.get("transitions", []):
                name = t.get("name", "")
                tid = t.get("id", "")
                self.status_listbox.insert(tk.END, name)
                self._transitions[name] = tid

        # Linkli İşler
        for w in self.links_frame.winfo_children():
            w.destroy()
        
        # Epic'leri ve diğer linkli issue'ları ayır
        epics = []
        other_links = []
        
        if links:
            for link in links:
                link_type = link.get("type", {}).get("name", "").lower()
                inward = link.get("inwardIssue")
                outward = link.get("outwardIssue")
                
                # Epic linklerini ayır
                if "epic" in link_type:
                    if inward:
                        epics.append((inward.get("key", ""), inward.get("fields", {}).get("summary", "")))
                    if outward:
                        epics.append((outward.get("key", ""), outward.get("fields", {}).get("summary", "")))
                else:
                    if inward:
                        other_links.append((link_type, "←", inward.get("key", ""), inward.get("fields", {}).get("summary", "")))
                    if outward:
                        other_links.append((link_type, "→", outward.get("key", ""), outward.get("fields", {}).get("summary", "")))
        
        # Epic Başlığı
        if epics:
            ttk.Label(self.links_frame, text="📋 Epic:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(5, 2))
            for epic_key, epic_summary in epics:
                btn = ttk.Button(self.links_frame, text=f"{epic_key} - {epic_summary}",
                               command=lambda k=epic_key: self._open_linked_issue(k))
                btn.pack(fill=tk.X, pady=2, padx=(20, 0))
        
        # Linkli İşler Başlığı
        if other_links:
            ttk.Label(self.links_frame, text="🔗 Linkli İşler:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))
            for link_type, direction, issue_key, summary in other_links:
                btn = ttk.Button(self.links_frame, text=f"{direction} {link_type}: {issue_key} - {summary}",
                               command=lambda k=issue_key: self._open_linked_issue(k))
                btn.pack(fill=tk.X, pady=2)

    def _render_comments(self):
        for w in self.comments_inner.winfo_children():
            w.destroy()

        current_account = (self.current_user or {}).get("accountId", "")

        for c in self._comments:
            cid = c.get("id", "")
            author = (c.get("author") or {}).get("displayName", "")
            author_id = (c.get("author") or {}).get("accountId", "")
            created = c.get("created", "")[:19].replace("T", " ")

            frame = ttk.Frame(self.comments_inner, relief="groove", padding=6)
            frame.pack(fill=tk.X, padx=4, pady=4)

            header = ttk.Frame(frame)
            header.pack(fill=tk.X)
            ttk.Label(header, text=author, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(header, text=f"  {created}", font=("Segoe UI", 8), foreground="#888").pack(side=tk.LEFT)

            txt = tk.Text(frame, wrap=tk.WORD, font=("Segoe UI", 10), height=max(3, (c.get("body") or "").count("\n")+2),
                          state=tk.NORMAL, cursor="arrow", relief="flat", background="#f9f9f9")
            txt.pack(fill=tk.X, pady=(4, 0))
            render_jira_markup(txt, c.get("body", "") or "")
            txt.configure(state=tk.DISABLED)

            # Sadece kendi yorumunu düzenleyebilir
            if author_id == current_account:
                ttk.Button(frame, text="Düzenle", width=8,
                           command=lambda t=txt, ci=cid, b=c.get("body",""): self._edit_comment(t, ci, b)).pack(anchor=tk.E, pady=(4, 0))

    def _edit_comment(self, txt_widget, comment_id, original_body):
        """Yorumu düzenlenebilir yap — ham Jira markup ile"""
        # Rendered içeriği temizle, ham markup'ı yaz
        txt_widget.configure(state=tk.NORMAL, background="white", cursor="xterm")
        txt_widget.delete("1.0", tk.END)
        txt_widget.insert("1.0", original_body)

        btn_frame = txt_widget.master.winfo_children()[-1]  # Düzenle butonu
        btn_frame.destroy()

        actions = ttk.Frame(txt_widget.master)
        actions.pack(anchor=tk.E, pady=(4, 0))

        def save():
            new_body = txt_widget.get("1.0", tk.END).strip()
            def do_update():
                result = self.jira_client.update_comment(self.issue_key, comment_id, new_body)
                if "error" in result:
                    self.dialog.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.dialog))
                else:
                    self.dialog.after(0, self._reload_comments)
            threading.Thread(target=do_update, daemon=True).start()

        def cancel():
            actions.destroy()
            txt_widget.configure(state=tk.NORMAL)
            render_jira_markup(txt_widget, original_body)
            txt_widget.configure(state=tk.DISABLED, background="#f9f9f9", cursor="arrow")
            ttk.Button(txt_widget.master, text="Düzenle", width=8,
                       command=lambda: self._edit_comment(txt_widget, comment_id, original_body)).pack(anchor=tk.E, pady=(4, 0))

        ttk.Button(actions, text="Kaydet", width=8, command=save).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(actions, text="İptal", width=8, command=cancel).pack(side=tk.LEFT)

    def _add_comment(self):
        body = self.txt_new_comment.get("1.0", tk.END).strip()
        if not body:
            return
        self.txt_new_comment.configure(state=tk.DISABLED)

        def do_add():
            result = self.jira_client.add_comment(self.issue_key, body)
            if "error" in result:
                self.dialog.after(0, lambda: (
                    messagebox.showerror("Hata", result["error"], parent=self.dialog),
                    self.txt_new_comment.configure(state=tk.NORMAL)
                ))
            else:
                self.dialog.after(0, lambda: (
                    self.txt_new_comment.delete("1.0", tk.END),
                    self.txt_new_comment.configure(state=tk.NORMAL),
                    self._reload_comments()
                ))
        threading.Thread(target=do_add, daemon=True).start()

    def _reload_comments(self):
        def fetch():
            resp = self.jira_client.get_issue_comments(self.issue_key)
            self._comments = resp.get("fields", {}).get("comment", {}).get("comments", []) if "error" not in resp else []
            self.dialog.after(0, self._render_comments)
        threading.Thread(target=fetch, daemon=True).start()

    def _open_in_browser(self):
        import webbrowser
        url = f"{self.jira_client.server_url}/browse/{self.issue_key}"
        webbrowser.open(url)

    def _prev_issue(self):
        """Önceki issue'ya git"""
        if not self.issue_list:
            return
        # Mevcut indexi bul
        keys = [i.get("key", "") for i in self.issue_list]
        try:
            self._current_index = keys.index(self.issue_key)
        except ValueError:
            self._current_index = 0
        # Öncekiye git
        if self._current_index > 0:
            self._current_index -= 1
            self._navigate_to(self.issue_list[self._current_index].get("key", ""))

    def _next_issue(self):
        """Sonraki issue'ya git"""
        if not self.issue_list:
            return
        # Mevcut indexi bul
        keys = [i.get("key", "") for i in self.issue_list]
        try:
            self._current_index = keys.index(self.issue_key)
        except ValueError:
            self._current_index = 0
        # Sonrakiye git
        if self._current_index < len(self.issue_list) - 1:
            self._current_index += 1
            self._navigate_to(self.issue_list[self._current_index].get("key", ""))

    def _navigate_to(self, issue_key):
        """Belirtilen issue'ya git"""
        if not issue_key:
            return
        # Mevcut tab'ı kaydet
        current_tab = self.nb.index(self.nb.select())
        
        self.issue_key = issue_key
        self.dialog.title(f"Issue: {issue_key}")
        self._load_all()
        self._update_nav_buttons()
        
        # Aynı tab'a geri dön
        self.nb.select(current_tab)

    def _update_nav_buttons(self):
        """Navigasyon butonlarını güncelle"""
        if not self.issue_list:
            self.btn_nav_prev.config(state=tk.DISABLED)
            self.btn_nav_next.config(state=tk.DISABLED)
            self.lbl_nav.config(text="")
            return
        keys = [i.get("key", "") for i in self.issue_list]
        try:
            idx = keys.index(self.issue_key)
        except ValueError:
            idx = 0
        total = len(self.issue_list)
        self.lbl_nav.config(text=f"{idx + 1} / {total}")
        self.btn_nav_prev.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        self.btn_nav_next.config(state=tk.NORMAL if idx < total - 1 else tk.DISABLED)

    def _open_linked_issue(self, issue_key):
        """Linkli issue'yu aç"""
        IssueDetailDialog(self.parent, self.jira_client, issue_key, current_user=self.current_user, config_manager=self.config_manager)

    def _assign_to_me(self):
        """Issue'yu bağlı kullanıcıya ata"""
        if not self.current_user:
            messagebox.showwarning("Hata", "Kullanıcı bilgisi bulunamadı", parent=self.dialog)
            return
        
        username = self.current_user.get("name") or self.current_user.get("displayName", "")
        if not username:
            messagebox.showwarning("Hata", "Kullanıcı adı alınamadı", parent=self.dialog)
            return

        if not messagebox.askyesno("Atama Onayı",
                f"{self.issue_key} işi\n\n{username}\n\nkullanıcısına (sana) atanacak. Onaylıyor musunuz?",
                parent=self.dialog):
            return

        def do():
            result = self.jira_client.assign_issue(self.issue_key, username)
            if "error" in result:
                self.dialog.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.dialog))
            else:
                self.dialog.after(0, lambda: messagebox.showinfo("Başarılı",
                    f"{self.issue_key} → {username} atandı.", parent=self.dialog))
        
        threading.Thread(target=do, daemon=True).start()

    def _update_issue(self):
        """Issue'yu güncelle (sadece kendi işleri için)"""
        if not messagebox.askyesno("Güncelleme Onayı",
                f"{self.issue_key} işi güncellenecek. Onaylıyor musunuz?",
                parent=self.dialog):
            return

        def do():
            result = self.jira_client.get_issue(self.issue_key)
            if "error" in result:
                self.dialog.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.dialog))
            else:
                self.dialog.after(0, lambda: messagebox.showinfo("Başarılı",
                    f"{self.issue_key} güncellenmiştir.", parent=self.dialog))
        
        threading.Thread(target=do, daemon=True).start()

    def _change_status(self):
        """Durum değiştir"""
        sel = self.status_listbox.curselection()
        if not sel:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen bir durum seçin.", parent=self.dialog)
            return
        
        status_name = self.status_listbox.get(sel[0])
        transition_id = self._transitions.get(status_name)
        
        if not messagebox.askyesno("Durum Değişikliği Onayı",
                f"{self.issue_key} işinin durumu\n\n{status_name}\n\nolarak değiştirilecek. Onaylıyor musunuz?",
                parent=self.dialog):
            return

        def do():
            result = self.jira_client.transition_issue(self.issue_key, transition_id)
            if "error" in result:
                self.dialog.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.dialog))
            else:
                self.dialog.after(0, lambda: messagebox.showinfo("Başarılı",
                    f"{self.issue_key} durumu {status_name} olarak değiştirildi.", parent=self.dialog))
        
        threading.Thread(target=do, daemon=True).start()

    def _assign_from_dialog(self):
        """Dialog içinden issue ata"""
        if not self.config_manager:
            messagebox.showwarning("Hata", "Config manager bulunamadı", parent=self.dialog)
            return
        
        users = [u.strip() for u in self.config_manager.get("default_users", "").split(",") if u.strip()]
        if not users:
            messagebox.showwarning("Kullanıcı Listesi Boş",
                "Ayarlar > Filtreler bölümünde varsayılan kullanıcılar ekleyin.", parent=self.dialog)
            return

        # Kullanıcı seçme dialog'u
        win = tk.Toplevel(self.dialog)
        win.title("Kullanıcı Seç")
        win.geometry("300x400")
        win.transient(self.dialog)
        win.grab_set()

        ttk.Label(win, text="Atanacak Kullanıcı:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))

        listbox = tk.Listbox(win, font=("Segoe UI", 10), height=15)
        vsb = ttk.Scrollbar(win, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=vsb.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        vsb.pack(side=tk.LEFT, fill=tk.Y)

        for u in users:
            listbox.insert(tk.END, u)

        def assign_selected():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Seçim Yapılmadı", "Lütfen bir kullanıcı seçin.", parent=win)
                return
            
            selected_user = users[sel[0]]
            win.destroy()

            if not messagebox.askyesno("Atama Onayı",
                    f"{self.issue_key} işi\n\n{selected_user}\n\nkullanıcısına atanacak. Onaylıyor musunuz?",
                    parent=self.dialog):
                return

            def do():
                result = self.jira_client.assign_issue(self.issue_key, selected_user)
                if "error" in result:
                    self.dialog.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.dialog))
                else:
                    self.dialog.after(0, lambda: messagebox.showinfo("Başarılı",
                        f"{self.issue_key} → {selected_user} atandı.", parent=self.dialog))
            
            threading.Thread(target=do, daemon=True).start()

        ttk.Button(win, text="Ata", command=assign_selected).pack(pady=10)


    def _start_edit_desc(self):
        """Açıklamayı düzenleme moduna al"""
        self.txt_desc.configure(state=tk.NORMAL, cursor="xterm", background="white")
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", self._original_desc)
        self.btn_edit_desc.configure(text="Kaydet", command=self._save_desc)
        # İptal butonu ekle
        self._btn_cancel_desc = ttk.Button(
            self.btn_edit_desc.master, text="İptal", width=8, command=self._cancel_edit_desc)
        self._btn_cancel_desc.pack(side=tk.RIGHT, padx=(0, 4))

    def _cancel_edit_desc(self):
        self._btn_cancel_desc.destroy()
        self.btn_edit_desc.configure(text="Düzenle", command=self._start_edit_desc)
        self.txt_desc.configure(state=tk.NORMAL)
        render_jira_markup(self.txt_desc, self._original_desc)
        self.txt_desc.configure(state=tk.DISABLED, cursor="arrow", background="white")

    def _save_desc(self):
        new_body = self.txt_desc.get("1.0", tk.END).rstrip("\n")
        if new_body == self._original_desc:
            self._cancel_edit_desc()
            return
        self._show_diff_dialog(self._original_desc, new_body)

    def _show_diff_dialog(self, old, new):
        """Diff göster ve onaylatır"""
        import difflib
        diff = list(difflib.unified_diff(
            old.splitlines(), new.splitlines(),
            lineterm="", fromfile="Mevcut", tofile="Yeni"
        ))

        win = tk.Toplevel(self.dialog)
        win.title("Değişiklikleri Onayla")
        win.geometry("800x500")
        win.transient(self.dialog)
        win.grab_set()

        ttk.Label(win, text="Aşağıdaki değişiklikler kaydedilecek. Onaylıyor musunuz?",
                  font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=(10, 5))

        txt = tk.Text(win, font=("Courier New", 9), wrap=tk.NONE)
        vsb = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
        hsb = ttk.Scrollbar(win, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        txt.tag_configure("add", background="#ccffcc", foreground="#006600")
        txt.tag_configure("remove", background="#ffcccc", foreground="#cc0000")
        txt.tag_configure("meta", foreground="#888888")

        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                txt.insert(tk.END, line + "\n", "add")
            elif line.startswith("-") and not line.startswith("---"):
                txt.insert(tk.END, line + "\n", "remove")
            else:
                txt.insert(tk.END, line + "\n", "meta")

        txt.configure(state=tk.DISABLED)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True, padx=10)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=10, pady=8)

        def confirm():
            win.destroy()
            self._do_update_desc(new)

        ttk.Button(btn_frame, text="✔ Onayla ve Kaydet", command=confirm).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="İptal", command=win.destroy).pack(side=tk.RIGHT)

    def _do_update_desc(self, new_body):
        def do():
            result = self.jira_client.update_issue_description(self.issue_key, new_body)
            if "error" in result:
                self.dialog.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.dialog))
            else:
                self._original_desc = new_body
                self.dialog.after(0, lambda: (
                    self._btn_cancel_desc.destroy() if hasattr(self, "_btn_cancel_desc") and self._btn_cancel_desc.winfo_exists() else None,
                    self.btn_edit_desc.configure(text="Düzenle", command=self._start_edit_desc),
                    render_jira_markup(self.txt_desc, self._original_desc) or
                    self.txt_desc.configure(state=tk.DISABLED, cursor="arrow")
                ))
        threading.Thread(target=do, daemon=True).start()

    def _open_attachment(self, event):
        """Eke çift tıklanınca aç veya indir"""
        import tempfile, webbrowser, subprocess, sys
        sel = self.attach_tree.selection()
        if not sel:
            return
        info = self._attach_urls.get(sel[0])
        if not info or not info["url"]:
            return

        filename = info["filename"]
        url = info["url"]
        mime = info["mime"].lower()
        ext = os.path.splitext(filename)[1].lower()

        # Görüntülenebilir türler
        VIEWABLE = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg",
                    ".txt", ".log", ".xml", ".json", ".html", ".htm",
                    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}

        def do_open():
            tmp_dir = tempfile.mkdtemp()
            dest = os.path.join(tmp_dir, filename)
            err = self.jira_client.download_attachment(url, dest)
            if err:
                self.dialog.after(0, lambda: messagebox.showerror("İndirme Hatası", err, parent=self.dialog))
                return

            if ext in VIEWABLE:
                # OS varsayılan uygulamasıyla aç
                self.dialog.after(0, lambda: _open_file(dest))
            else:
                # İndir — kullanıcıya kayıt yeri sor
                from tkinter import filedialog
                def ask_save():
                    save_path = filedialog.asksaveasfilename(
                        parent=self.dialog,
                        initialfile=filename,
                        title="Dosyayı Kaydet"
                    )
                    if save_path:
                        import shutil
                        shutil.copy2(dest, save_path)
                        messagebox.showinfo("İndirildi", f"Dosya kaydedildi:\n{save_path}", parent=self.dialog)
                self.dialog.after(0, ask_save)

        threading.Thread(target=do_open, daemon=True).start()


def _open_file(path):
    """OS'a göre dosyayı varsayılan uygulamayla aç"""
    import subprocess, sys
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        messagebox.showerror("Açma Hatası", str(e))


class JiraMonitorApp:
    """Ana uygulama sınıfı"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"Jira Monitor v{__version__}")
        self.root.geometry("1400x800")
        # Tam ekran — OS'a göre
        import sys
        if sys.platform == "win32":
            self.root.state('zoomed')
        else:
            self.root.state('normal')
            self.root.attributes('-zoomed', True)
        
        # Modern stil ayarları
        self._setup_styles()
        
        self.config_manager = ConfigManager()
        self.jira_client = None
        self._current_user = None
        self.refresh_interval = 120
        self.last_update = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.issues = []
        self.refresh_thread = None
        self.is_running = True
        self._first_load = True  # İlk yükleme flag'i
        self._filter_changed = False  # Filtre değişikliği flag'i
        
        self._setup_ui()
        self._connect_jira()
        if self.jira_client:
            self._load_issues()
        self._start_refresh()
    
    def _setup_styles(self):
        """Modern stil ayarları"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Genel font
        style.configure('.', font=('Segoe UI', 10))
        
        # Treeview stil
        style.configure('Treeview', 
            font=('Segoe UI', 10),
            rowheight=28,
            background='white',
            fieldbackground='white',
            selectbackground='#0078d7',
            selectforeground='white'
        )
        style.configure('Treeview.Heading',
            font=('Segoe UI', 10, 'bold'),
            background='#e0e0e0',
            relief='flat'
        )
        style.map('Treeview.Heading',
            background=[('active', '#d0d0d0')]
        )
        
        # Frame stilleri
        style.configure('Card.TFrame', background='white')
        
        # Label stilleri
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#0078d7')
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11), foreground='#666666')
    
    def _setup_ui(self):
        """UI kurulumu"""
        # Ana arka plan
        self.root.configure(background='#f0f0f0')
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayarlar", menu=settings_menu)
        settings_menu.add_command(label="Yapılandırma", command=self._show_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Çıkış", command=self._exit)
        
        # Ana container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Başlık
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="Jira Issue Monitor", style='Title.TLabel').pack(side=tk.LEFT)
        self.lbl_count = ttk.Label(header_frame, text="0 issue", style='Subtitle.TLabel')
        self.lbl_count.pack(side=tk.RIGHT, padx=20)
        
        # Filter frame
        filter_frame = ttk.LabelFrame(main_container, text="Filtreler", padding="12")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter içeriği
        filter_content = ttk.Frame(filter_frame)
        filter_content.pack(fill=tk.X)
        
        # User filter
        ttk.Label(filter_content, text="Kullanıcı:").pack(side=tk.LEFT, padx=(0, 5))
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(filter_content, textvariable=self.user_var, width=22, state='readonly')
        self.user_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.user_combo.bind('<<ComboboxSelected>>', lambda e: self._on_filter_change())
        
        # Project filter
        ttk.Label(filter_content, text="Proje:").pack(side=tk.LEFT, padx=(0, 5))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(filter_content, textvariable=self.project_var, width=15, state='readonly')
        self.project_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.project_combo.bind('<<ComboboxSelected>>', lambda e: self._on_filter_change())
        
        # Status filter
        ttk.Label(filter_content, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(filter_content, textvariable=self.status_var, width=18, state='readonly')
        self.status_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.status_combo.bind('<<ComboboxSelected>>', lambda e: self._on_filter_change())
        
        # Buttons
        btn_frame = ttk.Frame(filter_content)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, text="🔄 Yenile", command=self._load_issues, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⚙️ Ayarlar", command=self._show_settings, width=12).pack(side=tk.LEFT, padx=5)
        
        # Treeview container
        tree_container = ttk.Frame(main_container)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Summary arama alanı
        search_frame = ttk.Frame(tree_container)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="🔍 Summary'de ara:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_tree)
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT)
        ttk.Button(search_frame, text="Temizle", command=lambda: self.search_var.set("")).pack(side=tk.LEFT, padx=5)
        
        # Treeview ve scrollbar'lar için ayrı frame (grid kullanacak)
        self.tree_inner = ttk.Frame(tree_container)
        self.tree_inner.pack(fill=tk.BOTH, expand=True)
        
        columns = ("#", "Key", "Summary", "Status", "Assignee", "Reporter", "Project", "Updated", "Geçen Süre", "Ata")
        self.tree = ttk.Treeview(self.tree_inner, columns=columns, show='headings', selectmode='browse')
        
        self.tree.heading("#", text="#")
        self.tree.heading("Key", text="Key")
        self.tree.heading("Summary", text="Summary")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Assignee", text="Assignee")
        self.tree.heading("Reporter", text="Reporter")
        self.tree.heading("Project", text="Project")
        self.tree.heading("Updated", text="Updated")
        self.tree.heading("Geçen Süre", text="Geçen Süre")
        self.tree.heading("Ata", text="İş Ata")
        
        self.tree.column("#", width=40, anchor='center')
        self.tree.column("Key", width=90, anchor='center')
        self.tree.column("Summary", width=250)
        self.tree.column("Status", width=100, anchor='center')
        self.tree.column("Assignee", width=120)
        self.tree.column("Reporter", width=120)
        self.tree.column("Project", width=80, anchor='center')
        self.tree.column("Updated", width=130, anchor='center')
        self.tree.column("Geçen Süre", width=100, anchor='center')
        self.tree.column("Ata", width=140, anchor='center')
        
        # Kaydedilmiş column genişliklerini yükle
        saved_widths = self.config_manager.get("column_widths", {})
        for col, width in saved_widths.items():
            try:
                self.tree.column(col, width=width)
            except:
                pass
        
        # Column genişliklerini düzenli kontrol et ve kaydet
        def check_and_save():
            self._save_column_widths()
            self.root.after(1000, check_and_save)
        self.root.after(1000, check_and_save)
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.tree_inner, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_inner, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        self.tree_inner.grid_columnconfigure(0, weight=1)
        self.tree_inner.grid_rowconfigure(0, weight=1)
        
        # Double click to view details
        self.tree.bind('<Double-1>', self._show_issue_details)
        # Ata kolonu tıklama
        self.tree.bind('<Button-1>', self._on_tree_click)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Hazır", relief=tk.SUNKEN, anchor=tk.W, padding=(10, 5))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _connect_jira(self):
        """Jira'ya bağlan"""
        server_url = self.config_manager.get("server_url", "").strip()
        username = self.config_manager.get("username", "").strip()
        api_token = self.config_manager.get("api_token", "").strip()
        
        errors = []
        if not server_url:
            errors.append("• Sunucu URL'si boş")
        elif not server_url.startswith("http"):
            errors.append("• URL 'http' veya 'https' ile başlamalı")
        if not username:
            errors.append("• Kullanıcı adı boş")
        if not api_token:
            errors.append("• API Token boş")
        
        if errors:
            messagebox.showwarning(
                "Eksik/Yanlış Bilgi",
                "Lütfen aşağıdaki sorunları düzeltin:\n\n" + "\n".join(errors) +
                "\n\nAyarlar menüsünden yapılandırmayı güncelleyin."
            )
            return False
        
        try:
            client = JiraClient(server_url, username, api_token)
            test_result = client.search_issues("project is not EMPTY", max_results=1)
            if "error" in test_result:
                messagebox.showerror(
                    "Bağlantı Hatası",
                    f"Jira sunucusuna bağlanılamadı:\n\n{test_result['error']}\n\n"
                    "Lütfen URL ve token bilgilerini kontrol edin."
                )
                return False
            self.jira_client = client
            self._current_user = client.get_current_user()
            self._populate_filters()
            return True
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası", f"Beklenmeyen hata oluştu:\n\n{str(e)}")
            return False

    def _populate_filters(self):
        """Filtre combobox'larını doldur"""
        users = [""] + [u.strip() for u in self.config_manager.get("default_users", "").split(",") if u.strip()]
        extra_projects = [p.strip() for p in self.config_manager.get("extra_projects", "").split(",") if p.strip()]
        extra_statuses = [s.strip().strip("'") for s in self.config_manager.get("extra_statuses", "").split(",") if s.strip()]
        self.user_combo['values'] = users
        self.project_combo['values'] = [""] + extra_projects
        self.status_combo['values'] = [""] + extra_statuses
    
    def _calculate_elapsed_time(self, updated_str):
        """Geçen süreyi insan anlayacağı dilde hesapla"""
        if not updated_str:
            return "-"
        
        try:
            updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            now = datetime.now(updated.tzinfo) if updated.tzinfo else datetime.now()
            delta = now - updated
            
            seconds = int(delta.total_seconds())
            
            if seconds < 60:
                return f"{seconds}s"
            elif seconds < 3600:
                return f"{seconds // 60}m"
            elif seconds < 86400:
                return f"{seconds // 3600}h"
            else:
                return f"{seconds // 86400}g"
        except:
            return "-"
    
    def _load_issues(self):
        """Issue'leri yükle"""
        if not self.jira_client:
            if not self._connect_jira():
                return
        
        # Get filter values
        user = self.user_var.get().strip()
        project = self.project_var.get().strip()
        status = self.status_var.get().strip()
        
        # Build JQL
        jql_parts = []
        
        # Users
        users = self.config_manager.get("default_users", "")
        if user:
            users = user
        if users:
            users_list = [u.strip() for u in users.split(",") if u.strip()]
            if users_list:
                users_str = ",".join([f'"{u}"' for u in users_list])
                jql_parts.append(f"assignee in ({users_str})")
        
        # Projects
        projects = self.config_manager.get("default_projects", "")
        if project:
            projects = project
        if projects:
            projects_list = [p.strip() for p in projects.split(",") if p.strip()]
            if projects_list:
                projects_str = ",".join([f'"{p}"' for p in projects_list])
                jql_parts.append(f"project in ({projects_str})")
        
        # Status
        default_status = self.config_manager.get("default_status", "")
        if status:
            default_status = status
        if default_status:
            jql_parts.append(f"status in ({default_status})")
        
        jql = " AND ".join(jql_parts)
        if not jql:
            jql = "project in (EVDBS) AND status in (OPEN, 'In Progress', Reopened)"
        
        jql += " ORDER BY updated DESC"
        
        # Show loading
        self.status_bar.config(text="Yükleniyor...")
        self.root.update()
        
        def load():
            result = self.jira_client.search_issues(jql)

            if "error" in result:
                self.root.after(0, lambda: self.status_bar.config(text=f"Hata: {result['error']}"))
                return

            issues = result.get("issues", [])
            
            # İlk yükleme veya filtre değişikliği değilse yeni issue'ları tespit et
            new_issues = []
            if not self._first_load and not self._filter_changed:
                old_keys = {i.get("key", "") for i in self.issues}
                new_issues = [i for i in issues if i.get("key", "") not in old_keys]
            
            self.issues = issues
            self._first_load = False  # İlk yükleme bitti
            self._filter_changed = False  # Filtre değişikliği bitti

            def update_ui():
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Sadece yeşil (today) satırlar için bildirim gönder
                today_issues = [i for i in new_issues if i.get("fields", {}).get("updated", "").startswith(datetime.now().strftime("%Y-%m-%d"))]
                if today_issues:
                    self._show_new_issue_notification(today_issues)

                for i, issue in enumerate(issues, 1):
                    fields = issue.get("fields", {})
                    key = issue.get("key", "")
                    summary = fields.get("summary", "")
                    status_name = fields.get("status", {}).get("name", "")
                    assignee = fields.get("assignee", {}).get("displayName", "")
                    reporter = fields.get("reporter", {}).get("displayName", "")
                    project_name = fields.get("project", {}).get("name", "")
                    updated = fields.get("updated", "")[:19].replace("T", " ") if fields.get("updated") else ""
                    
                    # Geçen süreyi hesapla
                    elapsed = self._calculate_elapsed_time(fields.get("updated", ""))

                    item_id = self.tree.insert("", tk.END, values=(
                        i, key, summary, status_name, assignee, reporter, project_name, updated, elapsed, "👤 Ata"
                    ))

                    tags = []
                    if project_name == "EVDBS":
                        tags.append('evdbs')
                    elif project_name == "EPDK":
                        tags.append('epdk')
                    elif project_name == "Yazılım Destek":
                        tags.append('destek')
                    if updated and updated.startswith(datetime.now().strftime("%Y-%m-%d")):
                        tags.append('today')
                    if tags:
                        self.tree.item(item_id, tags=tuple(tags))

                self.tree.tag_configure('evdbs', background='lightblue')
                self.tree.tag_configure('epdk', background='navajowhite')
                self.tree.tag_configure('destek', background='beige')
                self.tree.tag_configure('today', background='lightgreen')
                self.status_bar.config(text=f"{len(issues)} adet issue yüklendi. Son güncelleme: {datetime.now().strftime('%H:%M:%S')} | Sonraki yenileme: {self.config_manager.get('refresh_interval', 120)}s")

            self.root.after(0, update_ui)
        
        # Run in thread
        threading.Thread(target=load, daemon=True).start()
    
    def _show_issue_details(self, event):
        """Issue detayını göster"""
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        key = item['values'][1]
        if key:
            IssueDetailDialog(self.root, self.jira_client, key, current_user=self._current_user, config_manager=self.config_manager, issue_list=self.issues)

    def _filter_tree(self, *args):
        """Summary'de arama filtresi"""
        search_text = self.search_var.get().lower()
    def _filter_tree(self, *args):
        """Summary'de arama filtresi"""
        search_text = self.search_var.get().lower()
        
        # Mevcut tüm item'ları temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filtrele ve yeniden ekle
        for i, issue in enumerate(self.issues, 1):
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            
            # Filtrele
            if search_text and search_text not in summary.lower():
                continue
            
            key = issue.get("key", "")
            status_name = fields.get("status", {}).get("name", "")
            assignee = fields.get("assignee", {}).get("displayName", "")
            reporter = fields.get("reporter", {}).get("displayName", "")
            project_name = fields.get("project", {}).get("name", "")
            updated = fields.get("updated", "")[:19].replace("T", " ") if fields.get("updated") else ""
            elapsed = self._calculate_elapsed_time(fields.get("updated", ""))
            
            item_id = self.tree.insert("", tk.END, values=(
                i, key, summary, status_name, assignee, reporter, project_name, updated, elapsed, "👤 Ata"
            ))
            
            # Tag'leri ekle
            tags = []
            if project_name == "EVDBS":
                tags.append('evdbs')
            elif project_name == "EPDK":
                tags.append('epdk')
            elif project_name == "Yazılım Destek":
                tags.append('destek')
            if updated and updated.startswith(datetime.now().strftime("%Y-%m-%d")):
                tags.append('today')
            if tags:
                self.tree.item(item_id, tags=tuple(tags))

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        # "Ata" 9. kolon → #9
        if col != "#9":
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        key = values[1]
        self._assign_issue(key)

    def _save_column_widths(self):
        """Column genişliklerini kaydet"""
        columns = self.tree["columns"]
        widths = {}
        for col in columns:
            widths[col] = self.tree.column(col, "width")
        self.config_manager.set("column_widths", widths)
        # Debounce: sadece değişiklik olduysa kaydet
        current = self.config_manager.get("column_widths", {})
        if widths != current:
            self.config_manager.save_config(self.config_manager.config)

    def _assign_issue(self, issue_key):
        """Round-robin ile sıradaki kullanıcıya ata"""
        queue = self.config_manager.get("assign_queue", [])
        if not queue:
            messagebox.showwarning("Atama Kuyruğu Boş",
                "Ayarlar > Atama Kuyruğu bölümünden kullanıcı ekleyin.", parent=self.root)
            return

        idx = self.config_manager.get("assign_queue_index", 0) % len(queue)
        next_user = queue[idx]

        if not messagebox.askyesno("Atama Onayı",
                f"{issue_key} işi\n\n{next_user}\n\nkullanıcısına atanacak. Onaylıyor musunuz?",
                parent=self.root):
            return

        def do():
            result = self.jira_client.assign_issue(issue_key, next_user)
            if "error" in result:
                self.root.after(0, lambda: messagebox.showerror("Hata", result["error"], parent=self.root))
            else:
                new_idx = (idx + 1) % len(queue)
                self.config_manager.set("assign_queue_index", new_idx)
                self.config_manager.save_config(self.config_manager.config)
                self.root.after(0, lambda: (
                    self.status_bar.config(
                        text=f"{issue_key} → {next_user} atandı. Sıradaki: {queue[new_idx]}"),
                    self._load_issues()
                ))
        threading.Thread(target=do, daemon=True).start()
    
    def _on_filter_change(self):
        """Filtre değişikliği - bildirim verme"""
        self._filter_changed = True
        self._load_issues()
    
    def _show_settings(self):
        """Ayarları göster"""
        dialog = SettingsDialog(self.root, self.config_manager)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self._populate_filters()
            self._connect_jira()
            self._load_issues()
    
    def _show_new_issue_notification(self, new_issues):
        """Yeni issue bildirimi gonder"""
        if not self.config_manager.get("notifications_enabled", True):
            return

        issue_keys = ", ".join([i.get("key", "") for i in new_issues])
        title = f"Jira Monitor - {len(new_issues)} Yeni Issue"
        message = f"Yeni issue'lar yuklendi: {issue_keys}"

        send_notification(title, message)

    def _start_refresh(self):
        """Otomatik yenilemeyi başlat"""
        def refresh():
            while self.is_running:
                interval = self.config_manager.get("refresh_interval", 120)
                for remaining in range(interval, 0, -1):
                    if not self.is_running:
                        return
                    self.root.after(0, lambda r=remaining: self.status_bar.config(
                        text=f"Sonraki yenileme: {r}s"))
                    time.sleep(1)
                if self.is_running:
                    self.root.after(0, self._load_issues)
        
        self.refresh_thread = threading.Thread(target=refresh, daemon=True)
        self.refresh_thread.start()
    
    def _exit(self):
        """Çıkış"""
        self.is_running = False
        self.root.destroy()


def main():
    """Ana fonksiyon"""
    root = tk.Tk()
    app = JiraMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
