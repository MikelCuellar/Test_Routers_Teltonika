"""Tests unitarios para el cliente Teltonika RutOS."""
import json
import pytest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from teltonika_api_client import TeltonikaRutOSClient


@pytest.fixture
def mock_client():
    return TeltonikaRutOSClient(
        host="192.168.1.1",
        port=443,
        username="admin",
        password="test-password",
    )


def test_login_ubus_success(mock_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": [0, {"ubus_rpc_session": "abc123sessiontoken"}],
    }
    with patch.object(mock_client.session, "post", return_value=mock_resp):
        ok = mock_client.login_ubus()
        assert ok is True
        assert mock_client.ubus_session_id == "abc123sessiontoken"


def test_login_ubus_failure(mock_client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32002, "message": "Access denied"},
    }
    with patch.object(mock_client.session, "post", return_value=mock_resp):
        ok = mock_client.login_ubus()
        assert ok is False
        assert mock_client.ubus_session_id is None


def test_get_system_info_rest_success(mock_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "device": "RUT955",
        "firmware": "RUT9_R_00.07.06.3",
        "serial": "1102938475",
    }
    with patch.object(mock_client.session, "get", return_value=mock_resp):
        info = mock_client.get_system_info_rest()
        assert info is not None
        assert info["device"] == "RUT955"
        assert info["serial"] == "1102938475"


def test_set_digital_output(mock_client):
    mock_client.ubus_session_id = "test-session"
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": [0, {"status": "ok"}],
    }
    with patch.object(mock_client.session, "post", return_value=mock_resp):
        res = mock_client.set_digital_output("dout1", 1)
        assert res is True
