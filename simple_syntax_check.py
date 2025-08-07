#!/usr/bin/env python3
"""
Simple syntax checker
"""

def check_syntax(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for script blocks
    import re
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    
    total_braces = 0
    total_parens = 0
    
    for i, block in enumerate(script_blocks):
        print(f"Block {i+1}:")
        
        # Count braces and parentheses
        open_braces = block.count('{')
        close_braces = block.count('}')
        open_parens = block.count('(')
        close_parens = block.count(')')
        
        print(f"  Open braces: {open_braces}")
        print(f"  Close braces: {close_braces}")
        print(f"  Open parens: {open_parens}")  
        print(f"  Close parens: {close_parens}")
        
        if open_braces != close_braces:
            print(f"  ERROR: Braces mismatch! {open_braces - close_braces}")
        
        if open_parens != close_parens:
            print(f"  ERROR: Parentheses mismatch! {open_parens - close_parens}")
        
        # Check for unclosed template literals
        backticks = block.count('`')
        if backticks % 2 != 0:
            print(f"  ERROR: Odd number of backticks: {backticks}")
        
        total_braces += (open_braces - close_braces)
        total_parens += (open_parens - close_parens)
        
        print()
    
    print(f"Total brace difference: {total_braces}")
    print(f"Total paren difference: {total_parens}")

if __name__ == "__main__":
    file_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\src\web\templates\conflict_monitoring.html"
    check_syntax(file_path)
