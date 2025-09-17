import pytest
from pathlib import Path
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DirCat.main import generate_tree_output

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

def test_basic_structure(test_project):
    """测试基本的目录遍历和文件内容读取。"""
    output = generate_tree_output(test_project, user_exclude=[], max_items=20)
    
    assert "📜 file1.txt" in output
    assert "hello" in output
    assert "📜 file2.py" in output
    assert "print('world')" in output
    assert "📂 sub/" in output
    assert "📜 file3.log" in output
    assert "log message" in output
    assert "📂 empty_dir/" in output
    # 默认应排除 node_modules
    assert "node_modules" not in output

def test_exclude_option(test_project):
    """测试 -n/--exclude 命令行参数。"""
    output = generate_tree_output(test_project, user_exclude=["*.log", "sub"], max_items=20)
    
    assert "📜 file1.txt" in output
    assert "sub/" not in output
    assert "file3.log" not in output

def test_dircatignore_file(test_project):
    """测试 .dircatignore 文件。"""
    (test_project / ".dircatignore").write_text("*.py\nempty_dir/")
    
    output = generate_tree_output(test_project, user_exclude=[], max_items=20)
    
    assert "📜 file1.txt" in output
    assert "file2.py" not in output
    assert "empty_dir/" not in output

def test_max_items_limit(test_project):
    """测试 --max-items 参数。"""
    for i in range(5):
        (test_project / f"extra_file_{i}.txt").write_text(f"extra {i}")
        
    output = generate_tree_output(test_project, user_exclude=[], max_items=4)
    
    assert "因为包含超过 4 个项目而被跳过" in output
    # 跳过后，不应包含任何文件或子目录的详细信息
    assert "file1.txt" not in output
    assert "sub/" not in output

def test_language_detection(test_project):
    """测试代码块中的语言标识符。"""
    output = generate_tree_output(test_project, user_exclude=[], max_items=20)
    
    # 检查 file2.py 的内容是否被 python 代码块包围
    assert "```python\n" in output
    assert "print('world')" in output
    # 检查 file1.txt 的内容是否被没有语言标识符的代码块包围
    assert "```\n" in output
    assert "hello" in output
