import subprocess
import socket
import requests
import time
import requests.exceptions
import os
import configparser

DEFAULT_SERVER_URL = "http://127.0.0.1:60001/"
CONFIG_FILE_PATH = "/opt/gpu-monitor-client/gpu_info_client.config"
TODESK_CONFIG_PATH = "/opt/todesk/config/config.ini"


def read_server_url():
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"读取配置文件出错: {str(e)}")
    else:
        try:
            with open(CONFIG_FILE_PATH, 'w') as f:
                f.write(DEFAULT_SERVER_URL)
            print(f"配置文件 {CONFIG_FILE_PATH} 不存在，已创建并写入默认地址。")
        except Exception as e:
            print(f"创建配置文件出错: {str(e)}")
    return DEFAULT_SERVER_URL


SERVER_URL = read_server_url()


def get_gpu_info():
    try:
        output = subprocess.check_output(['nvidia-smi', '-q'], text=True)
        return output
    except Exception as e:
        return f"Error getting GPU info: {str(e)}"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
    
def read_clientid():
    config = configparser.ConfigParser()
    if os.path.exists(TODESK_CONFIG_PATH):
        try:
            config.read(TODESK_CONFIG_PATH)
            if 'configinfo' in config and 'clientid' in config['configinfo']:
                return config['configinfo']['clientid']
        except Exception as e:
            print(f"读取 clientid 出错: {str(e)}")
    return ""


while True:
    try:
        hostname = socket.gethostname()
        clientid = read_clientid()
        ip = get_local_ip()
        gpu_info = get_gpu_info()
        
        data = {
            'hostname': hostname,
            'clientid': clientid,
            'ip': ip,
            'gpu_info': gpu_info
        }
        response = requests.post(SERVER_URL + 'report', json=data, timeout=5)
        if response.status_code != 200:
            print(f"Server error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("无法连接服务器，可能是网络问题或服务器未启动")
        SERVER_URL = read_server_url()
    except requests.exceptions.Timeout:
        print("请求超时，服务器响应过慢")
        SERVER_URL = read_server_url()
    except Exception as e:
        SERVER_URL = read_server_url()
        print(f"未知错误: {str(e)}")
    finally:
        time.sleep(10)  # 无论是否异常都等待10秒
