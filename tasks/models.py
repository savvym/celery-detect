# Create your models here.
from enum import Enum
from typing import Any, Self

from celery import states
from celery.events.state import Task as CeleryTask
from pydantic import BaseModel, Field, field_validator

from common.types import EpochTimestamp


class TaskState(str, Enum):
    PENDING = states.PENDING
    RECEIVED = states.RECEIVED
    STARTED = states.STARTED
    SUCCESS = states.SUCCESS
    FAILURE = states.FAILURE
    REVOKED = states.REVOKED
    REJECTED = states.REJECTED
    RETRY = states.RETRY
    IGNORED = states.IGNORED


class Task(BaseModel):
    id: str = Field(description="Task UUID")
    type: str | None = Field(None, description="Task function name")
    state: TaskState = Field(description="Task last known state")

    sent_at: EpochTimestamp = Field(description="When task was published by client to queue")
    received_at: EpochTimestamp | None = Field(None, description="When task was received by worker")
    started_at: EpochTimestamp | None = Field(None, description="When task was started to be executed by worker")
    succeeded_at: EpochTimestamp | None = Field(None, description="When task was finished successfully by worker")
    failed_at: EpochTimestamp | None = Field(None, description="When task was finished with failure by worker")
    retried_at: EpochTimestamp | None = Field(None, description="When task was last published for retry")
    revoked_at: EpochTimestamp | None = Field(None, description="When task was revoked last")
    rejected_at: EpochTimestamp | None = Field(None, description="When task was rejected by worker")
    runtime: float | None = Field(None, description="How long task executed in seconds")
    last_updated: EpochTimestamp = Field(description="When task last event published")

    args: str | None = Field(None, description="Positional arguments provided to task (truncated)")
    kwargs: str | None = Field(None, description="Keyword arguments provided to task (truncated)")
    eta: str | None = Field(None, description="Absolute time when task should be executed")
    expires: str | None = Field(None, description="Absolute time when task should be expired")
    retries: int | None = Field(None, description="Retry count")
    exchange: str | None = Field(None, description="Broker exchange name")
    routing_key: str | None = Field(None, description="Broker routing key")
    root_id: str | None = Field(None, description="Root Task ID")
    parent_id: str | None = Field(None, description="Parent Task ID")
    children: list[str] = Field(description="Children Task IDs")
    worker: str | None = Field(None, description="Executing worker hostname")
    result: str | None = Field(None, description="Task returned result")
    exception: str | None = Field(None, description="Task failure exception message")
    traceback: str | None = Field(None, description="Task failure traceback")

    @classmethod
    def from_celery_task(cls, task: CeleryTask) -> Self:
        return cls(
            id=task.id,
            type=task.name,
            state=task.state,
            # timings
            sent_at=task.sent or task.timestamp,
            received_at=task.received,
            started_at=task.started,
            succeeded_at=task.succeeded,
            failed_at=task.failed,
            retried_at=task.retried,
            revoked_at=task.revoked,
            rejected_at=task.rejected,
            runtime=task.runtime,
            last_updated=task.timestamp,
            # metadata
            args=task.args,
            kwargs=task.kwargs,
            eta=task.eta,
            expires=task.expires,
            retries=task.retries,
            exchange=task.exchange,
            routing_key=task.routing_key,
            root_id=task.root_id,
            parent_id=task.parent_id,
            children=[child.id for child in task.children],
            client=task.client,
            worker=f"{task.worker.hostname}-{task.worker.pid}" if task.worker is not None else None,
            result=task.result,
            exception=task.exception,
            traceback=task.traceback,
        )


class TaskResult(BaseModel):
    id: str = Field(description="Task ID")
    type: str | None = Field(None, description="Task type name")
    state: TaskState = Field(description="Task current state")
    queue: str | None = Field(None, description="Task queue name")
    result: Any | None = Field(None, description="Task return value or exception")
    traceback: str | None = Field(None, description="Task exception traceback")
    ignored: bool = Field(description="Task result is ignored")
    args: list[Any] = Field(description="Task positional arguments")
    kwargs: str = Field(description="Task keyword arguments")
    retries: int = Field(description="Task retries count")
    worker: str | None = Field(None, description="Executing worker id")

    @field_validator("result", mode="before")
    @classmethod
    def result_serializer(cls, value: Any) -> Any:
        if isinstance(value, Exception):
            return repr(value)
        else:
            return value
