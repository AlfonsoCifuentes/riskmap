import sys
import re

if len(sys.argv) < 2:
    print('Usage: python debug_js_block.py <file>')
    sys.exit(1)

file_path = sys.argv[1]

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f'Found {len(script_blocks)} script blocks')

# Focus on first block
for idx, block in enumerate(script_blocks, 1):
    print(f'\n--- Block {idx} length:', len(block))
    preview = block[:300].replace('\n', '\\n')
    print(preview)
    print('---')
    # Continue with checks only on non-empty blocks
    if len(block.strip()) == 0:
        continue

    single_quotes = block.count("'")
    double_quotes = block.count('"')
    backticks = block.count('`')
    open_braces = block.count('{')
    close_braces = block.count('}')
    open_paren = block.count('(')
    close_paren = block.count(')')

    print('--- Stats ---')
    print('single_quotes:', single_quotes)
    print('double_quotes:', double_quotes)
    print('backticks:', backticks)
    print('open_braces:', open_braces, 'close_braces:', close_braces)
    print('open_paren:', open_paren, 'close_paren:', close_paren)

# Attempt to find the line number with unmatched brace or quote scanning character by character

stack = []
line_num = 0
in_single = False
in_double = False
in_backtick = False
escape = False

for i, line in enumerate(block.splitlines(), 1):
    for c in line:
        if escape:
            escape = False
            continue
        if c == '\\':
            escape = True
            continue
        if in_single:
            if c == "'":
                in_single = False
            continue
        if in_double:
            if c == '"':
                in_double = False
            continue
        if in_backtick:
            if c == '`':
                in_backtick = False
            continue
        if c == "'":
            in_single = True
        elif c == '"':
            in_double = True
        elif c == '`':
            in_backtick = True
        elif c == '{':
            stack.append('{')
        elif c == '}':
            if not stack:
                print(f'Unmatched closing brace at line {i}')
            else:
                stack.pop()

if in_single:
    print('Unclosed single quote')
if in_double:
    print('Unclosed double quote')
if in_backtick:
    print('Unclosed backtick')
if stack:
    print('Unclosed braces count:', len(stack))

# Print lines around last brace
for i, line in enumerate(block.splitlines(), 1):
    if '{' in line or '}' in line:
        print(i, line)

print('Done')
