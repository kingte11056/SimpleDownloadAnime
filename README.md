# SimpleDownloadAnime

# 半自动下载番剧工具

## 项目简介
一个半自动下载番剧的工具，主要通过解析 RSS 订阅，将种子文件发送给 qBittorrent（简称 qb）以实现下载。虽然 qb 本身也有类似功能，但其 RSS 订阅和自动下载功能不够好用，因此开发了这个工具来提升使用体验。

## 前置条件

1. **番剧订阅 RSS 链接**：必须是来自 [Mikanani](https://mikanani.me/) 的 RSS。
2. **代理工具**：需要使用代理工具（如 v2rayN），以确保本工具和 qb 能访问 RSS 订阅和下载种子。
3. **qb 设置**：
    - 配置 qb 使用代理访问外网。
    - 确保启用了本地 Web UI 访问。

完成以上配置后，即可使用本工具实现更高效的番剧下载。

## 功能特性
- 自动解析 Mikanani 的 RSS 订阅。
- 根据订阅内容获取种子文件。
- 将种子文件发送到 qBittorrent 进行下载。

## 使用步骤

1. **准备工作**：
    - 确保已配置好 Mikanani RSS 链接。
    - 启动代理工具（如 v2rayN）。
    - 检查 qBittorrent 设置，确保代理和 Web UI 正常工作。

2. **运行工具**：
    - 启动本工具。
    - 配置 RSS 链接和 qb Web UI 信息。

3. **开始下载**：
    - 本工具会自动解析 RSS 链接，下载种子，并通过 qb 开始下载番剧。

## 注意事项
- 确保代理工具和 qb 配置正确，否则可能导致 RSS 无法解析或种子下载失败。
- Mikanani 的 RSS 链接为 HTTPS，需保证网络环境支持 HTTPS。

## 相关链接
- [Mikanani RSS](https://mikanani.me/)
- [qBittorrent 官方文档](https://www.qbittorrent.org/)
- [v2rayN GitHub](https://github.com/2dust/v2rayN)

