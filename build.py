#!/usr/bin/env python3
"""
多平台构建脚本
用于本地测试构建过程
"""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"命令执行失败: {cmd}")
            print(f"错误输出: {result.stderr}")
            return False
        print(f"命令执行成功: {cmd}")
        print(f"输出: {result.stdout}")
        return True
    except Exception as e:
        print(f"执行命令时发生错误: {e}")
        return False

def build_linux_x64(version):
    """构建Linux x64版本"""
    print("开始构建Linux x64版本...")
    
    cmd = f'pyinstaller --onefile --name "SocketChatApp-linux-x64-{version}" ' \
          f'--add-data "templates:templates" ' \
          f'--hidden-import=queue ' \
          f'--hidden-import=flask ' \
          f'--hidden-import=webview ' \
          f'main.py'
    
    return run_command(cmd)

def build_linux_arm64(version):
    """构建Linux ARM64版本"""
    print("开始构建Linux ARM64版本...")
    
    # 在GitHub Actions中，我们使用相同的构建命令，但重命名输出文件
    cmd = f'pyinstaller --onefile --name "SocketChatApp-linux-arm64-{version}" ' \
          f'--add-data "templates:templates" ' \
          f'--hidden-import=queue ' \
          f'--hidden-import=flask ' \
          f'--hidden-import=webview ' \
          f'main.py'
    
    return run_command(cmd)

def build_windows_x64(version):
    """构建Windows x64版本"""
    print("开始构建Windows x64版本...")
    
    if platform.system() != "Windows":
        print("警告: 非Windows系统构建Windows版本可能不完整")
    
    cmd = f'pyinstaller --onefile --name "SocketChatApp-windows-x64-{version}.exe" ' \
          f'--add-data "templates;templates" ' \
          f'--hidden-import=queue ' \
          f'--hidden-import=flask ' \
          f'--hidden-import=webview ' \
          f'main.py'
    
    return run_command(cmd)

def install_dependencies():
    """安装构建依赖"""
    print("安装构建依赖...")
    
    dependencies = [
        "pip install -r requirements.txt",
        "pip install pyinstaller"
    ]
    
    for cmd in dependencies:
        if not run_command(cmd):
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='多平台构建脚本')
    parser.add_argument('--version', required=True, help='版本号 (例如: v1.0.0)')
    parser.add_argument('--platform', choices=['linux-x64', 'linux-arm64', 'windows-x64', 'all'], 
                       default='all', help='构建平台')
    
    args = parser.parse_args()
    
    print(f"开始构建版本: {args.version}")
    print(f"目标平台: {args.platform}")
    
    # 安装依赖
    if not install_dependencies():
        print("依赖安装失败")
        return 1
    
    # 根据平台构建
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
        print("构建完成!")
        print("生成的文件在 dist/ 目录中")
    else:
        print("构建过程中出现错误")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())