#!/usr/bin/env python
"""
PEP 8u306eu30b9u30bfu30a4u30ebu554fu984cu3092u81eau52d5u4feeu6b63u3059u308bu305fu3081u306e
u30e6u30fcu30c6u30a3u30eau30c6u30a3u30b9u30afu30eau30d7u30c8u3002
u4e3bu306bu4ee5u4e0bu306eu554fu984cu3092u4feeu6b63u3057u307eu3059uff1a
- u7a7au767du884cu306eu7a7au767du6587u5b57u9664u53bb (W293)
- u884cu672bu306eu7a7au767du9664u53bb (W291)
- u30d5u30a1u30a4u30ebu672bu5c3eu306eu4f59u5206u306au7a7au884cu4feeu6b63 (W391)
"""

import os
import sys


def fix_whitespace_issues(file_path):
    """u30d5u30a1u30a4u30ebu5185u306eu7a7au767du95a2u9023u306eu554fu984cu3092u4feeu6b63u3059u308b"""
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
    """u6307u5b9au3055u308cu305fu30c7u30a3u30ecu30afu30c8u30eau5185u306eu30d5u30a1u30a4u30ebu306eu7a7au767du554fu984cu3092u4feeu6b63u3059u308b"""
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
    """u30e1u30a4u30f3u95a2u6570"""
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
        # u30c7u30d5u30a9u30ebu30c8u306fu30abu30ecu30f3u30c8u30c7u30a3u30ecu30afu30c8u30ea
        root_dir = os.getcwd()
        fixed = process_directory(root_dir)
        print(f"Fixed {fixed} files in {root_dir}")


if __name__ == "__main__":
    main()
