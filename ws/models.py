import logging
from enum import Enum
from typing import Self

from user_agents import parse as user_agent_parse
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class UserAgentInfo(BaseModel):
    os: str | None = Field(None, description="Operating System Name")
    os_version: str | None = Field(None, description="Operating System Version")
    device_family: str | None = Field(None, description="Device Family")
    device_brand: str | None = Field(None, description="Device Brand")
    device_model: str | None = Field(None, description="Device Model")
    browser: str | None = Field(None, description="Browser Name")
    browser_version: str | None = Field(None, description="Browser Version")

    @classmethod
    def parse(cls, user_agent_string: str) -> Self:
        try:
            user_agent = user_agent_parse(user_agent_string)
        except Exception as e:
            logger.exception(f"Failed to parse user agent header {user_agent_string!r}: {e}")
            user_agent = user_agent_parse("")  # 默认空解析结果

        # 返回 UserAgentInfo
        return cls(
            os=user_agent.os.family if user_agent.os.family else "Unknown OS",
            os_version=user_agent.os.version_string if user_agent.os.version_string else "Unknown Version",
            device_family=user_agent.device.family if user_agent.device.family else "Unknown Device",
            device_model=user_agent.device.model if user_agent.device.model else "Unknown Model",
            device_brand=user_agent.device.brand if user_agent.device.brand else "Unknown Brand",
            browser=user_agent.browser.family if user_agent.browser.family else "Unknown Browser",
            browser_version=user_agent.browser.version_string if user_agent.browser.version_string else "Unknown Version",
        )


class ClientInfo(BaseModel):
    host: str
    port: int
    state: ConnectionState  # 使用枚举值代替字符串
    is_secure: bool
    user_agent: UserAgentInfo | None

    @classmethod
    async def from_scope(cls, scope) -> Self:
        headers = dict(scope['headers'])
        user_agent_string = headers.get(b'user-agent', b"").decode('utf-8', errors='ignore')
        client = scope.get('client', ('', 0))
        state = ConnectionState.CONNECTED if scope['type'] == 'websocket.connect' else ConnectionState.DISCONNECTED
        is_secure = scope.get('scheme', '') == 'wss'

        logger.info(f"Client {client[0]}:{client[1]} {state.value}, user-agent: {user_agent_string}")

        return cls(
            host=client[0],
            port=client[1],
            state=state,
            is_secure=is_secure,
            user_agent=UserAgentInfo.parse(user_agent_string),
        )
