#!/bin/bash
# 客户端自动部署脚本

# 配置区域（根据实际情况修改）
PROJECT_DIR="/opt/gpu-monitor-client"  # 项目安装目录
SERVER="http://192.168.0.100:60001/"

# 创建项目目录
sudo mkdir -p $PROJECT_DIR
sudo cp ./GPUInfoClient.py $PROJECT_DIR

echo "[*] 生成配置文件..."
echo $SERVER | sudo tee $PROJECT_DIR/gpu_info_client.config > /dev/null

# 安装依赖
echo "[*] 安装Python依赖..."
# 获取 Python 路径
PYTHON_PATH=$(which python3 || which python)

# 检查是否存在
if [ -z "$PYTHON_PATH" ]; then
    echo "未找到 Python，正在安装 Python3..."
    sudo apt update && sudo apt install -y python3
    if [ $? -ne 0 ]; then
        echo "错误：Python 安装失败！"
        exit 1
    fi
    # 重新获取 Python3 路径
    PYTHON_PATH=$(which python3)
    exit 1
fi
$PYTHON_PATH -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r ./requirements.txt

# 创建systemd服务文件
cat << EOF | sudo tee /etc/systemd/system/gpu-monitor-client.service > /dev/null
[Unit]
Description=GPU Monitor Client
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH $PROJECT_DIR/GPUInfoClient.py
Restart=always
RestartSec=60
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=gpu-monitor-client

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
sudo chmod 644 /etc/systemd/system/gpu-monitor-client.service

# 重载systemd
echo "[*] 启用服务..."
sudo systemctl daemon-reload
sudo systemctl enable gpu-monitor-client.service
sudo systemctl restart gpu-monitor-client.service

echo "[+] 部署完成！使用以下命令查看状态："
echo "sudo systemctl status gpu-monitor-client"
echo "journalctl -u gpu-monitor-client -f"
