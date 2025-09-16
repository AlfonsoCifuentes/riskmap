#!/usr/bin/env python3
"""
Advanced JavaScript syntax validator
"""

def validate_js_detailed(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract script blocks
    import re
    scripts = []
    
    # Find all script blocks
    script_pattern = r'<script[^>]*>(.*?)</script>'
    for match in re.finditer(script_pattern, content, re.DOTALL):
        start_pos = match.start()
        lines_before = content[:start_pos].count('\n')
        script_content = match.group(1)
        scripts.append((lines_before + 1, script_content))
    
    print(f"Found {len(scripts)} script blocks")
    
    for i, (start_line, script_content) in enumerate(scripts):
        print(f"\n=== SCRIPT BLOCK {i+1} (starts at line {start_line}) ===")
        
        # Check for specific syntax issues
        issues = []
        
        # Count brackets and parentheses
        open_braces = script_content.count('{')
        close_braces = script_content.count('}')
        open_parens = script_content.count('(')
        close_parens = script_content.count(')')
        backticks = script_content.count('`')
        
        print(f"Open braces: {open_braces}")
        print(f"Close braces: {close_braces}")
        print(f"Open parens: {open_parens}")
        print(f"Close parens: {close_parens}")
        print(f"Backticks: {backticks}")
        
        if open_braces != close_braces:
            issues.append(f"Brace mismatch: {open_braces} open, {close_braces} close")
        
        if open_parens != close_parens:
            issues.append(f"Parentheses mismatch: {open_parens} open, {close_parens} close")
        
        if backticks % 2 != 0:
            issues.append(f"Odd number of backticks: {backticks}")
        
        # Look for unclosed template literals
        lines = script_content.split('\n')
        in_template = False
        template_depth = 0
        
        for line_num, line in enumerate(lines, start_line):
            for char_pos, char in enumerate(line):
                if char == '`':
                    in_template = not in_template
                    if in_template:
                        template_depth += 1
                    else:
                        template_depth -= 1
            
            # Check if we end a line in a template literal
            if in_template and line_num < start_line + len(lines) - 1:
                print(f"Line {line_num}: Inside template literal")
        
        if template_depth != 0:
            issues.append(f"Template literal depth: {template_depth}")
        
        # Look for specific problem patterns
        if 'document.write(`' in script_content:
            # Find all document.write template literals
            write_pattern = r'document\.write\(`(.*?)`\);'
            matches = list(re.finditer(write_pattern, script_content, re.DOTALL))
            print(f"Found {len(matches)} document.write template literals")
            
            for match in matches:
                template_content = match.group(1)
                # Check for unescaped template literals inside
                if '${' in template_content and template_content.count('${') != template_content.count('}'):
                    issues.append("Possible unmatched ${} in template literal")
        
        if issues:
            print("ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("No syntax issues detected")
    
    return len([issue for script in scripts for issue in script[1]]) == 0

if __name__ == "__main__":
    file_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\conflict_monitoring.html"
    validate_js_detailed(file_path)
