import os
import argparse
import pyperclip
from pathlib import Path
import fnmatch

# 默认排除的文件和文件夹模式
DEFAULT_EXCLUDE_PATTERNS = {
    # 版本控制
    '.git',
    '.svn',
    '.gitignore',
    '.gitattributes',

    # IDE 和编辑器文件夹
    '.vscode',
    '.idea',

    # Python 相关
    '__pycache__',
    '*.pyc',
    '*.egg-info',
    'build',
    'dist',
    '.pytest_cache',
    '.tox',
    '.env',

    # Node.js
    'node_modules',

    # 操作系统生成的文件
    '.DS_Store',
    
}

LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java',
    '.c': 'c', '.cpp': 'cpp', '.cs': 'csharp', '.go': 'go', '.rs': 'rust',
    '.php': 'php', '.rb': 'ruby', '.kt': 'kotlin', '.swift': 'swift',
    '.html': 'html', '.css': 'css', '.json': 'json', '.xml': 'xml',
    '.md': 'markdown', '.sh': 'shell', '.yml': 'yaml', '.yaml': 'yaml'
}


def _get_ignore_patterns(root_path):
    """从 .dircatignore 文件加载忽略模式."""
    ignore_file = Path(root_path) / '.dircatignore'
    patterns = set()
    if ignore_file.is_file():
        with open(ignore_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.add(line)
    return patterns


def _read_file_content(file_path, sub_indent):
    """读取并格式化单个文件的内容."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            lang = LANGUAGE_MAP.get(file_path.suffix, '')
            indented_content = '\n'.join([f"{sub_indent}{line}" for line in content.splitlines()])
            return f"{sub_indent}```{lang}\n{indented_content}\n{sub_indent}```\n\n"
    except UnicodeDecodeError:
        return f"{sub_indent}*** 无法以 UTF-8 格式读取二进制文件 ***\n\n"
    except IOError as e:
        return f"{sub_indent}*** 无法读取文件: {e} ***\n\n"


def _is_excluded(path, patterns, base_path):
    """检查路径是否匹配任何忽略模式。"""
    relative_path_str = str(path.relative_to(base_path))
    path_name = path.name
    
    for pattern in patterns:
        if pattern.endswith('/'):
            if path.is_dir() and (relative_path_str + '/').startswith(pattern):
                return True
        elif fnmatch.fnmatch(path_name, pattern):
            return True
        elif fnmatch.fnmatch(relative_path_str, pattern):
            return True
            
    return False

def generate_tree_output(root_path, user_exclude, max_items):
    """
    递归地获取目录结构和文件内容。
    """
    output = []
    base_path = Path(root_path)
    
    cli_patterns = set(user_exclude)
    file_patterns = _get_ignore_patterns(base_path)
    all_exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.union(cli_patterns).union(file_patterns).union({'.dircatignore'})

    for root, dirs, files in os.walk(base_path, topdown=True):
        current_path = Path(root)
        
        dirs[:] = [d for d in dirs if not _is_excluded(current_path / d, all_exclude_patterns, base_path)]
        files[:] = [f for f in files if not _is_excluded(current_path / f, all_exclude_patterns, base_path)]

        if len(dirs) + len(files) > max_items:
            rel_path = current_path.relative_to(base_path)
            output.append(f"--- 文件夹 '{rel_path}' 因为包含超过 {max_items} 个项目而被跳过 ---\n")
            dirs[:] = []
            continue

        level = len(current_path.relative_to(base_path).parts)
        indent = ' ' * 4 * level
        if current_path != base_path:
            output.append(f"{indent}📂 {current_path.name}/\n")
        
        sub_indent = ' ' * 4 * (level + 1)
        for f_name in files:
            output.append(f"{sub_indent}📜 {f_name}\n")
            file_path = current_path / f_name
            output.append(_read_file_content(file_path, sub_indent))

    return "".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="将目录结构和文件内容复制到剪切板，以便给 AI 进行分析。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help="要处理的目录路径，默认为当前目录。"
    )
    parser.add_argument(
        '-n', '--exclude',
        nargs='*',
        default=[],
        help="指定要排除的文件或文件夹名称/模式，例如: *.log my_folder"
    )
    parser.add_argument(
        '--max-items',
        type=int,
        default=20,
        help="如果一个文件夹下的文件和子文件夹总数超过此数量，则跳过该文件夹。默认值为 20。"
    )

    args = parser.parse_args()
    target_path = Path(args.path).resolve()

    try:
        structure = generate_tree_output(target_path, args.exclude, args.max_items)
        pyperclip.copy(structure)
        print("✅ 目录结构和文件内容已成功复制到剪切板！")
    except FileNotFoundError:
        print(f"❌ 错误：找不到指定的路径 '{target_path}'")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


if __name__ == "__main__":
    main()