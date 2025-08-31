#!/bin/bash

# 投资管理系统启动脚本
# 此脚本用于在Linux环境中快速启动应用

# 颜色定义
green="\033[0;32m"
red="\033[0;31m"
yellow="\033[0;33m"
reset="\033[0m"

# 检查是否在正确的目录
if [ ! -f "simple_app.py" ] && [ ! -d "app" ]; then
    echo -e "${red}错误：请在项目根目录下运行此脚本！${reset}"
    exit 1
fi

# 显示菜单
show_menu() {
    echo -e "\n${green}===== 投资管理系统启动菜单 =====${reset}\n"
    echo "1. 启动简化版应用（推荐）"
    echo "2. 启动模块化应用"
    echo "3. 安装依赖"
    echo "4. 初始化数据库"
    echo "5. 创建管理员账户"
    echo "6. 退出"
    echo -e "\n请选择操作 [1-6]:"
}

# 安装依赖
install_dependencies() {
    echo -e "${green}\n正在安装项目依赖...${reset}"
    
    # 检查是否有虚拟环境
    if [ ! -d ".venv" ]; then
        echo -e "${yellow}未检测到虚拟环境，正在创建...${reset}"
        python3 -m venv .venv
    fi
    
    # 激活虚拟环境
source .venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装基础依赖
    pip install flask sqlalchemy flask-login pandas numpy
    
    # 尝试安装akshare，如果失败则使用兼容版本
    echo -e "${yellow}\n尝试安装akshare...${reset}"
    if ! pip install akshare; then
        echo -e "${yellow}akshare 安装失败，尝试使用兼容版本...${reset}"
        pip install akshare==1.7.52 pandas==1.5.3 numpy==1.24.2
    fi
    
    echo -e "${green}\n依赖安装完成！${reset}"
}

# 初始化数据库
init_database() {
    echo -e "${green}\n正在初始化数据库...${reset}"
    
    # 激活虚拟环境
source .venv/bin/activate
    
    # 运行数据库初始化脚本
    if [ -f "db_init.py" ]; then
        python db_init.py
    else
        echo -e "${yellow}未找到 db_init.py，尝试使用 generate_mock_data.py...${reset}"
        if [ -f "generate_mock_data.py" ]; then
            python generate_mock_data.py
        else
            echo -e "${red}错误：未找到数据库初始化脚本！${reset}"
        fi
    fi
    
    echo -e "${green}\n数据库初始化完成！${reset}"
}

# 创建管理员账户
create_admin() {
    echo -e "${green}\n正在创建管理员账户...${reset}"
    
    # 激活虚拟环境
source .venv/bin/activate
    
    # 运行创建管理员脚本
    if [ -f "create_admin.py" ]; then
        python create_admin.py
    else
        echo -e "${red}错误：未找到 create_admin.py 脚本！${reset}"
    fi
    
    echo -e "${green}\n管理员账户创建完成！${reset}"
}

# 启动正式版应用（使用simple_app.py）
start_simple_app() {
    echo -e "${green}\n正在启动投资管理系统...${reset}"
    
    # 检查是否有虚拟环境
    if [ ! -d ".venv" ]; then
        echo -e "${yellow}未检测到虚拟环境，正在创建...${reset}"
        python3 -m venv .venv
    fi
    
    # 激活虚拟环境
source .venv/bin/activate
    
    # 检查是否安装了基础依赖
    if ! python -c "import flask" >/dev/null 2>&1; then
        echo -e "${yellow}未检测到必要依赖，正在安装...${reset}"
        pip install flask sqlalchemy flask-login pandas numpy
    fi
    
    # 启动应用
    echo -e "${green}\n应用已配置为绑定到所有网卡地址（0.0.0.0:5000）"
    echo -e "您可以通过以下方式访问："
    echo -e "- 本地访问：http://127.0.0.1:5000"
    echo -e "- 局域网访问：http://服务器局域网IP:5000"
    echo -e "- 公网访问：http://服务器公网IP:5000（需确保防火墙已开放5000端口）"
    echo -e "\n默认账户："
    echo -e "- 管理员账户：username=admin, password=admin123"
    echo -e "- 次级账户：username=user1/user2/user3, password=user123"
    echo -e "按 Ctrl+C 停止应用${reset}\n"
    
    python simple_app.py
}

# 启动模块化应用（已废弃，使用simple_app.py代替）
start_modular_app() {
    echo -e "${yellow}\n模块化应用已废弃，请使用simple_app.py作为正式版本。${reset}\n"
    start_simple_app
}

# 主程序
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

while true; do
    show_menu
    read -p "选择: " choice
    
    case $choice in
        1)
            start_simple_app
            ;;
        2)
            start_modular_app
            ;;
        3)
            install_dependencies
            ;;
        4)
            init_database
            ;;
        5)
            create_admin
            ;;
        6)
            echo -e "${green}\n感谢使用投资管理系统，再见！${reset}\n"
            exit 0
            ;;
        *)
            echo -e "${red}\n无效的选择，请重试！${reset}"
            ;;
    esac
    
    echo -e "${yellow}\n按 Enter 键继续...${reset}"
    read

done