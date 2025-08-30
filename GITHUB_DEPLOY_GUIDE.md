# GitHub 上传与 Linux 下载使用指南

本指南将帮助您将投资管理系统上传到 GitHub，然后下载到 Linux 环境中使用。

## 第一步：将项目上传到 GitHub

### 1. 在 GitHub 上创建新仓库

1. 登录您的 GitHub 账户
2. 点击右上角的 "+", 选择 "New repository"
3. 填写仓库名称（例如：treasure-investment-system）
4. 选择公开或私有仓库
5. 点击 "Create repository"

### 2. 在本地项目中初始化 Git

在项目根目录（e:/桌面/treasure）中打开命令行工具（Windows PowerShell 或 CMD）：

```powershell
# 初始化 Git 仓库
cd e:/桌面/treasure
git init

# 添加所有文件到暂存区
git add .

# 提交更改
git commit -m "Initial commit"

# 关联到 GitHub 仓库
git remote add origin https://github.com/您的用户名/您的仓库名.git

# 推送到 GitHub
git push -u origin main
```

> 注意：如果出现推送权限问题，可能需要配置 SSH 密钥或使用个人访问令牌。

## 第二步：在 Linux 上下载项目

### 1. 在 Linux 上安装 Git

```bash
# Ubuntu/Debian
apt update && apt install -y git

# CentOS/RHEL
yum install -y git
```

### 2. 克隆 GitHub 仓库

```bash
# 克隆仓库到 Linux 服务器
git clone https://github.com/您的用户名/您的仓库名.git

# 进入项目目录
cd 您的仓库名
```

## 第三步：在 Linux 上配置和使用项目

### 1. 使用启动脚本快速开始

我们提供了便捷的启动脚本，可以帮助您一键配置和启动应用：

```bash
# 为脚本添加执行权限
chmod +x start_app.sh

# 运行启动脚本
./start_app.sh
```

启动脚本会显示交互式菜单，您可以根据需要选择以下功能：
- 启动简化版应用（推荐）
- 启动模块化应用
- 安装依赖
- 初始化数据库
- 创建管理员账户

> **注意：** 应用已配置为绑定到所有网卡地址（0.0.0.0:5000），支持公网访问。如需从公网访问，请确保服务器防火墙已开放5000端口（详细配置请参考LINUX_DEPLOYMENT_GUIDE.md文件中的防火墙配置部分）。

### 2. 手动配置步骤（备选方案）

如果您不使用启动脚本，也可以手动执行以下步骤：

#### 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv

source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

#### 初始化数据库

```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 初始化数据库
python db_init.py

# 创建管理员账户
python create_admin.py
```

#### 启动应用

```bash
# 启动简化版应用（推荐）
source .venv/bin/activate
python simple_app.py

# 或启动模块化应用
source .venv/bin/activate
python -m app.run
```

## 第四步：访问应用

应用启动后，可以通过以下方式访问：
- 如果在本地 Linux 环境：http://127.0.0.1:5000
- 如果在远程服务器：http://服务器IP:5000（需确保防火墙已开放5000端口）

默认账户信息：
- 管理员账户：username=admin, password=admin123
- 次级账户：username=user1/user2/user3, password=user123

## 第五步：更新项目

### 从本地Windows上传更新到GitHub

当您在Windows上对项目进行了修改（如我们刚才的配置更新）后，可以按照以下步骤将更改上传到GitHub：

1. **在Windows本地提交更改**：
   
   打开Windows的命令提示符或PowerShell，进入项目目录：
   
   ```bash
   cd e:\桌面\treasure
   
   # 检查更改的文件
   git status
   
   # 添加所有更改的文件
   git add .
   
   # 提交更改
   git commit -m "更新系统配置以支持公网访问"
   
   # 推送到GitHub
   git push origin main
   ```
   
   > 注意：如果您使用的是不同的分支名称（如master），请将`main`替换为您的分支名称。

### 在Linux服务器上获取更新

当您已将更改推送到GitHub后，可以在Linux服务器上执行以下命令获取最新更新：

1. **进入项目目录**：
   ```bash
   cd /path/to/your/repository
   ```

2. **拉取最新代码**：
   ```bash
   git pull origin main
   ```

3. **重启应用以应用更新**：
   
   如果您使用启动脚本：
   ```bash
   # 先停止正在运行的应用（如果需要）
   # 按Ctrl+C停止或使用其他方式
   
   # 重新运行启动脚本
   ./start_app.sh
   ```

   如果您使用Systemd服务管理应用：
   ```bash
   sudo systemctl restart treasure.service
   ```

## 常见问题解决

### 1. 克隆仓库时权限错误

**解决方法**：
- 使用 HTTPS + 个人访问令牌
- 配置 SSH 密钥（推荐）

### 2. 依赖安装失败

**解决方法**：
- 参考 requirements.txt 中的注释，尝试安装兼容版本
- 执行 `pip install numpy==1.24.2 pandas==1.5.3`

### 3. 端口被占用

**解决方法**：
- 查找占用端口的进程：`lsof -i :5000`
- 杀死占用进程：`kill -9 <PID>`
- 或修改代码使用其他端口

## 更多详细信息

- 查看 <mcfile name="LINUX_DEPLOYMENT_GUIDE.md" path="e:/桌面/treasure/LINUX_DEPLOYMENT_GUIDE.md"></mcfile> 获取更详细的 Linux 部署说明
- 查看 <mcfile name="start_app.sh" path="e:/桌面/treasure/start_app.sh"></mcfile> 了解启动脚本的具体功能

祝您使用愉快！