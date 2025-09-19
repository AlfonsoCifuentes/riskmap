#!/usr/bin/env python3
"""
Script to extract and validate JavaScript from dashboard_BUENO.html
"""
import re
import os

def extract_javascript_from_html(html_file):
    """Extract JavaScript code from HTML file"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all script tags and their content
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, content, re.DOTALL)
        
        js_code = ""
        for script in scripts:
            js_code += script + "\n"
        
        # Also extract inline JavaScript (event handlers, etc.)
        onclick_pattern = r'onclick="([^"]*)"'
        onclicks = re.findall(onclick_pattern, content)
        
        return js_code, onclicks
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return "", []

def check_bracket_balance(js_code):
    """Check if brackets are balanced"""
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    line_num = 1
    char_pos = 0
    
    for char in js_code:
        char_pos += 1
        if char == '\n':
            line_num += 1
            char_pos = 0
            
        if char in brackets:
            stack.append((char, line_num, char_pos))
        elif char in brackets.values():
            if not stack:
                print(f"ERROR: Unmatched closing bracket '{char}' at line {line_num}, position {char_pos}")
                return False
            
            last_bracket, last_line, last_pos = stack.pop()
            expected = brackets[last_bracket]
            if char != expected:
                print(f"ERROR: Mismatched bracket. Expected '{expected}' but found '{char}' at line {line_num}, position {char_pos}")
                print(f"       Opening bracket '{last_bracket}' was at line {last_line}, position {last_pos}")
                return False
    
    if stack:
        for bracket, line, pos in stack:
            print(f"ERROR: Unclosed bracket '{bracket}' at line {line}, position {pos}")
        return False
    
    return True

def find_syntax_errors(js_code):
    """Find common JavaScript syntax errors"""
    errors = []
    lines = js_code.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for common syntax issues
        line_stripped = line.strip()
        
        # Check for standalone closing brackets at wrong positions
        if line_stripped == '}' and i > 1:
            prev_line = lines[i-2].strip() if i > 1 else ""
            if prev_line.endswith(');') or prev_line.endswith('});'):
                # This might be an extra closing bracket
                context_start = max(0, i-5)
                context_end = min(len(lines), i+3)
                context = lines[context_start:context_end]
                
                print(f"POTENTIAL ERROR at line {i}: Standalone '}}' - check context:")
                for j, ctx_line in enumerate(context, context_start + 1):
                    marker = " --> " if j == i else "     "
                    print(f"{marker}{j:4d}: {ctx_line}")
                print()
        
        # Check for missing semicolons before }
        if line_stripped.endswith('}') and not line_stripped.endswith(';}') and not line_stripped.endswith('});'):
            prev_line = lines[i-2].strip() if i > 1 else ""
            if prev_line and not prev_line.endswith(';') and not prev_line.endswith('{') and not prev_line.endswith('}'):
                errors.append(f"Line {i-1}: Missing semicolon before closing bracket")
        
        # Check for missing commas in arrays/objects
        if ',' in line and not line_stripped.endswith(',') and not line_stripped.endswith(';'):
            if i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('}') or next_line.startswith(']'):
                    errors.append(f"Line {i}: Possible trailing comma issue")
    
    return errors

def main():
    html_file = r"E:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\dashboard_BUENO.html"
    
    print("🔍 Extracting JavaScript from dashboard_BUENO.html...")
    js_code, onclicks = extract_javascript_from_html(html_file)
    
    if not js_code:
        print("❌ No JavaScript code found!")
        return
    
    print(f"✅ Extracted {len(js_code)} characters of JavaScript code")
    print(f"✅ Found {len(onclicks)} onclick handlers")
    
    print("\n🔧 Checking bracket balance...")
    is_balanced = check_bracket_balance(js_code)
    
    if is_balanced:
        print("✅ All brackets are balanced!")
    else:
        print("❌ Bracket imbalance detected!")
    
    print("\n🔍 Looking for syntax errors...")
    errors = find_syntax_errors(js_code)
    
    if errors:
        print("❌ Syntax errors found:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ No obvious syntax errors detected!")
    
    # Check specific line 4745 area
    print("\n🎯 Checking area around line 4745...")
    lines = js_code.split('\n')
    if len(lines) >= 4745:
        context_start = max(0, 4740)
        context_end = min(len(lines), 4750)
        print(f"Lines {context_start}-{context_end}:")
        for i in range(context_start, context_end):
            if i < len(lines):
                marker = " --> " if i == 4744 else "     "  # 4744 because array is 0-indexed
                print(f"{marker}{i+1:4d}: {lines[i]}")

if __name__ == "__main__":
    main()
