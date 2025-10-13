# 多平台构建说明

## GitHub Actions 自动构建

### 使用方法

1. 在GitHub仓库中，进入 **Actions** 标签页
2. 选择 **Multi-Platform Build** 工作流
3. 点击 **Run workflow** 按钮
4. 填写版本号 (例如: v1.0.0)
5. 选择要构建的平台
6. 点击 **Run workflow** 开始构建

### 构建平台

- **Linux x64**: 适用于大多数Linux发行版
- **Linux ARM64**: 适用于树莓派等ARM设备
- **Windows x64**: 适用于64位Windows系统
- **Android APK**: Android应用程序包

### 输出文件

构建完成后，可以在以下位置找到生成的文件：

1. **Artifacts**: 在Actions运行结果页面下载
2. **Releases**: 自动创建GitHub Release并上传所有文件

## 本地构建

### 前置要求

```bash
# 安装Python依赖
pip install -r requirements.txt
pip install pyinstaller

# 对于Android构建
pip install buildozer
```

### 使用构建脚本

```bash
# 构建所有平台
python build.py --version v1.0.0 --platform all

# 仅构建Linux版本
python build.py --version v1.0.0 --platform linux-x64

# 仅构建Windows版本
python build.py --version v1.0.0 --platform windows-x64
```

### 手动构建命令

#### Linux构建
```bash
pyinstaller --onefile --name "SocketChatApp-linux-x64-v1.0.0" \
  --add-data "templates:templates" \
  --hidden-import=queue \
  --hidden-import=flask \
  --hidden-import=webview \
  main.py
```

#### Windows构建
```bash
pyinstaller --onefile --name "SocketChatApp-windows-x64-v1.0.0.exe" \
  --add-data "templates;templates" \
  --hidden-import=queue \
  --hidden-import=flask \
  --hidden-import=webview \
  main.py
```

#### Android构建
```bash
buildozer android debug
```

## 文件说明

- `.github/workflows/build.yml`: GitHub Actions工作流配置
- `buildozer.spec`: Android构建配置
- `build.py`: 本地构建脚本
- `requirements.txt`: Python依赖列表

## 注意事项

1. **Android构建**: 需要较长时间，建议在GitHub Actions上运行
2. **跨平台构建**: Windows版本在Linux上构建可能不完整
3. **依赖管理**: 确保所有依赖都在requirements.txt中列出
4. **版本控制**: 每次构建使用不同的版本号便于管理