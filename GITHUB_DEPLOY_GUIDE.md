# GitHub 上传与 Linux 部署指南

本指南帮助您将投资管理系统上传到 GitHub，并在 Linux 服务器上部署运行。

## 上传到 GitHub

### 1. 创建 GitHub 仓库

1. 登录 GitHub，点击 "+" → "New repository"
2. 填写仓库名称，选择公开或私有
3. 点击 "Create repository"

### 2. 推送本地项目

```bash
cd /path/to/treasure
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/您的用户名/您的仓库名.git
git push -u origin main
```

## 在 Linux 上部署

### 1. 克隆仓库

```bash
git clone https://github.com/您的用户名/您的仓库名.git
cd treasure
```

### 2. 使用启动脚本（推荐）

```bash
chmod +x start_app.sh
./start_app.sh
```

启动脚本提供交互式菜单：启动应用、安装依赖、初始化数据库、创建管理员账户。

### 3. 手动部署

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 初始化数据库并创建管理员
python db_init.py
python create_admin.py

# 启动应用
python run.py
```

## 访问应用

- 本地：http://127.0.0.1:5000
- 局域网/公网：http://服务器IP:5000（需开放防火墙端口）

默认账户：`admin` / `admin123`

> 应用默认绑定 `0.0.0.0:5000`，可通过 `PORT` 环境变量修改端口。

## 更新部署

```bash
# 本地推送更新
git add .
git commit -m "更新说明"
git push origin main

# 服务器拉取更新并重启
cd /path/to/treasure
git pull origin main
# 重启应用（Ctrl+C 后重新运行，或 systemctl restart treasure）
```

## 常见问题

- **依赖安装失败**：尝试 `pip install pandas==1.5.3 numpy==1.24.2`
- **端口被占用**：`lsof -i :5000` 查看并 kill 占用进程，或用 `PORT=8000 python run.py`
- **权限错误**：配置 SSH 密钥或使用 GitHub 个人访问令牌

更多部署细节参考 `LINUX_DEPLOYMENT_GUIDE.md`。
