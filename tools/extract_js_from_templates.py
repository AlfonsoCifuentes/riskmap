#!/usr/bin/env python3
"""
Extract inline JS blocks from templates and create files for ESLint.
"""
import os
import re
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'src', 'web', 'templates')
OUT_DIR = os.path.join(BASE_DIR, '.tmp', 'html_js')

SCRIPT_RE = re.compile(r'<script[^>]*>([\s\S]*?)<\/script>', re.IGNORECASE)


def extract_file(src_path, dest_dir):
    with open(src_path, 'r', encoding='utf8') as f:
        content = f.read()
    matches = list(SCRIPT_RE.finditer(content))
    out_files = []
    if not matches:
        return out_files
    # Ensure destination
    os.makedirs(dest_dir, exist_ok=True)

    for i, m in enumerate(matches):
        js = m.group(1).strip()
        if not js:
            continue
        # Remove Jinja template delimiters for minimal linting
        cleaned = re.sub(r'\{\%[\s\S]*?\%\}', '', js)
        cleaned = re.sub(r'\{\{[\s\S]*?\}\}', '""', cleaned)

        name = os.path.splitext(os.path.basename(src_path))[0]
        out_path = os.path.join(dest_dir, f"{name}_block_{i}.js")
        with open(out_path, 'w', encoding='utf8') as out_f:
            out_f.write('// Extracted from: ' + src_path + '\n')
            out_f.write(cleaned)
        out_files.append(out_path)
    return out_files


def main(path):
    if os.path.exists(OUT_DIR):
        # Clear out dir
        for f in os.listdir(OUT_DIR):
            os.remove(os.path.join(OUT_DIR, f))
    os.makedirs(OUT_DIR, exist_ok=True)

    for root, dirs, files in os.walk(path):
        for fn in files:
            if fn.endswith('.html'):
                full = os.path.join(root, fn)
                extract_file(full, OUT_DIR)

    print('JS extracted to', OUT_DIR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--templates', default=TEMPLATES_DIR, help='Path to templates directory')
    args = parser.parse_args()
    main(args.templates)
