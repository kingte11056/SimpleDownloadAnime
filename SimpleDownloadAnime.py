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
DEFAULT_DOWNLOAD_DIR = r'H:\BT-Downloads\番剧'  # 下载文件的目标目录
DEFAULT_PROXY = "socks5h://127.0.0.1:10808"  # 默认代理地址
DEFAULT_RSS_URL = "https://mikanani.me/RSS/Bangumi?bangumiId=3416&subgroupid=370"  # 默认的 RSS URL
CONFIG_FILE_NAME = "subscriptions.json"  # 配置文件名称

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

# 解析 RSS 获取磁力链接
def get_magnet_links(rss_data):
    tree = ET.ElementTree(ET.fromstring(rss_data))
    root = tree.getroot()
    magnet_links = []

    for item in root.findall(".//item"):
        # 获取磁力链接
        enclosure = item.find(".//enclosure")
        if enclosure is not None:
            torrent_url = enclosure.get('url')
            magnet_links.append(torrent_url)

    return magnet_links

# 提取番剧名字
def get_folder_name(rss_data):
    tree = ET.ElementTree(ET.fromstring(rss_data))
    root = tree.getroot()

    # 提取 channel/title 作为番剧名字
    channel_title = root.find(".//channel/title")
    if channel_title is not None:
        title_text = channel_title.text
        # 假设 "Mikan Project - " 是固定前缀
        folder_name = title_text.replace("Mikan Project - ", "").strip()
        return folder_name
    return "未命名番剧"

# 将磁力链接添加到 qBittorrent
def add_magnets_to_qb(magnet_links, folder_name, qb, download_dir):
    folder_path = os.path.join(download_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)  # 确保文件夹存在

    for magnet in magnet_links:
        qb.torrents_add(urls=magnet, savepath=folder_path)
        print(f"Added magnet link to qBittorrent: {magnet}")

# 主处理函数
def start_download(qb_url, qb_username, qb_password, download_dir, proxy, rss_url):
    # 获取 RSS 数据并解析
    rss_data = get_rss_data(rss_url, {"http": proxy, "https": proxy})
    if rss_data is None:
        messagebox.showerror("Error", "Failed to retrieve RSS feed.")
        return

    # 提取番剧名字作为文件夹名
    folder_name = get_folder_name(rss_data)

    # 获取磁力链接
    magnet_links = get_magnet_links(rss_data)
    if magnet_links:
        # 连接到 qBittorrent
        qb = connect_to_qb(qb_url, qb_username, qb_password)

        # 将磁力链接添加到 qBittorrent
        add_magnets_to_qb(magnet_links, folder_name, qb, download_dir)
        messagebox.showinfo("Success", f"Successfully added {len(magnet_links)} torrents to qBittorrent.")
    else:
        messagebox.showwarning("No Torrents", "No torrents found in the RSS feed.")

# 创建图形化界面
def create_gui():
    # 创建主窗口
    root = tk.Tk()
    root.title("qBittorrent 自动下载番剧")

    # 设置窗口大小
    root.geometry("500x600")

    # 加载配置
    config = load_config()

    # 番剧列表框
    def refresh_anime_list():
        listbox.delete(0, tk.END)
        for anime, details in config.items():
            listbox.insert(tk.END, f"{anime} -> {details['download_dir']}")

    # 添加番剧
    def add_anime():
        name = simpledialog.askstring("添加番剧", "请输入番剧名称:")
        if name and name not in config:
            rss_url = simpledialog.askstring("添加番剧", "请输入 RSS 地址:")
            download_dir = filedialog.askdirectory(title="选择下载目录")
            if rss_url and download_dir:
                config[name] = {"rss_url": rss_url, "download_dir": download_dir}
                save_config(config)
                refresh_anime_list()

        elif name in config:
            messagebox.showerror("错误", "番剧已存在!")

    # 删除番剧
    def delete_anime():
        selected = listbox.curselection()
        if selected:
            anime = listbox.get(selected[0]).split(" -> ")[0]
            if anime in config:
                del config[anime]
                save_config(config)
                refresh_anime_list()

    # 下载选定番剧
    def download_selected():
        selected = listbox.curselection()
        if selected:
            anime = listbox.get(selected[0]).split(" -> ")[0]
            if anime in config:
                details = config[anime]
                start_download(DEFAULT_QB_URL, DEFAULT_QB_USERNAME, DEFAULT_QB_PASSWORD,
                               details['download_dir'], DEFAULT_PROXY, details['rss_url'])

    # 番剧列表
    listbox = tk.Listbox(root, height=20, width=70)
    listbox.pack(pady=10)

    refresh_anime_list()

    # 按钮区
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="添加番剧", command=add_anime).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="删除番剧", command=delete_anime).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="开始下载", command=download_selected).pack(side=tk.LEFT, padx=5)

    # 运行窗口
    root.mainloop()

if __name__ == "__main__":
    create_gui()
