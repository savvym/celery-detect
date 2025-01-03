import logging
import os
import platform
import resource
import time
from typing import Self

from celery.events.state import State
from pydantic import BaseModel, Field

from tasks.models import Task
from workers.models import CPULoad, Worker

logger = logging.getLogger(__name__)
start_time = time.time()


class ServerInfo(BaseModel):
    cpu_usage: CPULoad = Field(description="CPU load average in last 1, 5 and 15 minutes")
    memory_usage: float = Field(description="Memory Usage in KB")
    uptime: float = Field(description="Server Uptime in seconds")
    server_hostname: str = Field(description="Server Hostname")
    server_port: int = Field(description="Server Port")
    server_version: str = Field(description="Server Version")
    server_os: str = Field(description="Server OS")
    server_name: str = Field(description="Server Device Name")
    python_version: str = Field(description="Python Version")
    task_count: int = Field(description="Number of tasks stored in state")
    tasks_max_count: int = Field(description="Maximum number of tasks to store in state")
    worker_count: int = Field(description="Number of workers running")
    worker_max_count: int = Field(description="Maximum number of workers to store in state")

    @classmethod
    def create(cls, scope, state: State) -> Self:
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        client = scope.get('client', ('', 0))
        return ServerInfo(
            cpu_usage=os.getloadavg(),
            memory_usage=rusage.ru_maxrss,
            uptime=time.time() - start_time,
            server_hostname=client[0],
            server_port=client[1],
            server_os=platform.system(),
            server_name=platform.node(),
            python_version=platform.python_version(),
            task_count=len(state.tasks),
            tasks_max_count=state.max_tasks_in_memory,
            worker_count=len(state.workers),
            worker_max_count=state.max_workers_in_memory,
        )


class ClientDebugInfo(BaseModel):
    settings: dict
    screen_width: int
    screen_height: int


class StateDump(BaseModel):
    tasks: list[Task]
    workers: list[Worker]
