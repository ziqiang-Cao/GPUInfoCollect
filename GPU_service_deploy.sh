#!/bin/bash
# 服务端自动部署脚本

# 配置区域（根据实际情况修改）
PROJECT_DIR="/opt/gpu-monitor-service"  # 项目安装目录

# 创建项目目录
sudo mkdir -p $PROJECT_DIR
sudo cp -r ./GPUInfoService.py ./static/ ./templates/ $PROJECT_DIR

# 安装依赖
echo "[*] 安装Python依赖..."
# 获取 Python 路径
PYTHON_PATH=$(which python3 || which python)

# 检查是否存在
if [ -z "$PYTHON_PATH" ]; then
    echo "错误：Python 未安装！"
    exit 1
fi
$PYTHON_PATH -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r ./requirements.txt

# 创建systemd服务文件
cat << EOF | sudo tee /etc/systemd/system/gpu-monitor.service > /dev/null
[Unit]
Description=GPU Monitor Service
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH $PROJECT_DIR/GPUInfoService.py
Restart=always
RestartSec=30
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=gpu-monitor

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
sudo chmod 644 /etc/systemd/system/gpu-monitor.service

# 重载systemd
echo "[*] 启用服务..."
sudo systemctl daemon-reload
sudo systemctl enable gpu-monitor.service
sudo systemctl restart gpu-monitor.service

echo "[+] 部署完成！使用以下命令查看状态："
echo "sudo systemctl status gpu-monitor"
echo "journalctl -u gpu-monitor -f"
