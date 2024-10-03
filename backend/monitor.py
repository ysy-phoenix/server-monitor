import paramiko
import json
import time
import re
from typing import Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from utils import *


def create_ssh_client(server: str, port: int, user: str, key_file: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port=port, username=user, key_filename=key_file)
    return client


def get_ssh_client(host: dict) -> Tuple[paramiko.SSHClient, Optional[paramiko.SSHClient]]:
    try:
        if DEBUG:
            ssh = create_ssh_client(hostname, host["port"], username, key_file)
            return ssh, None
        else:
            vlab_host = "vlab.ustc.edu.cn"
            vlab_port = 22
            vlab_user = "ubuntu"
            vlab_key_file = "/home/azureuser/.ssh/vlab-vm9395.pem"
            vlab_client = create_ssh_client(
                vlab_host, vlab_port, vlab_user, vlab_key_file
            )

            transport = vlab_client.get_transport().open_channel(
                "direct-tcpip", (hostname, host["port"]), (vlab_host, vlab_port)
            )

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname,
                port=host["port"],
                username=username,
                key_filename=key_file,
                sock=transport,
            )
            return ssh, vlab_client
    except paramiko.AuthenticationException:
        print(f"SSH 认证失败: {host['name']}")
    except paramiko.SSHException as ssh_exception:
        print(f"SSH 连接错误: {host['name']} - {str(ssh_exception)}")
    except Exception as e:
        print(f"连接到 {host['name']} 时发生未知错误: {str(e)}")


def ssh_execute_command(ssh: paramiko.SSHClient, command: str) -> str:
    try:
        _, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            return stdout.read().decode()
        else:
            error_message = stderr.read().decode()
            print(f"Command failed: {error_message}")
            return None
    except Exception as e:
        print(f"Error in execute_command_on_host:\n{e}")
        return None


def get_cpu_usage(ssh: paramiko.SSHClient):
    command = f"{PYTHON} -c '{GET_CPU_USAGE_SCRTPTS}'"
    result = ssh_execute_command(ssh, command)
    cpu_usage, cpu_memory_usage = result.split(" ")
    return float(cpu_usage), float(cpu_memory_usage)


def check_cpu_usage(ssh: paramiko.SSHClient):
    command = f"ps aux --sort=-%cpu | awk '$3 > 10.0'"
    result = ssh_execute_command(ssh, command)
    upperbound = int(ssh_execute_command(ssh, "nproc")) // 4 * 100
    user_cpus = defaultdict(list)
    invalid_user_cpus = defaultdict(list)
    for line in result.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 11:
            user, cpu_percent, command = (
                fields[0],
                float(fields[2]),
                " ".join(fields[10:]),
            )
            user_cpus[user].append((command, cpu_percent))
    for user, cpus in user_cpus.items():
        if sum([cpu for _, cpu in cpus]) > upperbound:
            invalid_user_cpus[user] = cpus
    return invalid_user_cpus


def get_gpu_usage(ssh: paramiko.SSHClient):
    command = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
    result = ssh_execute_command(ssh, command)
    gpu_usage = [float(line.split(",")[0]) for line in result.splitlines()]
    gpu_memory_usage = [
        float(line.split(",")[1]) / float(line.split(",")[2]) * 100
        for line in result.splitlines()
    ]
    return gpu_usage, gpu_memory_usage


def check_gpu_usage(ssh: paramiko.SSHClient):
    command = "nvidia-smi pmon -s u -c 1 -d 10"
    gpu_processes = ssh_execute_command(ssh, command).splitlines()[2:]
    command_mem = (
        "nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits"
    )
    used_mem = ssh_execute_command(ssh, command_mem)
    mem_dict = {
        int(line.split(",")[0]): int(line.split(",")[1])
        for line in used_mem.splitlines()
    }
    command = "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits"
    total_mem = int(ssh_execute_command(ssh, command).split("\n")[0])
    invalid_user_gpus = defaultdict(list)
    user_gpus = defaultdict(list)
    for line in gpu_processes:
        parts = re.split(r"\s+", line.strip())
        if line.strip().count("-") < 3:
            idx, pid, sm, mem = (
                int(parts[0]),
                int(parts[1]),
                int(parts[3]),
                int(parts[4]),
            )
            mem_usage = mem_dict.get(pid, 0)
            user = ssh_execute_command(ssh, f"ps -o uname= -p {pid}").strip()
            command = ssh_execute_command(ssh, f"ps -o cmd= -p {pid}").strip()
            user_gpus[user].append((idx, command, sm, mem, mem_usage, total_mem))
    for user, processes in user_gpus.items():
        count = len(set([p[0] for p in processes]))
        if count > 2:
            invalid_user_gpus[user] = [(0, *p) for p in processes]
            continue
        invalid_processes = []
        for process in processes:
            idx, cmd, sm, mem, mem_usage, total_mem = process
            if mem_usage / total_mem > 0.5 and sm < 10:
                invalid_processes.append(process)
        if invalid_processes:
            invalid_user_gpus[user] = [(1, *p) for p in invalid_processes]
    return invalid_user_gpus


def test():
    for host in hosts:
        ssh, vlab_client = get_ssh_client(host)
        if ssh:
            print(f"{'=' * 20} {host['name']} {'=' * 20}")
            try:
                cpu_usage, cpu_memory_usage = get_cpu_usage(ssh)
                print(f"CPU Usage: {cpu_usage}%")
                print(f"CPU Memory Usage: {cpu_memory_usage}%")
                invalid_user_cpus = check_cpu_usage(ssh)
                for user, cpus in invalid_user_cpus.items():
                    print(f"User {user} has {len(cpus)} invalid CPUs:")
                    for cmd, cpu in cpus:
                        print(f"\t- Command: {cmd}, CPU: {cpu}%")
                gpu_usage, gpu_memory_usage = get_gpu_usage(ssh)
                print(f"GPU Usage: {gpu_usage}")
                print(f"GPU Memory Usage: {gpu_memory_usage}")
                invalid_user_gpus = check_gpu_usage(ssh)
                for user, gpus in invalid_user_gpus.items():
                    print(f"User {user} has {len(gpus)} invalid GPUs")
                    for error, idx, cmd, sm, mem, mem_usage, total_mem in gpus:
                        print(
                            f"\t- Error: {error}, Index: {idx}, Command: {cmd}, SM: {sm}, Mem: {mem}, Mem Usage: {mem_usage}, Total Mem: {total_mem}"
                        )
            except Exception as e:
                print(f"处理主机 {host['name']} 时发生错误: {str(e)}")
            finally:
                if vlab_client:
                    vlab_client.close()
                if ssh:
                    ssh.close()
        else:
            print(f"无法连接到 {host['name']}")


if __name__ == "__main__":
    test()
