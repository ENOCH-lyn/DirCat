# DirCat

[![PyPI version](https://badge.fury.io/py/DirCat.svg)](https://badge.fury.io/py/DirCat)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个简单的命令行工具，可以将整个目录的结构和文件内容递归地复制到剪切板中，方便与 AI 进行代码分析和调试。

## 🚀 安装

通过 pip 安装：

```bash
pip install DirCat
```

## ✨ 特性

-   **一键复制**: 在任何目录下运行，即可将整个项目结构和代码复制到剪贴板。
-   **智能过滤**: 自动跳过包含过多文件的目录 (例如 `node_modules`)，保持输出的简洁性。
-   **自动忽略**: **默认跳过 `.git`, `node_modules`, `__pycache__` 等常见的元数据和依赖文件夹**，无需手动排除。
-   **自定义排除**: 使用 `-n` 选项可以轻松排除您想忽略的任何其他文件或文件夹。

## 📖 使用方法

### 基本用法

在您想要复制的项目根目录下，直接运行：

```bash
dircat
```

### 指定目录

您也可以指定一个特定的目录路径：

```bash
dircat /path/to/your/project
```

### 排除文件或文件夹

如果您想排除列表之外的特定文件或文件夹，可以使用 `-n` 选项。

```bash
# 这将排除 output 文件夹和 my_secret.txt 文件
dircat -n output my_secret.txt
```

### 调整项目数量限制

默认情况下，如果一个文件夹下的文件和子文件夹总数超过 20，该文件夹将被跳过。您可以使用 `--max-items` 选项来修改这个限制：

```bash
dircat --max-items 30
```

## 📄 许可证

本项目根据 MIT 许可证授权。
