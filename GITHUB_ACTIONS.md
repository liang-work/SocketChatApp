# GitHub Actions 多平台构建指南

## 概述

本项目使用GitHub Actions实现自动化多平台构建，支持以下平台：
- Linux x64 可执行文件
- Linux ARM64 可执行文件  
- Windows x64 可执行文件
- Android APK

## 使用方法

### 1. 手动触发构建

1. 进入GitHub仓库的"Actions"标签页
2. 选择"Multi-Platform Build"工作流
3. 点击"Run workflow"按钮
4. 填写构建参数：
   - **platforms**: 选择要构建的平台（支持多选）
   - **version**: 输入版本号（例如：v1.0.0）
   - **create_release**: 是否创建GitHub Release

### 2. 构建参数说明

#### platforms 选项
- `linux-x64`: 仅构建Linux x64版本
- `linux-arm64`: 仅构建Linux ARM64版本  
- `windows-x64`: 仅构建Windows x64版本
- `android`: 仅构建Android APK
- `all`: 构建所有平台

#### version 格式
- 使用语义化版本号，例如：v1.0.0, v1.2.3-beta
- 建议遵循语义化版本规范

### 3. 构建产物

构建完成后，可以在以下位置找到构建产物：

1. **Artifacts**: 在GitHub Actions运行页面下载
   - `socketchatapp-linux-x64-{version}`
   - `socketchatapp-linux-arm64-{version}`  
   - `socketchatapp-windows-x64-{version}`
   - `socketchatapp-android-{version}`

2. **GitHub Release** (如果启用):
   - 自动创建版本标签
   - 包含所有平台的构建文件

### 4. 本地测试构建

在推送代码前，可以使用本地构建脚本测试：

```bash
# 构建所有平台
python build.py --version v1.0.0 --platform all

# 仅构建特定平台
python build.py --version v1.0.0 --platform linux-x64
python build.py --version v1.0.0 --platform windows-x64
```

### 5. 依赖要求

构建过程需要以下依赖：
- Python 3.11
- PyInstaller (用于桌面应用构建)
- Buildozer (用于Android APK构建)
- Android SDK (用于Android构建)

这些依赖已在GitHub Actions工作流中自动配置。

## 故障排除

### 常见问题

1. **构建失败**: 检查requirements.txt中的依赖是否兼容
2. **Android构建失败**: 确保buildozer.spec配置正确
3. **文件权限问题**: 确保构建脚本有执行权限

### 日志查看

构建过程中的详细日志可以在GitHub Actions运行页面查看，每个步骤都有对应的日志输出。