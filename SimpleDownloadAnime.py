import urllib.parse
import datetime
import os
import json
import requests
import re
import subprocess
import asyncio
import xml.etree.ElementTree as ET
from qbittorrentapi import Client
from nicegui import ui, app as nicegui_app

# --- 基础配置 ---
CONFIG_FILE = "subscriptions.json"
DANDAN_PATH = r"D:\弹弹play\dandanplay.exe"
POTPLAYER_PATH = r"D:\app\PotPlayer\PotPlayerMini64.exe"
DEFAULT_PROXY = "socks5h://127.0.0.1:10808"
DEFAULT_QB_URL = 'http://127.0.0.1:8080'
DEFAULT_QB_USERNAME = ''
DEFAULT_QB_PASSWORD = ''


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


class MikanWebUI:
    def __init__(self):
        self.config = load_config()
        self.selected_anime = None
        self.render_ui()

    def render_ui(self):
        ui.colors(primary='#1d4ed8', secondary='#334155')
        ui.add_head_html('''
            <style>
                body { 
                    background-color: #f1f5f9; 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
                    -webkit-font-smoothing: antialiased;
                }
                .high-contrast-card { border: 2px solid #94a3b8 !important; }
                .anime-title { font-weight: 800 !important; color: #0f172a !important; }
                .list-text { font-weight: 600 !important; color: #1e293b !important; }
                .delete-btn { display: none; }
                .anime-item:hover .delete-btn { display: block; }
            </style>
        ''')

        # --- Header 区域 ---
        with ui.header().classes(
                'items-center bg-white text-slate-900 shadow-md py-3 px-8 border-b-2 border-slate-300 z-50'):
            ui.label('Mikan Pro').classes('text-2xl font-black tracking-tight anime-title mr-8')

            # 功能按钮组
            with ui.row().classes('gap-3'):
                ui.button('检查更新', icon='download_for_offline', on_click=self.check_update_and_fix_cover).classes(
                    'rounded-lg font-black px-4 shadow-sm')
                ui.button('关闭服务', icon='power_settings_new', on_click=self.terminate_service).classes(
                    'rounded-lg font-black px-4 shadow-sm').props('color=red')

            # 搜索框
            with ui.row().classes(
                    'ml-auto items-center bg-slate-50 rounded-lg px-4 w-96 border-2 border-slate-400 focus-within:border-primary'):
                ui.icon('search')
                self.search_input = ui.input(placeholder='搜索番剧...').props('borderless dense').classes(
                    'flex-grow ml-2 py-1 font-bold text-lg')
                self.search_input.on('keydown.enter', self.handle_search)

        # --- 主内容区 ---
        with ui.row().classes('w-full p-6 no-wrap items-start max-w-[1500px] mx-auto gap-8'):
            # 左侧：订阅列表
            with ui.column().classes('w-80 sticky top-24 gap-4'):
                with ui.card().classes('w-full p-0 rounded-xl bg-white overflow-hidden high-contrast-card shadow-lg'):
                    ui.label('我的订阅').classes(
                        'font-black px-4 py-3 bg-slate-800 text-white text-sm uppercase tracking-wider')
                    self.list_container = ui.list().classes('w-full divide-y divide-slate-200')
                    self.refresh_anime_list()

            # 右侧：详情展示
            with ui.column().classes('flex-grow gap-4'):
                self.detail_card = ui.card().classes(
                    'w-full min-h-[700px] p-8 rounded-2xl bg-white relative high-contrast-card shadow-xl')
                with self.detail_card:
                    self.detail_area = ui.column().classes('w-full h-full')

    def terminate_service(self):
        """彻底杀掉后端进程"""
        ui.notify('正在关闭后台服务...', type='warning')
        # 给一点时间让通知显示
        asyncio.create_task(self.delayed_exit())

    async def delayed_exit(self):
        await asyncio.sleep(0.5)
        import os
        os._exit(0)

    def refresh_anime_list(self):
        self.list_container.clear()
        self.config = load_config()
        with self.list_container:
            for name in sorted(self.config.keys()):
                is_active = (name == self.selected_anime)
                data = self.config[name]
                with ui.item(on_click=lambda n=name: self.show_details(n)).props('clickable v-ripple').classes(
                        f'py-4 px-4 anime-item transition-all {"bg-blue-100 border-r-8 border-primary shadow-inner" if is_active else "hover:bg-slate-50"}'
                ):
                    with ui.item_section().props('avatar'):
                        if data.get('cover_url'):
                            ui.image(data['cover_url']).classes(
                                'w-12 h-16 rounded shadow-sm border border-slate-300 object-cover')
                        else:
                            ui.icon('movie', size='28px', color='slate-500')
                    with ui.item_section():
                        ui.item_label(name).classes('list-text')
                    with ui.item_section().props('side'):
                        ui.button(icon='delete', on_click=lambda n=name: self.delete_subscription(n)).props(
                            'flat round color=red size=sm').classes('delete-btn')

    def delete_subscription(self, name):
        if name in self.config:
            del self.config[name]
            save_config(self.config)
            ui.notify(f'已删除订阅: {name}')
            if self.selected_anime == name: self.selected_anime = None
            self.refresh_anime_list()
            self.detail_area.clear()

    def show_details(self, name):
        self.selected_anime = name
        self.refresh_anime_list()
        data = self.config[name]
        folder_name = data.get('folder_name', name)
        download_dir = data.get('download_dir', '')
        full_path = os.path.join(download_dir, folder_name)

        # 检查本地视频
        videos = []
        if os.path.exists(full_path):
            videos = sorted([f for f in os.listdir(full_path) if f.lower().endswith(('.mp4', '.mkv', '.ts'))])

        self.detail_area.clear()
        with self.detail_area:
            with ui.row().classes('no-wrap gap-8 w-full items-start'):
                if data.get('cover_url'):
                    ui.image(data['cover_url']).classes(
                        'w-64 h-96 rounded-2xl shadow-2xl object-cover border-4 border-white')
                with ui.column().classes('flex-grow pt-2'):
                    ui.label(name).classes('text-4xl font-black text-slate-900 tracking-tighter mb-6 anime-title')
                    ui.button('打开本地目录', icon='folder_open', on_click=lambda: os.startfile(full_path)).props(
                        'unelevated color=primary size=lg').classes('font-bold')

            ui.separator().classes('my-8 border-slate-300')
            ui.label('本地视频文件').classes('text-xl font-black mb-4 ml-1 tracking-tight')
            with ui.scroll_area().classes('w-full h-[400px] pr-4'):
                if not videos:
                    ui.label('暂无视频文件，请检查下载目录。').classes('text-slate-400 italic ml-1')
                for v in videos:
                    v_path = os.path.join(full_path, v)
                    with ui.row().classes(
                            'w-full items-center gap-3 py-3 px-5 mb-2 hover:bg-blue-50 rounded-xl border border-slate-200 transition-all'):
                        ui.label(v).classes('text-sm text-slate-900 truncate flex-grow font-bold cursor-pointer').on(
                            'click', lambda _, p=v_path: subprocess.Popen([POTPLAYER_PATH, p]))
                        with ui.row().classes('gap-2'):
                            ui.button(icon='play_circle',
                                      on_click=lambda _, p=v_path: subprocess.Popen([POTPLAYER_PATH, p])).props(
                                'flat round color=primary').tooltip('PotPlayer')
                            ui.button(icon='screenshot_monitor',
                                      on_click=lambda _, p=v_path: subprocess.Popen([DANDAN_PATH, p])).props(
                                'flat round color=green').tooltip('弹弹Play')

    async def check_update_and_fix_cover(self):
        if not self.selected_anime:
            ui.notify('请从左侧选择一个番剧');
            return
        name = self.selected_anime
        n = ui.notification(f'正在检索 Mikan RSS...', type='ongoing', spinner=True)
        try:
            proxies = {"http": DEFAULT_PROXY, "https": DEFAULT_PROXY}
            loop = asyncio.get_running_loop()

            # 如果没封面，尝试补全
            if not self.config[name].get('cover_url'):
                search_url = f"https://mikanani.me/RSS/Search?searchstr={urllib.parse.quote(name)}"
                r_search = await loop.run_in_executor(None,
                                                      lambda: requests.get(search_url, proxies=proxies, timeout=10))
                root_s = ET.fromstring(r_search.text)
                first_item = root_s.find(".//item")
                if first_item is not None:
                    ep_link = first_item.find("link").text
                    res_ep = await loop.run_in_executor(None, lambda: requests.get(ep_link, proxies=proxies))
                    b_match = re.search(r'/Home/Bangumi/(\d+)', res_ep.text)
                    if b_match:
                        bangumi_url = f"https://mikanani.me/Home/Bangumi/{b_match.group(1)}"
                        b_res = await loop.run_in_executor(None, lambda: requests.get(bangumi_url, proxies=proxies))
                        img_path_match = re.search(r'/(images/Bangumi/[^\s\'"\)>]+)', b_res.text)
                        if img_path_match:
                            img_url = "https://mikanani.me/" + img_path_match.group(1).lstrip('/')
                            self.config[name]['cover_url'] = img_url
                            save_config(self.config)
                            self.refresh_anime_list()

            # 获取 RSS 列表
            rss_url = self.config[name]['rss_url']
            r_rss = await loop.run_in_executor(None, lambda: requests.get(rss_url, proxies=proxies))
            root = ET.fromstring(r_rss.text)
            items = []
            for item in root.findall(".//item"):
                t = item.find("title").text
                g = re.search(r'^\[([^\]]+)\]', t).group(1) if re.search(r'^\[([^\]]+)\]', t) else "其他"
                items.append({'title': t, 'url': item.find(".//enclosure").get('url'), 'group': g})

            n.dismiss()
            if items:
                target_path = os.path.join(self.config[name]['download_dir'],
                                           self.config[name].get('folder_name', name))
                self.show_download_selection(items, target_path)
            else:
                ui.notify('未发现新资源')
        except Exception as e:
            n.dismiss()
            ui.notify(f'连接失败，请检查代理: {e}')

    def show_download_selection(self, items, target_path):
        grouped = {}
        for item in items:
            grouped.setdefault(item['group'], []).append(item)

        # 1600px 宽度适配，确保单窗口显示
        with ui.dialog() as d, ui.card().classes(
                'w-[1600px] max-w-[95vw] h-[90vh] rounded-2xl p-0 overflow-hidden shadow-2xl bg-slate-50'):
            # 顶部蓝色标题栏
            with ui.row().classes('w-full bg-blue-700 p-6 text-white items-center no-wrap shadow-lg'):
                ui.icon('cloud_download', size='36px')
                with ui.column().classes('gap-0'):
                    ui.label('资源更新清单').classes('text-2xl font-black ml-2 leading-none')
                    ui.label(f'推送目录: {target_path}').classes('text-xs ml-2 opacity-80 mt-1')
                ui.space()
                ui.button(icon='close', on_click=d.close).props('flat round color=white')

            selected = set()

            # 中间主内容滚动区
            with ui.scroll_area().classes('flex-grow p-8'):
                with ui.column().classes('w-full gap-6'):
                    for group, sub_items in grouped.items():
                        with ui.card().classes(
                                'w-full p-0 rounded-xl border-2 border-slate-200 overflow-hidden shadow-sm'):
                            # 字幕组分类头
                            with ui.row().classes(
                                    'w-full bg-slate-100 px-6 py-3 items-center border-b-2 border-slate-200'):
                                ui.icon('group', color='blue-900', size='20px')
                                ui.label(group).classes('font-black text-blue-900 text-lg ml-2 tracking-tight')
                                ui.badge(f'{len(sub_items)} 个资源').props('color=blue-100 text-color=blue-900').classes(
                                    'ml-2 font-bold')

                            # 资源列表详情
                            with ui.column().classes('w-full divide-y divide-slate-100'):
                                for item in sub_items:
                                    # 每一行资源
                                    with ui.row().classes(
                                            'w-full items-center py-4 px-8 hover:bg-blue-50 transition-colors cursor-pointer') as row:
                                        # 修复报错：通过 e.value 手动控制选中
                                        cb = ui.checkbox(
                                            on_change=lambda e, u=item['url']: selected.add(
                                                u) if e.value else selected.discard(u)
                                        ).props('size=lg color=blue')

                                        ui.label(item['title']).classes(
                                            'text-base flex-grow font-bold text-slate-800 ml-4 leading-relaxed break-all')

                                        # 修复 'toggle' 报错：改用直接修改 value 的方式
                                        row.on('click', lambda c=cb: setattr(c, 'value', not c.value))

            # 底部操作栏
            with ui.row().classes('w-full p-6 justify-end bg-white border-t-2 border-slate-200 gap-6 shadow-md'):
                ui.button('取消', on_click=d.close).props('outline color=grey-7').classes(
                    'px-8 font-bold h-12 rounded-lg')
                ui.button('确定推送至 qBittorrent', icon='send',
                          on_click=lambda: self.do_download(selected, target_path, d)).props(
                    'unelevated color=blue-7').classes('px-12 font-black h-12 rounded-lg text-lg shadow-md')

        d.open()

    def do_download(self, urls, path, dialog):
        if not urls: return
        try:
            qb = Client(DEFAULT_QB_URL)
            qb.auth_log_in(DEFAULT_QB_USERNAME, DEFAULT_QB_PASSWORD)
            for url in urls: qb.torrents_add(urls=url, savepath=path)
            ui.notify('推送成功！请在 qBittorrent 中查看进度')
            dialog.close()
        except Exception as e:
            ui.notify(f'qB 推送失败: {e}')

    async def handle_search(self):
        query = self.search_input.value.strip()
        if not query: return
        n = ui.notification('搜索 Mikan Project 中...', type='ongoing', spinner=True)
        try:
            proxies = {"http": DEFAULT_PROXY, "https": DEFAULT_PROXY}
            r = await asyncio.get_running_loop().run_in_executor(None, lambda: requests.get(
                f"https://mikanani.me/RSS/Search?searchstr={urllib.parse.quote(query)}", proxies=proxies))
            root = ET.fromstring(r.text)
            official_name = re.sub(r'^Mikan Project - (搜索结果:)?', '', root.find(".//channel/title").text).strip()

            cover_url = ""
            first_item = root.find(".//item")
            if first_item is not None:
                ep_url = first_item.find("link").text
                res = await asyncio.get_running_loop().run_in_executor(None,
                                                                       lambda: requests.get(ep_url, proxies=proxies))
                b_match = re.search(r'/Home/Bangumi/(\d+)', res.text)
                if b_match:
                    b_res = await asyncio.get_running_loop().run_in_executor(None, lambda: requests.get(
                        f"https://mikanani.me/Home/Bangumi/{b_match.group(1)}", proxies=proxies))
                    i_match = re.search(r'/(images/Bangumi/[^\s\'"\)>]+)', b_res.text)
                    if i_match: cover_url = "https://mikanani.me/" + i_match.group(1).lstrip('/')

            n.dismiss()
            self.show_confirm_dialog(official_name, cover_url)
        except Exception as e:
            n.dismiss()
            ui.notify(f'搜索失败: {e}')

    def show_confirm_dialog(self, name, cover):
        # 自动日期归档逻辑
        now = datetime.datetime.now()
        year = now.strftime('%Y')
        month = now.month
        quarter = "01" if month <= 3 else "04" if month <= 6 else "07" if month <= 9 else "10"
        dynamic_path = f"H:\\BT-Downloads\\番剧\\{year}\\{quarter}"

        with ui.dialog() as d, ui.card().classes('w-[500px] p-8 rounded-2xl high-contrast-card'):
            ui.label('确认新增订阅').classes('text-2xl font-black mb-4 text-primary anime-title')
            if cover: ui.image(cover).classes('w-full h-80 rounded-xl shadow-md mb-4 object-cover')
            ui.label(name).classes('font-black text-lg mb-6')

            path_i = ui.input('下载归档路径', value=dynamic_path).classes('w-full mb-8 font-bold').props(
                'outlined rounded dense')

            ui.button('确认订阅', on_click=lambda: self.final_add(name, cover, path_i.value, d)).props(
                'unelevated size=lg w-full').classes('font-black')
        d.open()

    def final_add(self, name, cover, path, dialog):
        self.config[name] = {
            "rss_url": f"https://mikanani.me/RSS/Search?searchstr={urllib.parse.quote(name)}",
            "download_dir": path,
            "cover_url": cover,
            "folder_name": name
        }
        save_config(self.config)
        dialog.close()
        self.refresh_anime_list()
        ui.notify(f'成功订阅: {name}')


if __name__ in {"__main__", "__mp_main__"}:
    app = MikanWebUI()
    # 使用 native=False 因为我们要通过启动脚本控制窗口和后台
    ui.run(title='Mikan Manager Pro', port=8105, show=False, reload=False)