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

"""Tests for the configurable ``public_url`` of the A2A ``AgentCard``.

``AgentkitAgentServerApp`` historically called ``to_a2a`` without
host/port/protocol, so the exposed ``AgentCard.url`` was always
``http://localhost:8000``. These tests cover the default (backward
compatible) behaviour, the custom ``public_url`` override, and the
``_resolve_public_url_components`` helper in isolation.
"""

from __future__ import annotations

import pytest
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.base_agent import BaseAgent
from starlette.testclient import TestClient
from veadk.memory.short_term_memory import ShortTermMemory

from agentkit.apps.agent_server_app.agent_server_app import (
    AgentkitAgentServerApp,
    _resolve_public_url_components,
)


# ---------------------------------------------------------------------------
# _resolve_public_url_components unit tests (no network/runtime)
# ---------------------------------------------------------------------------


def test_resolve_public_url_components_explicit_port():
    protocol, host, port = _resolve_public_url_components(
        "https://agents.example.com:8443"
    )
    assert (protocol, host, port) == ("https", "agents.example.com", 8443)


def test_resolve_public_url_components_http_explicit_port():
    protocol, host, port = _resolve_public_url_components(
        "http://10.0.0.1:9000"
    )
    assert (protocol, host, port) == ("http", "10.0.0.1", 9000)


def test_resolve_public_url_components_defaults_https_port():
    protocol, host, port = _resolve_public_url_components(
        "https://agents.example.com"
    )
    assert (protocol, host, port) == ("https", "agents.example.com", 443)


def test_resolve_public_url_components_defaults_http_port():
    protocol, host, port = _resolve_public_url_components(
        "http://agents.example.com"
    )
    assert (protocol, host, port) == ("http", "agents.example.com", 80)


def test_resolve_public_url_components_rejects_missing_scheme():
    with pytest.raises(ValueError, match="scheme and host"):
        _resolve_public_url_components("agents.example.com:8443")


def test_resolve_public_url_components_rejects_missing_host():
    with pytest.raises(ValueError, match="scheme and host"):
        _resolve_public_url_components("https:///path")


# ---------------------------------------------------------------------------
# Integration: AgentCard.url via the mounted A2A well-known route
# ---------------------------------------------------------------------------


def _make_app(public_url=None) -> AgentkitAgentServerApp:
    root_agent = BaseAgent(
        name="agent_server_public_url_test_agent",
        description="Agent used to verify configurable AgentCard public URL.",
    )
    kwargs = {"agent": root_agent, "short_term_memory": ShortTermMemory(backend="local")}
    if public_url is not None:
        kwargs["public_url"] = public_url
    return AgentkitAgentServerApp(**kwargs)


def test_default_public_url_is_localhost_8000():
    server = _make_app()
    assert server.public_url is None

    with TestClient(server.app) as client:
        response = client.get(AGENT_CARD_WELL_KNOWN_PATH)

    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "agent_server_public_url_test_agent"
    # Backward compatible: no public_url -> default localhost:8000 endpoint.
    assert card["url"] == "http://localhost:8000"


def test_custom_public_url_overrides_agent_card_url():
    server = _make_app(public_url="http://public.example.com:9000")
    assert server.public_url == "http://public.example.com:9000"

    with TestClient(server.app) as client:
        response = client.get(AGENT_CARD_WELL_KNOWN_PATH)

    assert response.status_code == 200
    card = response.json()
    assert card["url"] == "http://public.example.com:9000"


def test_custom_https_public_url_overrides_agent_card_url():
    server = _make_app(public_url="https://agents.example.com:8443")

    with TestClient(server.app) as client:
        response = client.get(AGENT_CARD_WELL_KNOWN_PATH)

    assert response.status_code == 200
    assert response.json()["url"] == "https://agents.example.com:8443"
