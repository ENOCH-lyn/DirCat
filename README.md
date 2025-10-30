# DirCat

[![PyPI version](https://badge.fury.io/py/DirCat.svg)](https://badge.fury.io/py/DirCat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个简单的命令行工具，可以将整个目录的结构和文件内容递归地复制到剪切板或输出到文件，方便与 AI 进行代码分析和调试。

## 🚀 安装

通过 pip 安装：

```bash
pip install dircat
```

## ✨ 特性

-   **结构清晰**: 开头生成一个完整的目录树，结构一目了然
-   **多编码支持**: 自动尝试常见编码
-   **智能输出**: 默认复制到剪切板，但在无剪切板环境会自动保存到文件
-   **文件输出**: 使用 `-o` 选项可将所有内容直接输出到指定文件
-   **自动忽略**: **默认跳过 `.git`, `node_modules`, `__pycache__` 等常见的元数据和依赖文件夹**，无需手动排除
-   **可配置忽略**: 使用 `-n/--exclude` 永久写入 `.dircatignore`，或 `-i/--ignore-temp` 临时忽略特定文件/文件夹

## 📖 使用方法

### 基本用法

在您想要复制的项目根目录下，直接运行：

```bash
dircat
```
> 默认复制到剪切板。在无 GUI 环境下，将自动保存为 `dircat_YYYYMMDD_HHMMSS.txt`。

### 输出到文件

使用 `-o` 或 `--output` 选项指定输出文件：

```bash
dircat -o project_snapshot.txt
```

### 指定目录

您也可以指定一个特定的目录路径：

```bash
dircat /path/to/your/project
```

### 排除文件或文件夹

使用 `-n` 或 `--exclude` 选项，永久添加忽略规则到 .dircatignore 文件中，支持通配符：

```bash
# 排除 build 文件夹和所有 .log 文件
dircat -n "build/" "*.log"
```

### 临时忽略文件或文件夹

使用 `-i` 或 `--ignore-temp` 选项，可以临时忽略某些文件或文件夹，而不会将其添加到 `.dircatignore` 文件中。

```bash
# 本次运行忽略 build 文件夹和所有 .log 文件
dircat -i "build/" "*.log"
```

### 调整项目数量限制
默认情况下，如果一个文件夹下的文件和子文件夹总数超过 20，该文件夹将被跳过。您可以使用 `--max-items` 选项来修改这个限制：
```bash
dircat --max-items 30
```

## 📄 许可证

本项目根据 MIT 许可证授权。详情请参阅 `LICENSE` 文件。
