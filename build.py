#!/usr/bin/env python3
"""
Multi-platform build script
For local testing of build process
"""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error output: {result.stderr}")
            return False
        print(f"Command successful: {cmd}")
        print(f"Output: {result.stdout}")
        return True
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def build_linux_x64(version):
    """Build Linux x64 version"""
    print("Building Linux x64 version...")
    
    cmd = f'pyinstaller --onefile --name "SocketChatApp-linux-x64-{version}" ' \
          f'--add-data "templates:templates" ' \
          f'--hidden-import=queue ' \
          f'--hidden-import=flask ' \
          f'--hidden-import=webview ' \
          f'main.py'
    
    return run_command(cmd)

def build_linux_arm64(version):
    """Build Linux ARM64 version"""
    print("Building Linux ARM64 version...")
    
    # In GitHub Actions, we use the same build command but rename the output file
    cmd = f'pyinstaller --onefile --name "SocketChatApp-linux-arm64-{version}" ' \
          f'--add-data "templates:templates" ' \
          f'--hidden-import=queue ' \
          f'--hidden-import=flask ' \
          f'--hidden-import=webview ' \
          f'main.py'
    
    return run_command(cmd)

def build_windows_x64(version):
    """Build Windows x64 version"""
    print("Building Windows x64 version...")
    
    if platform.system() != "Windows":
        print("Warning: Building Windows version on non-Windows system may be incomplete")
    
    cmd = f'pyinstaller --onefile --name "SocketChatApp-windows-x64-{version}.exe" ' \
          f'--add-data "templates;templates" ' \
          f'--hidden-import=queue ' \
          f'--hidden-import=flask ' \
          f'--hidden-import=webview ' \
          f'main.py'
    
    return run_command(cmd)

def install_dependencies():
    """Install build dependencies"""
    print("Installing build dependencies...")
    
    dependencies = [
        "pip install -r requirements.txt",
        "pip install pyinstaller"
    ]
    
    for cmd in dependencies:
        if not run_command(cmd):
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Multi-platform build script')
    parser.add_argument('--version', required=True, help='Version number (e.g., v1.0.0)')
    parser.add_argument('--platform', choices=['linux-x64', 'linux-arm64', 'windows-x64', 'all'], 
                       default='all', help='Build platform')
    
    args = parser.parse_args()
    
    print(f"Starting build for version: {args.version}")
    print(f"Target platform: {args.platform}")
    
    # Install dependencies
    if not install_dependencies():
        print("Dependency installation failed")
        return 1
    
    # Build based on platform
    success = True
    
    if args.platform in ['linux-x64', 'all']:
        if not build_linux_x64(args.version):
            success = False
    
    if args.platform in ['linux-arm64', 'all']:
        if not build_linux_arm64(args.version):
            success = False
    
    if args.platform in ['windows-x64', 'all']:
        if not build_windows_x64(args.version):
            success = False
    
    if success:
        print("Build completed!")
        print("Generated files are in dist/ directory")
    else:
        print("Errors occurred during build process")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())