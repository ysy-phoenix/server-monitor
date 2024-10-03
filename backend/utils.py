import os
user = os.getenv('USER') or os.getenv('USERNAME')
DEBUG = False if user == "azureuser" else True
hosts = [
    {"name": "4090-s1", "port": 1721},
    {"name": "4090-s2", "port": 1722},
    {"name": "4090-s3", "port": 1723},
    {"name": "TNT", "port": 1745},
]
username = "fake"
hostname = "fake"
key_file = "fake" if DEBUG else "/home/azureuser/.ssh/id_ed25519"

PYTHON = "/data/ShengyuYe/miniconda3/bin/python"
GET_CPU_USAGE_SCRTPTS = '''
import psutil
cpu_usage = psutil.cpu_percent(interval=1)
memory_info = psutil.virtual_memory()
cpu_memory_usage = memory_info.percent
print(cpu_usage, cpu_memory_usage)
'''