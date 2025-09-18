# 默认排除的文件和文件夹模式
DEFAULT_EXCLUDE_PATTERNS = {
    # 版本控制
    '.git',
    '.svn',
    '.hg',
    '.gitignore',
    '.gitattributes',

    # IDE 和编辑器配置
    '.vscode',
    '.idea',
    '*.suo',
    '*.ntvs*',
    '*.njsproj',
    '*.sln',
    '*.swp', # Vim swap file

    # Python 相关
    '__pycache__/',
    '*.py[cod]',
    '*.egg-info/',
    'build/',
    'dist/',
    '.pytest_cache/',
    '.tox/',
    '.env',
    '.venv',
    'env/',
    'venv/',
    'htmlcov/', # Coverage reports
    'instance/', # Flask instance folder

    # Node.js
    'node_modules/',
    'package-lock.json',
    'yarn.lock',
    '.npm',

    # Java / Maven / Gradle
    'target/',
    '.gradle',

    # C/C++ 编译产物
    '*.o',
    '*.a',
    '*.so',
    '*.lib',
    '*.dll',
    '*.exe',

    # 操作系统和临时文件
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    '__MACOSX/',
    '*.tmp',
    '*.bak',
    
    # 压缩文件
    '*.zip',
    '*.tar',
    '*.gz',
    '*.rar',
    '*.7z',
}

# 文件扩展名到语言的映射
LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java',
    '.c': 'c', '.cpp': 'cpp', '.cs': 'csharp', '.go': 'go', '.rs': 'rust',
    '.php': 'php', '.rb': 'ruby', '.kt': 'kotlin', '.swift': 'swift',
    '.html': 'html', '.css': 'css', '.json': 'json', '.xml': 'xml',
    '.md': 'markdown', '.sh': 'shell', '.yml': 'yaml', '.yaml': 'yaml'
}
