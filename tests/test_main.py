import pytest
from pathlib import Path
import os
import sys
from unittest.mock import patch, MagicMock
import pyperclip # 导入以使用异常

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.DirCat.main import generate_tree_output, main

@pytest.fixture
def test_project(tmp_path):
    """创建一个临时的目录结构用于测试。"""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / "file1.txt").write_text("hello")
    (project_root / "file2.py").write_text("print('world')")
    
    sub_dir = project_root / "sub"
    sub_dir.mkdir()
    (sub_dir / "file3.log").write_text("log message")
    
    empty_dir = project_root / "empty_dir"
    empty_dir.mkdir()
    
    # 用于测试排除的文件夹
    node_modules = project_root / "node_modules"
    node_modules.mkdir()
    (node_modules / "some_lib.js").write_text("lib code")

    return project_root

def test_basic_structure_and_tree(test_project):
    """测试基本的目录遍历、树状结构和文件内容读取。"""
    output = generate_tree_output(str(test_project), user_exclude=[], max_items=20)
    
    # 检查树状结构
    assert "📜 file1.txt" in output
    assert "📂 sub/" in output
    assert "📜 file3.log" in output
    
    # 检查文件内容分隔符和标题
    assert "--- 文件内容 ---" in output
    assert "--- 文件: file1.txt ---" in output
    assert "--- 文件: file2.py ---" in output
    
    # 检查文件内容
    assert "hello" in output
    assert "print('world')" in output
    
    # 默认应排除 node_modules
    assert "node_modules" not in output

def test_exclude_option(test_project):
    """测试 -n/--exclude 命令行参数。"""
    output = generate_tree_output(str(test_project), user_exclude=["*.log", "sub/"], max_items=20)
    
    assert "📜 file1.txt" in output
    assert "sub/" not in output
    assert "file3.log" not in output

def test_dircatignore_file(test_project):
    """测试 .dircatignore 文件。"""
    (test_project / ".dircatignore").write_text("*.py\nempty_dir/")
    
    output = generate_tree_output(str(test_project), user_exclude=[], max_items=20)
    
    assert "📜 file1.txt" in output
    assert "file2.py" not in output
    assert "empty_dir/" not in output
    assert ".dircatignore" not in output # 自身也应该被排除

def test_max_items_limit(test_project):
    """测试 --max-items 参数。"""
    for i in range(5):
        (test_project / f"extra_file_{i}.txt").write_text(f"extra {i}")
        
    output = generate_tree_output(str(test_project), user_exclude=[], max_items=4)
    
    assert "因为包含超过 4 个项目而被跳过" in output
    assert "--- 文件内容 ---" not in output # 跳过后不应有文件内容部分

def test_language_detection(test_project):
    """测试代码块中的语言标识符。"""
    output = generate_tree_output(str(test_project), user_exclude=[], max_items=20)
    
    assert "--- 文件: file2.py ---" in output
    assert "```python\nprint('world')\n```" in output
    
    assert "--- 文件: file1.txt ---" in output
    assert "```\nhello\n```" in output


def test_encoding_detection_multiple_files(tmp_path):
    """测试不同编码类型的文件能被自动检测并正确读取。"""
    project_root = tmp_path / "encoding_project"
    project_root.mkdir()

    gbk_file = project_root / "gbk.txt"
    gbk_content = "你好，世界"
    gbk_file.write_bytes(gbk_content.encode('gbk'))

    utf16_file = project_root / "utf16.txt"
    utf16_content = "Hello UTF16"
    utf16_file.write_text(utf16_content, encoding='utf-16')

    utf8_file = project_root / "utf8.txt"
    utf8_content = "plain utf8"
    utf8_file.write_text(utf8_content, encoding='utf-8')

    output = generate_tree_output(str(project_root), user_exclude=[], max_items=20)

    assert "📜 gbk.txt" in output
    assert gbk_content in output

    assert "📜 utf16.txt" in output
    assert utf16_content in output

    assert "📜 utf8.txt" in output
    assert utf8_content in output

@patch('src.DirCat.main.pyperclip')
def test_output_to_clipboard(mock_pyperclip, test_project, capsys):
    """测试默认输出到剪切板。"""
    with patch('sys.argv', ['dircat', str(test_project)]):
        main()
    
    mock_pyperclip.copy.assert_called_once()
    captured = capsys.readouterr()
    assert "已成功复制到剪切板" in captured.out

@patch('src.DirCat.main.pyperclip.copy', side_effect=pyperclip.PyperclipException)
def test_clipboard_fallback_to_file(mock_copy, test_project, capsys):
    """测试在没有剪切板的环境下回退到文件输出。"""
    with patch('sys.argv', ['dircat', str(test_project)]):
        main()
    
    captured = capsys.readouterr()
    assert "未检测到剪切板环境" in captured.out
    assert "输出已自动保存到文件" in captured.out
    
    # 检查文件是否已创建
    output_file = [f for f in os.listdir() if f.startswith('dircat_') and f.endswith('.txt')]
    assert len(output_file) == 1
    os.remove(output_file[0]) # 清理测试文件

def test_output_to_file_option(test_project, tmp_path, capsys):
    """测试 -o/--output 参数。"""
    output_path = tmp_path / "output.txt"
    with patch('sys.argv', ['dircat', str(test_project), '-o', str(output_path)]):
        main()
        
    captured = capsys.readouterr()
    assert f"已成功保存到文件: {output_path}" in captured.out
    assert output_path.read_text(encoding='utf-8') != ""

def test_combined_options(test_project, tmp_path, capsys):
    """测试组合使用多个选项 (-n, -i, -o)。"""
    output_path = tmp_path / "combined_output.txt"
    
    # 模拟运行: dircat <path> -n "*.log" -i "*.py" -o <output_path>
    with patch('sys.argv', [
        'dircat', 
        str(test_project), 
        '-n', '*.log',          # 永久忽略 .log
        '-i', '*.py', 'sub/',   # 临时忽略 .py 和 sub/
        '-o', str(output_path)
    ]):
        main()

    # 1. 验证 -n 的效果：.dircatignore 文件被创建/更新
    ignore_file = test_project / '.dircatignore'
    assert ignore_file.is_file()
    assert '*.log' in ignore_file.read_text(encoding='utf-8')
    
    # 2. 验证 -o 的效果：输出到指定文件
    captured = capsys.readouterr()
    assert f"已成功保存到文件: {output_path}" in captured.out
    
    # 3. 验证 -i 的效果：输出内容被正确地临时过滤
    output_content = output_path.read_text(encoding='utf-8')
    assert 'file1.txt' in output_content  # 应该存在
    assert 'file2.py' not in output_content  # 被临时忽略
    assert 'sub/' not in output_content      # 被临时忽略
    
    # 4. 验证 -n 的效果也立即生效
    assert 'file3.log' not in output_content # 被永久忽略


def test_dircatignore_append_preserves_encoding(tmp_path, capsys):
    """测试对非 UTF-8 编码的 .dircatignore 追加规则时保持原有编码。"""
    project_root = tmp_path / "encoding_project"
    project_root.mkdir()

    # 创建一个包含非 ASCII 内容的 gbk 编码 .dircatignore
    ignore_path = project_root / '.dircatignore'
    original_text = "初始模式\n"
    ignore_path.write_bytes(original_text.encode('gbk'))

    # 准备最小化的项目结构以便 main 正常运行
    sample_file = project_root / 'sample.txt'
    sample_file.write_text('content', encoding='utf-8')

    output_path = tmp_path / 'encoding_output.txt'

    with patch('sys.argv', ['dircat', str(project_root), '-n', '*.tmp', '-o', str(output_path)]):
        main()

    capsys.readouterr()  # 清理输出，避免影响后续断言

    # 断言 .dircatignore 仍可用 gbk 正确解码并包含新规则
    updated_bytes = ignore_path.read_bytes()
    decoded_content = updated_bytes.decode('gbk')

    assert '初始模式' in decoded_content
    assert '*.tmp' in decoded_content

    # 确保输出文件被创建，避免剪贴板路径
    assert output_path.is_file()
