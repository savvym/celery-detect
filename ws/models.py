import logging
from typing import Self

from user_agents import parse as user_agent_parse
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


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
            user_agent = user_agent_parse("")

        return cls(
            os=user_agent.os.family if user_agent else None,
            os_version=user_agent.os.version_string if user_agent else None,
            device_family=user_agent.device.family if user_agent else None,
            device_model=user_agent.device.model if user_agent else None,
            device_brand=user_agent.device.brand if user_agent else None,
            browser=user_agent.browser.family if user_agent else None,
            browser_version=user_agent.browser.version_string if user_agent else None,
        )


class ClientInfo(BaseModel):
    host: str = Field(description="Client Hostname")
    port: int = Field(description="Client Port")
    state: str = Field(description="Connection State")
    is_secure: bool = Field(description="Connection Secure Scheme WSS")
    user_agent: UserAgentInfo | None = Field(None, description="User agent details")

    @classmethod
    async def from_scope(cls, scope) -> Self:
        headers = dict(scope['headers'])
        user_agent_string = headers.get(b'user-agent', b"").decode('utf-8')
        client = scope.get('client', ('', 0))
        state = 'connected' if scope['type'] == 'websocket.connect' else 'disconnected'
        is_secure = scope['scheme'] == 'wss'

        return cls(
            host=client[0],
            port=client[1],
            state=state,
            is_secure=is_secure,
            user_agent=UserAgentInfo.parse(user_agent_string),
        )
