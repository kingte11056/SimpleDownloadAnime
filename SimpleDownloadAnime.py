import requests
import xml.etree.ElementTree as ET
from qbittorrentapi import Client
import os
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
import json
import urllib.parse
import datetime

# --- 设置默认值 ---
DEFAULT_QB_URL = 'http://127.0.0.1:8080'
DEFAULT_QB_USERNAME = 'admin'
DEFAULT_QB_PASSWORD = '1qaz2wsx'
CONFIG_FILE_NAME = "subscriptions.json"
DEFAULT_PROXY = "socks5h://127.0.0.1:10808"


# --- 数据持久化 ---
def load_config():
    if os.path.exists(CONFIG_FILE_NAME):
        try:
            with open(CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config):
    with open(CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def get_rss_data(rss_url, proxies):
    try:
        response = requests.get(rss_url, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response.text
    except:
        return None


class MikanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mikan Anime Downloader Pro")
        self.root.geometry("900x650")  # 稍微调宽一点点
        self.root.configure(bg="#f5f6f7")
        self.config = load_config()

        self.setup_styles()
        self.create_widgets()
        self.refresh_list()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", font=("Microsoft YaHei", 10), rowheight=35)
        self.style.map("Treeview", background=[('selected', '#0078d7')])

    def create_widgets(self):
        # --- 顶部重构：搜索添加区域 ---
        header = tk.Frame(self.root, bg="#ffffff", height=80, bd=0, highlightthickness=1, highlightbackground="#e0e0e0")
        header.pack(fill="x", side="top")

        tk.Label(header, text="Mikan 追番", bg="#ffffff", fg="#333", font=("Microsoft YaHei", 16, "bold")).pack(
            side="left", padx=(25, 15), pady=20)

        # 搜索输入框容器
        search_frame = tk.Frame(header, bg="#f1f3f4", padx=10, pady=5)
        search_frame.pack(side="left", padx=10)

        self.search_entry = tk.Entry(search_frame, font=("Microsoft YaHei", 11), width=35, bg="#f1f3f4", bd=0,
                                     highlightthickness=0)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.insert(0, "输入番剧名称直接订阅...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0,
                                                                               'end') if self.search_entry.get() == "输入番剧名称直接订阅..." else None)
        self.search_entry.bind("<Return>", lambda e: self.add_anime_from_input())

        btn_add_inline = tk.Button(header, text="快速订阅", command=self.add_anime_from_input, bg="#0078d7", fg="white",
                                   relief="flat", font=("Microsoft YaHei", 9, "bold"), padx=15, pady=5, cursor="hand2")
        btn_add_inline.pack(side="left", padx=10)

        # --- 主内容区 ---
        main_container = tk.Frame(self.root, bg="#f5f6f7")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 左侧列表
        left_frame = tk.Frame(main_container, bg="#f5f6f7")
        left_frame.pack(side="left", fill="both", expand=True)
        tk.Label(left_frame, text="已订阅番剧", bg="#f5f6f7", fg="#888", font=("Microsoft YaHei", 9, "bold")).pack(
            anchor="w", pady=(0, 8))

        tree_border = tk.Frame(left_frame, bg="#e0e0e0", padx=1, pady=1)
        tree_border.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_border, columns=("path"), show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # 右侧操作面板
        right_frame = tk.Frame(main_container, bg="#f5f6f7", width=280)
        right_frame.pack(side="right", fill="y", padx=(25, 0))
        right_frame.pack_propagate(False)

        detail_card = tk.Frame(right_frame, bg="#ffffff", bd=1, highlightthickness=1, highlightbackground="#e0e0e0")
        detail_card.pack(fill="x", pady=(0, 20))
        tk.Label(detail_card, text="订阅详情", bg="#ffffff", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=15,
                                                                                                    pady=10)
        self.info_label = tk.Label(detail_card, text="请在左侧选择番剧", bg="#ffffff", justify="left",
                                   font=("Microsoft YaHei", 9), fg="#999", wraplength=230)
        self.info_label.pack(padx=15, pady=(0, 15))

        btn_font = ("Microsoft YaHei", 10, "bold")
        # 主按钮：检查更新
        self.btn_check = tk.Button(right_frame, text="🔍 检查更新并下载", command=self.check_update, bg="#4CAF50", fg="white",
                                   relief="flat", font=btn_font, height=2, cursor="hand2")
        self.btn_check.pack(fill="x", pady=5)

        # 次要按钮：删除
        tk.Button(right_frame, text="🗑️ 删除选中订阅", command=self.delete_anime, bg="#ffffff", fg="#f44336", relief="flat",
                  highlightthickness=1, highlightbackground="#f44336", font=("Microsoft YaHei", 9), height=1,
                  cursor="hand2").pack(fill="x", pady=(20, 0))

    def get_default_season_dir(self):
        now = datetime.datetime.now()
        m, d, y = now.month, now.day, now.year
        score = m * 100 + d
        if score >= 1210 or score <= 310:
            s, ry = "一月", (y + 1 if m == 12 else y)
        elif 311 <= score <= 610:
            s, ry = "四月", y
        elif 611 <= score <= 910:
            s, ry = "七月", y
        else:
            s, ry = "十月", y
        return f"H:\\BT-Downloads\\番剧\\{ry}\\{s}"

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            name = self.tree.item(sel[0], "text")
            data = self.config.get(name)
            if data:
                self.info_label.config(text=f"【名称】\n{name}\n\n【路径】\n{data['download_dir']}", fg="#555")

    def add_anime_from_input(self):
        """直接从一级界面输入框读取名称并添加"""
        name = self.search_entry.get().strip()
        if not name or name == "输入番剧名称直接订阅...":
            messagebox.showwarning("提示", "请输入番剧名称后再试")
            return

        # 1. 询问订阅模式
        is_auto = messagebox.askyesno("订阅确认", f"准备订阅：{name}\n\n是否自动使用 Mikan 搜索链接？")
        rss = f"https://mikanani.me/RSS/Search?searchstr={urllib.parse.quote(name)}" if is_auto else simpledialog.askstring(
            "RSS", "手动输入 RSS 链接:")
        if not rss: return

        # 2. 路径确认
        suggested = self.get_default_season_dir()
        choice = messagebox.askyesnocancel("路径确认", f"建议路径：\n{suggested}\n\n是否使用该默认目录？")

        if choice is True:
            path = suggested
        elif choice is False:
            path = filedialog.askdirectory(initialdir="H:\\")
        else:
            return

        if path:
            self.config[name] = {"rss_url": rss, "download_dir": path.replace("/", "\\")}
            save_config(self.config)
            self.refresh_list()
            self.search_entry.delete(0, 'end')  # 清空输入框
            messagebox.showinfo("成功", f"【{name}】已加入订阅列表")

    def refresh_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for name in sorted(self.config.keys()): self.tree.insert("", "end", text=name)

    def delete_anime(self):
        sel = self.tree.selection()
        if not sel: return
        name = self.tree.item(sel[0], "text")
        if messagebox.askyesno("确认", f"确定删除 {name}？"):
            del self.config[name]
            save_config(self.config)
            self.refresh_list()
            self.info_label.config(text="请在左侧选择番剧", fg="#999")

    def check_update(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先在列表中选中番剧")
            return
        name = self.tree.item(sel[0], "text")
        details = self.config[name]
        data = get_rss_data(details["rss_url"], {"http": DEFAULT_PROXY, "https": DEFAULT_PROXY})
        if data:
            self.show_torrent_selection_window(data, details, name)
        else:
            messagebox.showerror("错误", "网络请求失败，请检查代理是否开启")

    def show_torrent_selection_window(self, rss_data, details, anime_name):
        root_node = ET.fromstring(rss_data)
        groups = {}
        all_items = []

        for item in root_node.findall(".//item"):
            title = item.find(".//title").text
            url = item.find(".//enclosure").get('url')
            group_name = title[1:title.find("]")] if title.startswith("[") and "]" in title else "其它"
            info = {"title": title, "url": url, "group": group_name}
            all_items.append(info)
            if group_name not in groups: groups[group_name] = []
            groups[group_name].append(info)

        if not all_items:
            messagebox.showinfo("提示", "未找到可用资源")
            return

        win = tk.Toplevel(self.root)
        win.title(f"选择资源 - {anime_name}")
        win.geometry("950x650")

        pane = tk.PanedWindow(win, orient="horizontal", bg="#ccc", sashwidth=4)
        pane.pack(fill="both", expand=True)

        left_group = tk.Frame(pane, bg="#ffffff")
        tk.Label(left_group, text="字幕组列表", bg="#eee", font=("Microsoft YaHei", 9, "bold")).pack(fill="x", pady=5)
        lb_groups = tk.Listbox(left_group, selectmode="multiple", font=("Microsoft YaHei", 9), bd=0,
                               highlightthickness=0)
        lb_groups.pack(fill="both", expand=True)
        for g in sorted(groups.keys()):
            lb_groups.insert("end", g)
            lb_groups.selection_set("end")

        pane.add(left_group, width=200)

        right_res = tk.Frame(pane, bg="#ffffff")
        pane.add(right_res)
        canvas = tk.Canvas(right_res, bg="#ffffff", highlightthickness=0)
        scroll = ttk.Scrollbar(right_res, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#ffffff")
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        vars_dict = {}

        def render():
            for w in scroll_frame.winfo_children(): w.destroy()
            selected_groups = [lb_groups.get(i) for i in lb_groups.curselection()]
            for g in selected_groups:
                tk.Label(scroll_frame, text=f"  {g}", bg="#e8f2ff", fg="#0056b3", font=("Microsoft YaHei", 10, "bold"),
                         anchor="w").pack(fill="x", pady=(10, 2))
                for item in groups[g]:
                    v = vars_dict.get(item['title'], tk.BooleanVar())
                    vars_dict[item['title']] = v
                    tk.Checkbutton(scroll_frame, text=item['title'], variable=v, bg="#ffffff",
                                   font=("Microsoft YaHei", 9), wraplength=680, justify="left").pack(anchor="w",
                                                                                                     padx=15)
            scroll_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        lb_groups.bind("<<ListboxSelect>>", lambda e: render())
        render()

        def do_dl():
            selected = [i for i in all_items if vars_dict.get(i['title']) and vars_dict[i['title']].get()]
            if not selected: return
            try:
                qb = Client(DEFAULT_QB_URL)
                qb.auth_log_in(DEFAULT_QB_USERNAME, DEFAULT_QB_PASSWORD)
                c_title = root_node.find(".//channel/title").text
                f_name = c_title.replace("Mikan Project - ", "").replace("搜索结果:", "").strip()
                save_path = os.path.join(details['download_dir'], f_name)
                for s in selected: qb.torrents_add(urls=s['url'], savepath=save_path)
                messagebox.showinfo("完成", f"已推送 {len(selected)} 个任务")
                win.destroy()
            except Exception as e:
                messagebox.showerror("QB连接失败", str(e))

        tk.Button(win, text="🚀 立即下载选中资源", command=do_dl, bg="#0078d7", fg="white",
                  font=("Microsoft YaHei", 10, "bold"), height=2, relief="flat").pack(fill="x", padx=20, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = MikanApp(root)
    root.mainloop()