import logging
import zipfile
from io import BytesIO
from typing import Any, NamedTuple
from pathlib import Path

from asgiref.sync import sync_to_async
from pydantic_core import to_json

from celery_detect import settings
from events.receiver import state
from server_info.models import ClientDebugInfo, ServerInfo, StateDump
from tasks.models import Task
from workers.models import Worker
from ws.managers import events_manager
from ws.models import ClientInfo, UserAgentInfo

logger = logging.getLogger(__name__)

Settings = settings.DebugBundleSettings


def dump_model(file: zipfile.ZipFile, filename: str, model: Any) -> None:
    try:
        settings_json = to_json(model, indent=4)
        file.writestr(filename, settings_json)
    except Exception as e:
        logger.exception(f"Failed to dump object {model!r} to file {filename!r}: {e}")


@sync_to_async
def dump_file(file: zipfile.ZipFile, filename: str, path: Path) -> None:
    if not path.is_file():
        logger.info(f"Unable to find file at {path!r}, skipping...")
        return

    with path.open('r', encoding='utf-8') as f:
        content = f.read()
        file.writestr(filename, content)


class DebugBundleData(NamedTuple):
    settings: Settings
    log_path: str
    browser: UserAgentInfo
    client_info: ClientDebugInfo
    connections: list[ClientInfo]
    state_dump: StateDump
    server_info: ServerInfo


def generate_bundle_file(data: DebugBundleData) -> BytesIO:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as file:
        dump_file(file, "config.py", Path(data.settings.config_path))
        dump_file(file, "app.log", Path(data.log_path))
        dump_model(file, "settings.json", data.settings)
        dump_model(file, "browser.json", data.browser)
        dump_model(file, "client_info.json", data.client_info)
        dump_model(file, "connections.json", data.connections)
        dump_model(file, "state.json", data.state_dump)
        dump_model(file, "server_info.json", data.server_info)

    buffer.seek(0)
    return buffer


def get_state_dump() -> StateDump:
    return StateDump(
        tasks=[Task.from_celery_task(task) for _, task in state.tasks_by_time()],
        workers=[Worker.from_celery_worker(worker) for worker in state.workers.itervalues()],
    )


@sync_to_async
def create_debug_bundle(scope, client_info: ClientDebugInfo) -> BytesIO:
    headers = dict(scope['headers'])
    user_agent = headers.get(b'user-agent', b"").decode('utf-8')
    bundle_data = DebugBundleData(
        settings=Settings,
        log_path=Settings['LOG_FILE_PATH'],
        browser=UserAgentInfo.parse(user_agent),
        client_info=client_info,
        connections=list(events_manager.get_clients()),
        state_dump=get_state_dump(),
        server_info=ServerInfo.create(scope, state),
    )
    return generate_bundle_file(bundle_data)
