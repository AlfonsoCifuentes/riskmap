#!/usr/bin/env python3
import subprocess
import sys

def main():
    print("Formateando código...")
    subprocess.run(['black', '.'], check=True)
    subprocess.run(['ruff', 'format', '.'], check=True)
    print("Código formateado exitosamente")

if __name__ == '__main__':
    main()