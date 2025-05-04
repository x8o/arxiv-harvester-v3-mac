#!/usr/bin/env python
"""
PEP 8u306eu30b9u30bfu30a4u30ebu554fu984cu3092u81eau52d5u4feeu6b63u3059u308bu305fu3081u306eu30e6u30fcu30c6u30a3u30eau30c6u30a3u30b9u30afu30eau30d7u30c8u3002
u4e3bu306bu4ee5u4e0bu306eu554fu984cu3092u4feeu6b63u3057u307eu3059uff1a
- u7a7au767du884cu306eu7a7au767du6587u5b57u9664u53bb (W293)
- u884cu672bu306eu7a7au767du9664u53bb (W291)
- u30d5u30a1u30a4u30ebu672bu5c3eu306eu4f59u5206u306au7a7au884cu4feeu6b63 (W391)
"""

import os
import sys
from pathlib import Path

def fix_whitespace_issues(file_path):
    """u30d5u30a1u30a4u30ebu5185u306eu7a7au767du95a2u9023u306eu554fu984cu3092u4feeu6b63u3059u308b"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # u884cu672bu306eu7a7au767du3092u524au9664u3057u3001u7a7au767du884cu306eu7a7au767du6587u5b57u3092u524au9664
    fixed_lines = [line.rstrip() + '\n' if line.strip() else '\n' for line in lines]
    
    # u30d5u30a1u30a4u30ebu672bu5c3eu306eu4f59u5206u306au7a7au884cu3092u6700u59271u884cu306bu5236u9650
    while len(fixed_lines) > 1 and fixed_lines[-1] == '\n' and fixed_lines[-2] == '\n':
        fixed_lines.pop()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    return True

def process_directory(directory):
    """u30c7u30a3u30ecu30afu30c8u30eau5185u306ePythonu30d5u30a1u30a4u30ebu3092u518du5e30u7684u306bu51e6u7406"""
    fixed_files = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if fix_whitespace_issues(file_path):
                    fixed_files += 1
                    print(f"Fixed: {file_path}")
    
    return fixed_files

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
