import requests
import xml.etree.ElementTree as ET
from qbittorrentapi import Client
import os
import tkinter as tk
from tkinter import messagebox

# 设置默认值
DEFAULT_QB_URL = 'http://127.0.0.1:8080'  # qBittorrent Web UI 的 URL
DEFAULT_QB_USERNAME = 'admin'  # qBittorrent Web UI 用户名
DEFAULT_QB_PASSWORD = '1qaz2wsx'  # qBittorrent Web UI 密码
DEFAULT_DOWNLOAD_DIR = r'H:\BT-Downloads\番剧'  # 下载文件的目标目录
DEFAULT_PROXY = "socks5h://127.0.0.1:10808"  # 默认代理地址
DEFAULT_RSS_URL = "https://mikanani.me/RSS/Bangumi?bangumiId=3416&subgroupid=370"  # 默认的 RSS URL


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
    root.geometry("400x450")

    # RSS 链接
    tk.Label(root, text="RSS URL:").pack(pady=5)
    rss_url_entry = tk.Entry(root, width=50)
    rss_url_entry.insert(0, DEFAULT_RSS_URL)
    rss_url_entry.pack(pady=5)

    # qBittorrent Web UI 地址
    tk.Label(root, text="qBittorrent Web UI URL:").pack(pady=5)
    qb_url_entry = tk.Entry(root, width=50)
    qb_url_entry.insert(0, DEFAULT_QB_URL)
    qb_url_entry.pack(pady=5)

    # 用户名
    tk.Label(root, text="qBittorrent Username:").pack(pady=5)
    qb_username_entry = tk.Entry(root, width=50)
    qb_username_entry.insert(0, DEFAULT_QB_USERNAME)
    qb_username_entry.pack(pady=5)

    # 密码
    tk.Label(root, text="qBittorrent Password:").pack(pady=5)
    qb_password_entry = tk.Entry(root, width=50, show="*")
    qb_password_entry.insert(0, DEFAULT_QB_PASSWORD)
    qb_password_entry.pack(pady=5)

    # 下载目录
    tk.Label(root, text="下载目录:").pack(pady=5)
    download_dir_entry = tk.Entry(root, width=50)
    download_dir_entry.insert(0, DEFAULT_DOWNLOAD_DIR)
    download_dir_entry.pack(pady=5)

    # 代理地址
    tk.Label(root, text="代理地址 (如:socks5h://127.0.0.1:10808):").pack(pady=5)
    proxy_entry = tk.Entry(root, width=50)
    proxy_entry.insert(0, DEFAULT_PROXY)
    proxy_entry.pack(pady=5)

    # 开始下载按钮
    def on_download_click():
        rss_url = rss_url_entry.get()
        qb_url = qb_url_entry.get()
        qb_username = qb_username_entry.get()
        qb_password = qb_password_entry.get()
        download_dir = download_dir_entry.get()
        proxy = proxy_entry.get()

        start_download(qb_url, qb_username, qb_password, download_dir, proxy, rss_url)

    download_button = tk.Button(root, text="开始下载", command=on_download_click)
    download_button.pack(pady=20)

    # 运行窗口
    root.mainloop()


if __name__ == "__main__":
    create_gui()
