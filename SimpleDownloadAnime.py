import requests
import xml.etree.ElementTree as ET
import qbittorrentapi
from qbittorrentapi import Client
import os
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import json

# 设置默认值
DEFAULT_QB_URL = 'http://127.0.0.1:8080'  # qBittorrent Web UI 的 URL
DEFAULT_QB_USERNAME = 'admin'  # qBittorrent Web UI 用户名
DEFAULT_QB_PASSWORD = '1qaz2wsx'  # qBittorrent Web UI 密码
CONFIG_FILE_NAME = "subscriptions.json"  # 配置文件名称

DEFAULT_PROXY = "socks5h://127.0.0.1:10808"  # 默认代理地址

# 读取配置文件
def load_config():
    if os.path.exists(CONFIG_FILE_NAME):
        try:
            with open(CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config file: {e}")
    return {}

# 保存配置文件
def save_config(config):
    try:
        with open(CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Failed to save config file: {e}")

# 获取 RSS 链接内容
def get_rss_data(rss_url, proxies):
    try:
        response = requests.get(rss_url, proxies=proxies)
        response.raise_for_status()  # 确保请求成功
        return response.text
    except requests.RequestException as e:
        print(f"Failed to retrieve RSS feed: {e}")
        return None

# 连接到 qBittorrent
def connect_to_qb(qb_url, qb_username, qb_password):
    qb = Client(qb_url)
    qb.auth_log_in(qb_username, qb_password)
    return qb

# 解析 RSS 获取磁力链接和番剧集信息
def get_magnet_links(rss_data):
    tree = ET.ElementTree(ET.fromstring(rss_data))
    root = tree.getroot()
    items = []

    for item in root.findall(".//item"):
        title = item.find(".//title").text
        enclosure = item.find(".//enclosure")
        if enclosure is not None:
            torrent_url = enclosure.get('url')
            items.append({
                "title": title,
                "url": torrent_url,
                "downloaded": False  # 默认没有下载
            })

    return items

# 将磁力链接添加到 qBittorrent
def add_magnets_to_qb(magnet_links, folder_name, qb, download_dir):
    folder_path = os.path.join(download_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)  # 确保文件夹存在

    for magnet in magnet_links:
        qb.torrents_add(urls=magnet['url'], savepath=folder_path)
        print(f"Added magnet link to qBittorrent: {magnet['title']}")

# 主处理函数
def start_download(qb_url, qb_username, qb_password, download_dir, proxy, rss_url, selected_items):
    # 获取 RSS 数据并解析
    rss_data = get_rss_data(rss_url, {"http": proxy, "https": proxy})
    if rss_data is None:
        messagebox.showerror("Error", "Failed to retrieve RSS feed.")
        return

    # 获取磁力链接
    items = get_magnet_links(rss_data)

    # 过滤出已选择的种子
    selected_magnets = [item for item in items if item["title"] in selected_items]

    if selected_magnets:
        # 连接到 qBittorrent
        qb = connect_to_qb(qb_url, qb_username, qb_password)

        # 将磁力链接添加到 qBittorrent
        add_magnets_to_qb(selected_magnets, "下载", qb, download_dir)
        messagebox.showinfo("Success", f"Successfully added {len(selected_magnets)} torrents to qBittorrent.")
    else:
        messagebox.showwarning("No Torrents", "No torrents selected for download.")

# 显示番剧的种子信息
def show_torrent_selection_window(rss_data, rss_url, download_dir):
    # 获取RSS数据中的所有种子
    items = get_magnet_links(rss_data)

    # 创建新的窗口显示种子信息
    selection_window = tk.Toplevel()
    selection_window.title("选择要下载的种子")
    selection_window.geometry("1080x720")  # 更大的窗口大小，适应1080p显示

    # 创建滚动条和画布容器
    canvas = tk.Canvas(selection_window)
    scrollbar = tk.Scrollbar(selection_window, orient="vertical", command=canvas.yview)
    canvas.config(yscrollcommand=scrollbar.set)

    # 创建一个frame来放入所有种子条目
    frame = tk.Frame(canvas)

    # 创建复选框列表，供用户选择下载的种子
    var_dict = {}
    for item in items:
        var = tk.BooleanVar()
        var_dict[item["title"]] = var
        checkbox = tk.Checkbutton(frame, text=item["title"], variable=var)
        checkbox.pack(anchor="w", padx=10, pady=2)

    # 将frame放入canvas中
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # 配置滚动条
    scrollbar.config(command=canvas.yview)

    # 打包Canvas和Scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 更新滚动区域大小
    frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # 点击按钮下载选中的种子
    def download_selected():
        # 选中种子的标题列表
        selected_items = [item["title"] for item in items if var_dict.get(item["title"]).get()]

        if selected_items:
            # 执行下载
            start_download(DEFAULT_QB_URL, DEFAULT_QB_USERNAME, DEFAULT_QB_PASSWORD,
                           download_dir, DEFAULT_PROXY, rss_url, selected_items)
            selection_window.destroy()
        else:
            messagebox.showwarning("No Selection", "Please select at least one item to download.")

    # 添加“开始下载”按钮
    tk.Button(selection_window, text="开始下载", command=download_selected).pack(pady=10)

# 创建图形化界面
def create_gui():
    # 创建主窗口
    root = tk.Tk()
    root.title("qBittorrent 自动下载番剧")

    # 设置窗口大小
    root.geometry("500x600")

    # 加载配置
    config = load_config()

    # 输入框：RSS URL 和下载目录
    def set_rss_and_dir():
        rss_url = simpledialog.askstring("设置", "请输入 RSS 地址:")
        download_dir = simpledialog.askstring("设置", "请输入下载目录:")
        if rss_url and download_dir:
            name = simpledialog.askstring("设置", "请输入番剧名称:")
            if name and name not in config:
                config[name] = {
                    "rss_url": rss_url,
                    "download_dir": download_dir,
                    "items": []  # 初始没有下载过的番剧
                }
                save_config(config)
                refresh_anime_list()

    # 刷新番剧列表
    def refresh_anime_list():
        listbox.delete(0, tk.END)
        for anime, details in config.items():
            listbox.insert(tk.END, f"{anime} -> {details['download_dir']}")

    # 删除番剧
    def delete_anime():
        selected = listbox.curselection()
        if selected:
            anime = listbox.get(selected[0]).split(" -> ")[0]
            if anime in config:
                del config[anime]
                save_config(config)
                refresh_anime_list()
                messagebox.showinfo("删除成功", f"已删除 {anime} 的订阅信息.")
            else:
                messagebox.showerror("错误", "该番剧不存在!")

    # 显示种子选择窗口
    def show_torrent_selection():
        selected = listbox.curselection()
        if selected:
            anime = listbox.get(selected[0]).split(" -> ")[0]
            if anime in config:
                details = config[anime]
                rss_data = get_rss_data(details["rss_url"], {"http": DEFAULT_PROXY, "https": DEFAULT_PROXY})
                if rss_data:
                    show_torrent_selection_window(rss_data, details["rss_url"], details['download_dir'])

    # 番剧列表
    listbox = tk.Listbox(root, height=20, width=70)
    listbox.pack(pady=10)

    refresh_anime_list()

    # 按钮区
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="设置订阅和下载目录", command=set_rss_and_dir).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="显示种子选择", command=show_torrent_selection).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="删除番剧", command=delete_anime).pack(side=tk.LEFT, padx=5)

    # 运行窗口
    root.mainloop()


if __name__ == "__main__":
    create_gui()
