# GPUInfoCollection
The project comprises client and server components designed for GPU information collection and web-based visualization across multiple Ubuntu hosts.

This is a management tool designed to collect GPU information within local area networks (LANs) (applicable to wide area networks/WANs provided there is a public IP address or implementation of intranet penetration). The development was motivated by the need for GPU resource management in our research group, while remaining adaptable for other usage scenarios as required.
这是一个用于收集局域网（可用于广域网，前提是拥有公网ip或进行内网穿透）GPU信息的管理工具，研发初衷是用于我们课题组GPU信息管理，根据需要也可用于其他场景,欢迎大家使用.

# 部署服务端并部署9个客户端后网页访问效果:
![GPUInfo](https://github.com/user-attachments/assets/b2acc3aa-a70f-402b-bd13-811b3b81daac)


服务端部署(已安装python环境):

chmod +x ./GPU_service_deploy.sh
./GPU_service_deploy.sh


客户端(已安装python环境):

chmod +x ./GPU_client_deploy.sh
./GPU_client_deploy.sh
