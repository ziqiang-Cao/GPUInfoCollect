
import time
import re  # 正则模块
import os
from threading import Lock, Thread
from datetime import datetime
import requests

import logging
from logging.handlers import RotatingFileHandler
from markupsafe import Markup, escape
from flask import Flask, jsonify, request, render_template, redirect, url_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加滚动日志
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),  # 绝对路径
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['STATIC_VERSION'] = '1.0.1'  # 每次更新后修改版本号
handler = RotatingFileHandler(
    'monitor.log', maxBytes=10*1024*1024,
    backupCount=5, encoding='utf-8'
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.CRITICAL)

lock = Lock()
clients = {}
TIMEOUT = 60
DELETE_TIMEOUT = 60 * 60 * 24 * 7  # 7 天
# 新增，记录上次收到请求的时间
last_report_time = time.time()
# 新增，记录是否已经发送过通知
notification_sent = False
# 新增，指定超时时间（秒）
CHECK_TIMEOUT = 300  # 5 分钟
# 新增，通知地址
NOTIFICATION_URL = "https://192.168.1.113/api/send/message/"
NOTIFICATION_MESSAGE = "ClientsTimeout"

# 新增，网页浏览计数
visit_count = 0


def cleanup_clients():
    current_time = time.time()
    expired_clientids = [
        clientid for clientid, client in clients.items()
        if current_time - client['timestamp'] > DELETE_TIMEOUT
    ]
    for clientid in expired_clientids:
        del clients[clientid]

# 定时检查函数(所有客户端超时5分钟时发送客户端连接超时微信通知)


def check_timeout():
    global last_report_time, notification_sent
    try:
        while True:

            current_time = time.time()
            if current_time - last_report_time > CHECK_TIMEOUT and not notification_sent:
                try:
                    response = requests.get(
                        NOTIFICATION_URL + NOTIFICATION_MESSAGE)
                    print(response.text)
                    if response.status_code == 200:
                        notification_sent = True
                        app.logger.info("Notification sent successfully.")
                    else:
                        app.logger.error(
                            f"Failed to send notification: {response.text}")
                except Exception as e:
                    app.logger.error(f"Error sending notification: {str(e)}")
            time.sleep(60)  # 每分钟检查一次
    except Exception as e:
        app.logger.error(f"Error in check_timeout thread: {str(e)}")


def parse_gpu_info(gpu_info):
    gpu_list = []
    try:
        blocks = re.split(r'(?=Product Name\s+:)', gpu_info)
        for idx, block in enumerate(blocks):
            # 防御性解析
            product_match = re.search(r"Product Name\s+:\s+(.+)", block)
            used_match = re.search(r"Used\s+:\s+(\d+) MiB", block)
            total_match = re.search(r"Total\s+:\s+(\d+) MiB", block)

            if not (product_match and used_match and total_match):
                continue  # 跳过无效块

            gpu_list.append({
                "index": idx,
                "model": product_match.group(1).strip(),
                "memory": f"{used_match.group(1)}MiB / {total_match.group(1)}MiB"
            })
    except Exception as e:
        app.logger.error(f"GPU parse error: {str(e)}")
    return gpu_list


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
    return jsonify(status="error", message="Internal server error"), 500


@app.route('/report', methods=['POST'])
def handle_report():
    global last_report_time, notification_sent
    try:
        data = request.json
        required_fields = ['ip', 'clientid', 'gpu_info']
        if not all(field in data for field in required_fields):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

        clientid = data.get('clientid')
        if not clientid:
            return jsonify({"error": "IP address is missing"}), 400

        with lock:
            clients[clientid] = {
                'hostname': data.get('hostname', ''),
                'clientid': data.get('clientid', ''),
                'ip': data.get('ip', ''),
                'gpu_info': data.get('gpu_info', ''),
                'timestamp': time.time()
            }
            cleanup_clients()
        app.logger.info(f"Report from {clientid} ({data['hostname']})")
        # 新增，更新上次收到请求的时间
        last_report_time = time.time()
        # 新增，重置通知标记
        notification_sent = False
    except Exception as e:
        app.logger.error(f"Report error: {str(e)}", exc_info=True)
    return jsonify({'status': 'success'})


@app.route('/status')
def status():
    global visit_count
    visit_count += 1

    with lock:
        current_time = time.time()
        cleanup_clients()
        clients_html = []
        for client in clients.values():
            time_diff = current_time - client['timestamp']
            status_class = 'online' if time_diff < TIMEOUT else 'offline'
            # 转义所有用户输入字段
            safe_hostname = escape(client['hostname'])
            safe_clientid = escape(client['clientid'])
            timestamp_str = datetime.fromtimestamp(
                client['timestamp']).strftime('%m-%d %H:%M:%S')
            date_part, time_part = timestamp_str.split(' ')

            # 生成GPU信息时使用安全标记
            gpu_rows = []
            for gpu in parse_gpu_info(client['gpu_info']):
                gpu_rows.append(f'''
                <tr>
                    <td class="gpu-index">GPU {gpu["index"]}</td>
                    <td class="gpu-model">{escape(gpu["model"])}</td>
                    <td class="gpu-memory">{escape(gpu["memory"])}</td>
                </tr>
                ''')

            # 使用Markup标记安全HTML
            clients_html.append(Markup(f'''
            <div class="gpu-box">
                <div class="gpu-header">
                    <table class="info-table">
                        <tr>
                            <td>
                                <span class="status-indicator {status_class}"></span>
                                <strong>{safe_hostname}</strong>
                            </td>
                            <td class="date-timestamp">{date_part}</td>
                        </tr>
                        <tr>
                            <td class="todesk-code">ToDesk设备代码: {safe_clientid}</td>
                            <td class="time-timestamp">{time_part}</td>
                        </tr>
                    </table>
                </div>
                <table class="gpu-table">
                    {Markup(''.join(gpu_rows))}
                </table>
            </div>
            '''))
        return render_template(
            'status.html',
            count=len(clients),
            clients='\n'.join(clients_html),
            last_update=datetime.now(),
            visit_count=visit_count
        )


@app.route('/')
def index():
    # 使用 url_for 反向生成 /status 的 URL，避免硬编码
    return redirect(url_for('status'))


if __name__ == '__main__':
    # 新增，启动定时检查线程
    timeout_thread = Thread(target=check_timeout, daemon=False)
    timeout_thread.start()
    app.run(host='0.0.0.0', port=60001, use_reloader=False,
            threaded=True, debug=False, ssl_context=None)
