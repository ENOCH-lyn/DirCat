import os
import argparse
import pyperclip
from pathlib import Path
import fnmatch
from datetime import datetime
from .config import DEFAULT_EXCLUDE_PATTERNS, LANGUAGE_MAP


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


def _read_file_content(file_path, base_path):
    """读取并格式化单个文件的内容,在前面加上文件路径标题。"""
    relative_path = file_path.relative_to(base_path)
    header = f"--- 文件: {relative_path.as_posix()} ---\n"
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            lang = LANGUAGE_MAP.get(file_path.suffix, '')
            return f"{header}{lang}\n{content}\n\n"
    except UnicodeDecodeError:
        return f"{header}*** 无法以 UTF-8 格式读取二进制文件 ***\n\n"
    except IOError as e:
        return f"{header}*** 无法读取文件: {e} ***\n\n"


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
    递归地获取目录结构和文件内容,首先显示树形结构,然后是文件内容。
    """
    tree_lines = []
    content_lines = []
    base_path = Path(root_path)
    
    cli_patterns = set(user_exclude)
    file_patterns = _get_ignore_patterns(base_path)
    all_exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.union(cli_patterns).union(file_patterns).union({'.dircatignore'})

    files_to_read = []

    for root, dirs, files in os.walk(base_path, topdown=True):
        current_path = Path(root)
        
        dirs[:] = [d for d in dirs if not _is_excluded(current_path / d, all_exclude_patterns, base_path)]
        files[:] = [f for f in files if not _is_excluded(current_path / f, all_exclude_patterns, base_path)]

        if len(dirs) + len(files) > max_items:
            rel_path = current_path.relative_to(base_path)
            tree_lines.append(f"--- 文件夹 '{rel_path}' 因为包含超过 {max_items} 个项目而被跳过 ---\n")
            dirs[:] = []
            continue

        level = len(current_path.relative_to(base_path).parts)
        indent = ' ' * 4 * level
        if current_path != base_path:
            tree_lines.append(f"{indent}📂 {current_path.name}/\n")
        
        sub_indent = ' ' * 4 * (level + 1)
        for f_name in sorted(files):
            tree_lines.append(f"{sub_indent}📜 {f_name}\n")
            files_to_read.append(current_path / f_name)

    if files_to_read:
        content_lines.append("\n--- 文件内容 ---\n\n")
        for file_path in files_to_read:
            content_lines.append(_read_file_content(file_path, base_path))

    return "".join(tree_lines) + "".join(content_lines)

def main():
    parser = argparse.ArgumentParser(
        description="将目录结构和文件内容复制到剪切板或输出到文件，以便给 AI 进行分析。",
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
        help="永久添加忽略规则到 .dircatignore 文件中。"
    )
    parser.add_argument(
        '-i', '--ignore-temp',
        nargs='*',
        default=[],
        help="临时忽略文件或文件夹，仅对本次运行生效。"
    )
    parser.add_argument(
        '--max-items',
        type=int,
        default=20,
        help="如果一个文件夹下的文件和子文件夹总数超过此数量，则跳过该文件夹。默认值为 20。"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help="指定输出文件的路径。如果未提供，则默认复制到剪切板。"
    )

    args = parser.parse_args()
    target_path = Path(args.path).resolve()

    if args.exclude:
        ignore_file_path = target_path / '.dircatignore'
        newly_added = []
        
        try:
            existing_patterns = set(ignore_file_path.read_text(encoding='utf-8').splitlines()) if ignore_file_path.is_file() else set()
            
            with open(ignore_file_path, 'a', encoding='utf-8') as f:
                for pattern in args.exclude:
                    if pattern not in existing_patterns:
                        f.write(f"\n{pattern}")
                        newly_added.append(pattern)
            
            if newly_added:
                print(f"✨ 已经将规则自动写入 .dircatignore 文件")
        except IOError as e:
            print(f"⚠️ 警告：无法写入 .dircatignore 文件: {e}")

    try:
        # 将临时忽略规则传递给生成函数
        structure = generate_tree_output(target_path, args.ignore_temp, args.max_items)
        
        if args.output:
            # 如果指定了输出文件
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(structure)
            print(f"✅ 目录结构和文件内容已成功保存到文件: {args.output}")
        else:
            # 否则，尝试复制到剪切板，如果失败则回退到文件
            try:
                pyperclip.copy(structure)
                print("✅ 目录结构和文件内容已成功复制到剪切板！")
            except pyperclip.PyperclipException:
                # 剪切板不可用，自动保存到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                fallback_filename = f"dircat_{timestamp}.txt"
                with open(fallback_filename, 'w', encoding='utf-8') as f:
                    f.write(structure)
                print("📋 警告：未检测到剪切板环境。")
                print(f"✅ 输出已自动保存到文件: {fallback_filename}")

    except FileNotFoundError:
        print(f"❌ 错误：找不到指定的路径 '{target_path}'")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


if __name__ == "__main__":
    main()