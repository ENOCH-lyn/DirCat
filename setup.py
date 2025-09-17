from setuptools import setup, find_packages
import os
import re

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join('src', package, '__init__.py'), encoding="utf-8").read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)

version = get_version('DirCat')


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="DirCat",
    version=version,
    author="ENOCH",
    author_email="enoch@enoch.host",
    description="一个将目录结构和文件内容复制到剪切板的工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ENOCH-lyn/DirCat",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'pyperclip',
    ],
    entry_points={
        'console_scripts': [
            'dircat=DirCat.main:main',
        ],
    },
)