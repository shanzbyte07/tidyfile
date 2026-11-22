# 🧹 tidyfile

> 一键整理乱糟糟的文件夹 —— **零依赖、单文件、支持预览与一键撤销**

[English](#-english) | 中文

![License](https://img.shields.io/badge/license-MIT-green) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

下载文件夹里堆了 500 个文件?桌面乱成鸡窝?`tidyfile` 一条命令帮你按类型(或日期)自动归档,还支持**预览**和**一键撤销**,放心大胆地整理。

## ✨ 特性

- 📦 **零依赖** —— 只用 Python 标准库,不需要 `pip install` 任何东西
- 🗂️ **按类型整理** —— 图片 / 文档 / 视频 / 音频 / 压缩包 / 程序 / 代码 / 字体…
- 📅 **按日期整理** —— 按「年月」归档,适合照片、录屏等按时间归类的文件
- 👀 **预览模式** —— 先看看会发生什么,再决定是否执行,绝不误伤
- ↩️ **一键撤销** —— 整理后悔了?`--undo` 把所有文件放回原位
- 🔁 **防覆盖** —— 重名文件自动改名(`报告 (1).pdf`),绝不覆盖你的文件
- 🌍 **跨平台** —— Windows / macOS / Linux 都能用
- 📄 **单文件** —— 就一个 `.py` 文件,下载即用,代码不到 400 行,适合阅读学习

## 🚀 快速开始

**方式一:下载 exe,双击就用(不需要会编程)**

1. 打开 [Releases 页面](https://github.com/shanzbyte07/tidyfile/releases),下载 `tidyfile.exe`
2. 双击运行(它会先询问你要整理哪个文件夹,输入 y 确认)
3. 更推荐:按 `Win + R` 输入 `cmd`,然后用命令行操作,可以指定文件夹、预览、撤销等

> ⚠️ 首次运行如遇到 Windows SmartScreen 蓝色提示,点 **「更多信息」→「仍要运行」** 即可——因为我们没有花钱购买代码签名证书,微软不认识这个签名,并非病毒(全部代码公开可见,可自行审查)。

**方式二:用 Python 运行(适合开发者)**

只需要 **Python 3.8+**(无需安装任何第三方库),下载本仓库的 `tidyfile.py` 即可使用。

```bash
# 整理下载文件夹
python tidyfile.py ~/Downloads
```

```text
🧹 整理:C:\Users\you\Downloads

✅ 整理完成!
  🖼️ 图片      43 个    120.3MB
  📄 文档      21 个     45.6MB
  📦 压缩包    11 个     89.1MB
  🎬 视频       8 个    612.5MB
  ————————————————
  合计 128 个文件,867.5MB

  后悔了?加 --undo 参数可一键撤销。
```

## 🧪 常用命令

```bash
# 先预览,不真正移动(强烈推荐第一次先用这个)
python tidyfile.py ~/Downloads --dry-run

# 连子文件夹里的文件也一起整理
python tidyfile.py ~/Downloads --recursive

# 按年月整理照片
python tidyfile.py ~/Pictures --by-date

# 整理后悔了?一键撤销,全部放回原位
python tidyfile.py ~/Downloads --undo

# 查看每个文件的移动明细
python tidyfile.py ~/Downloads --verbose

# 查看帮助
python tidyfile.py --help
```

## ⚙️ 全部参数

| 参数 | 说明 |
|------|------|
| `目录` | 要整理的文件夹路径,默认为当前目录 |
| `-r, --recursive` | 连子文件夹里的文件也一起整理 |
| `-d, --by-date` | 按「年月」整理,而不是按文件类型 |
| `-n, --dry-run` | 只预览要做什么,不真正移动文件 |
| `-u, --undo` | 撤销上一次整理,把文件放回原位 |
| `-v, --verbose` | 显示每一个文件的移动明细 |
| `-V, --version` | 显示版本号 |

## 📁 默认分类

| 分类 | 扩展名 |
|------|--------|
| 🖼️ 图片 | jpg jpeg png gif webp bmp svg ico tif tiff heic raw |
| 📄 文档 | pdf doc docx xls xlsx ppt pptx txt md csv rtf epub |
| 🎬 视频 | mp4 mkv avi mov wmv flv webm m4v rmvb |
| 🎵 音频 | mp3 wav flac aac ogg m4a wma ape |
| 📦 压缩包 | zip rar 7z tar gz bz2 xz iso cab |
| ⚙️ 程序 | exe msi bat cmd apk dmg deb rpm pkg |
| 💻 代码 | py js ts html css java c cpp go rs php sh sql json xml yml yaml toml |
| 🔤 字体 | ttf otf woff woff2 |
| 🧲 种子 | torrent |
| 🗂️ 其他 | 无法识别的类型 |

💡 想加自己的分类?打开 `tidyfile.py`,在顶部的 `CATEGORIES` 里加一行即可,比如 `"设计": (".fig", ".xd"),`

## ❓ 常见问题

**会覆盖同名文件吗?**
不会。目标位置有同名文件时,会自动改名成 `文件 (1).jpg`、`文件 (2).jpg`。

**隐藏文件会被移动吗?**
不会。以 `.` 开头的文件和文件夹(包括 `tidyfile` 自己的撤销账本)都会被跳过。

**整理错了怎么办?**
在同一个文件夹运行 `python tidyfile.py --undo`,所有文件会放回原位。

**移动失败怎么办?**
文件被占用或没有权限时,`tidyfile` 会跳过它并在最后提示,不会中断整个整理过程。

## 🌏 English

**tidyfile** is a zero-dependency, single-file Python CLI tool that tidies messy folders (Downloads, Desktop…) by file type or by year-month, with a `--dry-run` preview mode and one-command `--undo`. Download `tidyfile.py` and run it with Python 3.8+ — no installation needed.

```bash
python tidyfile.py ~/Downloads          # tidy a folder
python tidyfile.py ~/Downloads -n       # preview only
python tidyfile.py ~/Downloads --undo   # revert the last run
```

## 🤝 参与贡献

欢迎提 Issue 和 Pull Request!哪怕是修正一个错别字也非常感谢 🎉

1. Fork 本仓库
2. 新建分支:`git checkout -b feat/your-feature`
3. 提交修改:`git commit -m "feat: 你的功能"`
4. 推送并提交 Pull Request

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。
