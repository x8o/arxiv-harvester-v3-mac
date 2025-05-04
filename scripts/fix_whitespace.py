#!/usr/bin/env python
"""
PEP 8のスタイル問題を自動修正するための
ユーティリティスクリプト。
主に以下の問題を修正します：
- 空白行の空白文字除去 (W293)
- 行末の空白除去 (W291)
- ファイル末尾の余分な空行修正 (W391)
"""

import os
import sys


def fix_whitespace_issues(file_path):
    """ファイル内の空白関連の問題を修正する"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove trailing whitespace
    lines = [line.rstrip() + '\n' for line in lines]

    # Remove blank lines with whitespace
    for i in range(len(lines)):
        if lines[i].strip() == '':
            lines[i] = '\n'

    # Fix end of file (ensure exactly one newline at the end)
    if lines and lines[-1].strip() == '':
        while len(lines) > 1 and lines[-2].strip() == '':
            lines.pop()

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return True


def process_directory(directory):
    """
    指定されたディレクトリ内の
    ファイルの空白問題を修正する
    """
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.md'):
                file_path = os.path.join(root, file)
                original = open(file_path, 'r', encoding='utf-8').read()
                fix_whitespace_issues(file_path)
                new = open(file_path, 'r', encoding='utf-8').read()
                if original != new:
                    count += 1
                    print(f"Fixed: {file_path}")

    return count


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isfile(target) and target.endswith(".py"):
            fix_whitespace_issues(target)
            print(f"Fixed: {target}")
        elif os.path.isdir(target):
            fixed = process_directory(target)
            print(f"Fixed {fixed} files in {target}")
        else:
            print(f"Error: {target} is not a Python file or directory")
    else:
        # デフォルトはカレントディレクトリ
        root_dir = os.getcwd()
        fixed = process_directory(root_dir)
        print(f"Fixed {fixed} files in {root_dir}")


if __name__ == "__main__":
    main()
