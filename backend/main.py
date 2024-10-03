from fastapi import FastAPI
from typing import Dict, List, Tuple
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import asyncio
from datetime import datetime, timedelta
from monitor import *
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager


class GPUInfo(BaseModel):
    index: int
    usage: float
    memory_usage: float


class CPUInvalidUsage(BaseModel):
    user: str
    command: str
    usage: float


class GPUInvalidUsage(BaseModel):
    user: str
    error: int
    index: int
    command: str
    sm: int
    mem: int
    mem_usage: int
    total_mem: int


class ServerStatus(BaseModel):
    name: str
    cpu_usage: float
    cpu_memory_usage: float
    gpus: List[GPUInfo]
    cpu_invalid_usage: List[CPUInvalidUsage]
    gpu_invalid_usage: List[GPUInvalidUsage]


origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://server.eviloder.win",
]

STATUS_CACHE = []
CPU_HISTORY_CACHE = []
GPU_HISTORY_CACHE = []
STATUS_FILE = os.path.join(os.getcwd(), "data/status.csv")
CPU_FILE = os.path.join(os.getcwd(), "data/cpu_history.csv")
GPU_FILE = os.path.join(os.getcwd(), "data/gpu_history.csv")
INTERVAL = 20 if not DEBUG else 1  # minutes


def get_detailed_status() -> List[ServerStatus]:
    server_status = []
    for host in hosts:
        try:
            ssh, vlab_client = get_ssh_client(host)
            cpu_usage, cpu_memory_usage = get_cpu_usage(ssh)
            gpu_usage, gpu_memory_usage = get_gpu_usage(ssh)
            invalid_cpu = check_cpu_usage(ssh)
            invalid_gpu = check_gpu_usage(ssh)

            gpus = [
                GPUInfo(index=i, usage=gpu_usage[i], memory_usage=gpu_memory_usage[i])
                for i in range(len(gpu_usage))
            ]

            cpu_invalid_usage = [
                CPUInvalidUsage(user=user, command=cmd, usage=usage)
                for user, cmds in invalid_cpu.items()
                for cmd, usage in cmds
            ]
            gpu_invalid_usage = [
                GPUInvalidUsage(
                    user=user,
                    error=error,
                    index=idx,
                    command=cmd,
                    sm=sm,
                    mem=mem,
                    mem_usage=mem_usage,
                    total_mem=total_mem,
                )
                for user, cmds in invalid_gpu.items()
                for error, idx, cmd, sm, mem, mem_usage, total_mem in cmds
            ]
            server_status.append(
                ServerStatus(
                    name=host["name"],
                    cpu_usage=cpu_usage,
                    cpu_memory_usage=cpu_memory_usage,
                    gpus=gpus,
                    cpu_invalid_usage=cpu_invalid_usage,
                    gpu_invalid_usage=gpu_invalid_usage,
                )
            )
            if vlab_client:
                vlab_client.close()
            if ssh:
                ssh.close()
        except Exception as e:
            print(f"连接主机 {host['name']} 时发生错误: {str(e)}")
    return server_status


def save_to_csv(data: List[ServerStatus]) -> None:
    now = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame(
        [
            {
                "timestamp": now,
                "name": server.name,
                "cpu_usage": server.cpu_usage,
                "cpu_memory_usage": server.cpu_memory_usage,
                "gpus": str(server.gpus),
            }
            for server in data
        ]
    )
    header = os.path.getsize(STATUS_FILE) == 0
    df.to_csv(STATUS_FILE, mode="a", header=header, index=False)
    # CPU
    if len([c for s in data for c in s.cpu_invalid_usage]) > 0:
        df = pd.DataFrame(
            [
                {
                    "timestamp": now,
                    "name": server.name,
                    "user": invalid_cpu.user,
                    "command": invalid_cpu.command,
                    "usage": invalid_cpu.usage,
                }
                for server in data
                for invalid_cpu in server.cpu_invalid_usage
            ]
        )
        header = os.path.getsize(CPU_FILE) == 0
        df.to_csv(CPU_FILE, mode="a", header=header, index=False)
    # GPU
    if len([g for s in data for g in s.gpu_invalid_usage]) > 0:
        df = pd.DataFrame(
            [
                {
                    "timestamp": now,
                    "name": server.name,
                    "user": invalid_gpu.user,
                    "error": invalid_gpu.error,
                    "index": invalid_gpu.index,
                    "command": invalid_gpu.command,
                    "sm": invalid_gpu.sm,
                    "mem": invalid_gpu.mem,
                    "mem_usage": invalid_gpu.mem_usage,
                    "total_mem": invalid_gpu.total_mem,
                }
                for server in data
                for invalid_gpu in server.gpu_invalid_usage
            ]
        )
        header = os.path.getsize(GPU_FILE) == 0
        df.to_csv(GPU_FILE, mode="a", header=header, index=False)


def trim_history(file: str) -> List[Dict]:
    if os.path.getsize(file) == 0:
        return []
    one_week_ago = datetime.now() - timedelta(days=7)
    df = pd.read_csv(file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[df["timestamp"] > one_week_ago]
    df.to_csv(file, index=False)
    return df.to_dict("records")


async def update_all_caches() -> None:
    global STATUS_CACHE, CPU_HISTORY_CACHE, GPU_HISTORY_CACHE
    STATUS_CACHE = get_detailed_status()
    save_to_csv(STATUS_CACHE)
    CPU_HISTORY_CACHE = trim_history(CPU_FILE)
    GPU_HISTORY_CACHE = trim_history(GPU_FILE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_all_caches, "interval", minutes=INTERVAL)
    scheduler.start()
    await update_all_caches()  # update caches immediately when server starts
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status", response_model=List[ServerStatus])
async def get_server_status() -> List[ServerStatus]:
    return STATUS_CACHE


@app.get("/api/cpu_history", response_model=List[Dict])
async def get_cpu_history() -> List[Dict]:
    return CPU_HISTORY_CACHE


@app.get("/api/gpu_history", response_model=List[Dict])
async def get_gpu_history() -> List[Dict]:
    return GPU_HISTORY_CACHE


async def test():
    server_status = await get_server_status()
    print(server_status)
    save_to_csv(server_status)


if __name__ == "__main__":
    asyncio.run(test())
