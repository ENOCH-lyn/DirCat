import os
import argparse
import pyperclip
from pathlib import Path
import fnmatch
from datetime import datetime
from .config import DEFAULT_EXCLUDE_PATTERNS, LANGUAGE_MAP


DEFAULT_ENCODING_CANDIDATES = [
    'utf-8',
    'utf-8-sig',
    'gb18030',
    'gbk',
    'big5',
    'shift_jis',
    'latin-1'
]


def _detect_bom_encoding(file_path: Path):
    """检测文件的 BOM 并返回首选编码,未检测到则返回 None。"""
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(4)
    except IOError:
        return None

    if raw.startswith(b'\xff\xfe\x00\x00'):
        return 'utf-32'
    if raw.startswith(b'\x00\x00\xfe\xff'):
        return 'utf-32'
    if raw.startswith(b'\xff\xfe'):
        return 'utf-16'
    if raw.startswith(b'\xfe\xff'):
        return 'utf-16'
    if raw.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    return None


def _prepare_encoding_sequence(file_path: Path, fallback_candidates=None):
    """根据 BOM 优先级构建编码尝试顺序。"""
    fallback_candidates = fallback_candidates or DEFAULT_ENCODING_CANDIDATES
    sequence = []

    bom_encoding = _detect_bom_encoding(file_path)
    if bom_encoding:
        sequence.append(bom_encoding)

    for encoding in fallback_candidates:
        if encoding not in sequence:
            sequence.append(encoding)

    return sequence


def _get_ignore_patterns(root_path, encodings=None):
    """从 .dircatignore 文件加载忽略模式,逐个尝试提供的编码."""
    ignore_file = Path(root_path) / '.dircatignore'
    if not ignore_file.is_file():
        return set()

    encodings = encodings or DEFAULT_ENCODING_CANDIDATES

    for encoding in _prepare_encoding_sequence(ignore_file, encodings):
        try:
            with open(ignore_file, 'r', encoding=encoding) as f:
                patterns = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.add(line)
                return patterns
        except UnicodeDecodeError:
            continue
        except IOError:
            break

    return set()


def _read_file_content(file_path, base_path, encodings=None):
    """读取并格式化单个文件的内容,在前面加上文件路径标题,支持多编码。"""
    encodings = encodings or DEFAULT_ENCODING_CANDIDATES
    relative_path = file_path.relative_to(base_path)
    header = f"--- 文件: {relative_path.as_posix()} ---\n"
    
    # 先检查是否为二进制文件（在尝试文本解码前）
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            
            # 检查是否有文本编码的 BOM，如果有则不是二进制
            has_text_bom = (
                chunk.startswith(b'\xff\xfe') or  # UTF-16 LE
                chunk.startswith(b'\xfe\xff') or  # UTF-16 BE
                chunk.startswith(b'\xff\xfe\x00\x00') or  # UTF-32 LE
                chunk.startswith(b'\x00\x00\xfe\xff') or  # UTF-32 BE
                chunk.startswith(b'\xef\xbb\xbf')  # UTF-8 BOM
            )
            
            # 如果有文本 BOM，跳过二进制检查
            if not has_text_bom:
                # 检查是否包含空字节，这是二进制文件的明确标志
                if b'\x00' in chunk:
                    file_size = file_path.stat().st_size
                    size_str = f"{file_size:,} bytes" if file_size < 1024 else f"{file_size / 1024:.2f} KB"
                    return f"{header}*** 二进制文件 ({size_str}) ***\n\n"
    except:
        pass
    
    # 尝试用所有编码读取文本文件
    for encoding in _prepare_encoding_sequence(file_path, encodings):
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                lang = LANGUAGE_MAP.get(file_path.suffix, '')
                opening = f"```{lang}\n" if lang else "```\n"
                return f"{header}{opening}{content}\n```\n\n"
        except UnicodeDecodeError:
            continue
        except IOError as e:
            return f"{header}*** 无法读取文件: {e} ***\n\n"
    
    # 如果不是明显的二进制文件，返回编码失败提示
    return f"{header}*** 无法使用以下编码读取文件: {', '.join(encodings)} ***\n\n"


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

def _build_tree_recursive(current_path, base_path, all_exclude_patterns, max_items, 
                          prefix="", is_last=True, files_to_read=None):
    """递归构建 ASCII 树形结构，返回树形字符串列表。"""
    if files_to_read is None:
        files_to_read = []
    
    lines = []
    
    # 当前目录名
    if current_path == base_path:
        lines.append(f"{current_path.name}/\n")
    
    try:
        entries = list(current_path.iterdir())
    except PermissionError:
        return lines, files_to_read
    
    # 过滤排除项
    dirs = sorted([e for e in entries if e.is_dir() and not _is_excluded(e, all_exclude_patterns, base_path)])
    files = sorted([e for e in entries if e.is_file() and not _is_excluded(e, all_exclude_patterns, base_path)])
    
    # 检查数量限制
    if len(dirs) + len(files) > max_items:
        rel_path = current_path.relative_to(base_path)
        lines.append(f"{prefix}--- 文件夹 '{rel_path}' 因为包含超过 {max_items} 个项目而被跳过 ---\n")
        return lines, files_to_read
    
    all_entries = dirs + files
    
    for i, entry in enumerate(all_entries):
        is_last_entry = (i == len(all_entries) - 1)
        connector = "└── " if is_last_entry else "├── "
        
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/\n")
            # 递归子目录
            extension = "    " if is_last_entry else "│   "
            sub_lines, files_to_read = _build_tree_recursive(
                entry, base_path, all_exclude_patterns, max_items,
                prefix + extension, is_last_entry, files_to_read
            )
            lines.extend(sub_lines)
        else:
            lines.append(f"{prefix}{connector}{entry.name}\n")
            files_to_read.append(entry)
    
    return lines, files_to_read


def generate_tree_output(root_path, user_exclude, max_items, encodings=None,
                         style="emoji", include_content=True):
    """生成目录结构(两种显示模式)和可选的文件内容。

    :param style: "emoji" 使用 📂/📜 前缀; "tree" 使用树形字符 (├─, └─)。
    :param include_content: False 时仅输出目录结构,不附带文件内容。
    """
    encodings = encodings or DEFAULT_ENCODING_CANDIDATES
    tree_lines = []
    content_lines = []
    base_path = Path(root_path)

    cli_patterns = set(user_exclude)
    file_patterns = _get_ignore_patterns(base_path, encodings)
    all_exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.union(cli_patterns).union(file_patterns).union({'.dircatignore'})

    files_to_read = []

    if style == "emoji":
        # emoji 模式：使用 os.walk
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
    else:
        # tree 模式：使用递归函数
        tree_lines, files_to_read = _build_tree_recursive(
            base_path, base_path, all_exclude_patterns, max_items
        )

    if include_content and files_to_read:
        content_lines.append("\n--- 文件内容 ---\n\n")
        for file_path in files_to_read:
            content_lines.append(_read_file_content(file_path, base_path, encodings))

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
        '--style',
        choices=['emoji', 'tree'],
        default='tree',
        help=(
            "目录显示样式: "
            "emoji = 使用 📂/📜 前缀; "
            "tree = 使用 ASCII 树形 (├──, └──)。默认: emoji。"
        )
    )
    parser.add_argument(
        '-t','--tree-only',
        action='store_true',
        help="只显示目录结构(类似 tree 命令), 不包含文件内容。"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help="指定输出文件的路径。如果未提供，则默认复制到剪切板。"
    )

    args = parser.parse_args()
    target_path = Path(args.path).resolve()

    encoding_candidates = DEFAULT_ENCODING_CANDIDATES

    if args.exclude:
        ignore_file_path = target_path / '.dircatignore'
        newly_added = []
        
        try:
            existing_patterns = set()
            file_exists = ignore_file_path.is_file()
            active_encoding = encoding_candidates[0]

            if file_exists:
                for encoding in _prepare_encoding_sequence(ignore_file_path, encoding_candidates):
                    try:
                        existing_content = ignore_file_path.read_text(encoding=encoding)
                        existing_patterns = set(line.strip() for line in existing_content.splitlines() if line.strip())
                        active_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                # 如果全部解码失败,existing_patterns 保持为空,使用首选编码写入

            patterns_to_add = []
            for pattern in args.exclude:
                pattern = pattern.strip()
                if pattern and pattern not in existing_patterns:
                    patterns_to_add.append(pattern)
                    newly_added.append(pattern)

            if patterns_to_add:
                file_size = ignore_file_path.stat().st_size if file_exists else 0
                with open(ignore_file_path, 'a', encoding=active_encoding) as f:
                    if file_size > 0:
                        f.write('\n')
                    f.write('\n'.join(patterns_to_add))
                print("已经将规则自动写入 .dircatignore 文件")
        except IOError as e:
            print(f"警告：无法写入 .dircatignore 文件: {e}")

    try:
        # 将临时忽略规则传递给生成函数
        structure = generate_tree_output(
            target_path,
            args.ignore_temp,
            args.max_items,
            encoding_candidates,
            style=args.style,
            include_content=not args.tree_only,
        )
        
        if args.output:
            # 如果指定了输出文件
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(structure)
            print(f"已成功保存到文件: {args.output}")
        else:
            # 否则，尝试复制到剪切板，如果失败则回退到文件
            try:
                pyperclip.copy(structure)
                print("已成功复制到剪切板！")
            except pyperclip.PyperclipException:
                # 剪切板不可用，自动保存到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                fallback_filename = f"dircat_{timestamp}.txt"
                with open(fallback_filename, 'w', encoding='utf-8') as f:
                    f.write(structure)
                print("警告：未检测到剪切板环境。")
                print(f"输出已自动保存到文件: {fallback_filename}")

    except FileNotFoundError:
        print(f"错误：找不到指定的路径 '{target_path}'")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    main()