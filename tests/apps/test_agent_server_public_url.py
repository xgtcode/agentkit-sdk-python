# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for ``AgentkitAgentServerApp`` public_url configuration.

These tests verify that the ``public_url`` constructor parameter correctly
overrides the AgentCard URL exposed via the well-known A2A endpoint, while
preserving backward-compatible default behaviour when the parameter is omitted.
"""

from __future__ import annotations

import pytest
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.base_agent import BaseAgent
from starlette.testclient import TestClient
from veadk.memory.short_term_memory import ShortTermMemory

from agentkit.apps.agent_server_app.agent_server_app import (
    AgentkitAgentServerApp,
)


def _create_server(**kwargs) -> AgentkitAgentServerApp:
    return AgentkitAgentServerApp(
        agent=BaseAgent(
            name="public_url_test_agent",
            description="Agent for public_url tests.",
        ),
        short_term_memory=ShortTermMemory(backend="local"),
        **kwargs,
    )


def _fetch_agent_card(client: TestClient) -> dict:
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    return response.json()


def test_default_public_url_is_localhost():
    """Without public_url the AgentCard URL points to localhost:8000 (http)."""
    server = _create_server()
    with TestClient(server.app) as client:
        card = _fetch_agent_card(client)

    assert card["url"] == "http://localhost:8000"


def test_custom_public_url_https_with_port():
    """A fully-specified https URL overrides the AgentCard URL."""
    server = _create_server(public_url="https://agent.example.com:8443")
    with TestClient(server.app) as client:
        card = _fetch_agent_card(client)

    assert card["url"] == "https://agent.example.com:8443"


def test_custom_public_url_http_without_port():
    """An http URL without explicit port defaults to port 80."""
    server = _create_server(public_url="http://agent.example.com")
    with TestClient(server.app) as client:
        card = _fetch_agent_card(client)

    assert card["url"] == "http://agent.example.com:80"


def test_custom_public_url_https_without_port():
    """An https URL without explicit port defaults to port 443."""
    server = _create_server(public_url="https://agent.example.com")
    with TestClient(server.app) as client:
        card = _fetch_agent_card(client)

    assert card["url"] == "https://agent.example.com:443"


def test_public_url_missing_scheme_raises():
    with pytest.raises(ValueError, match="scheme"):
        _create_server(public_url="agent.example.com")


def test_public_url_missing_hostname_raises():
    with pytest.raises(ValueError, match="hostname"):
        _create_server(public_url="https:///")
