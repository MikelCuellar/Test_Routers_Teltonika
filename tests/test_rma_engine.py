"""Tests unitarios y de integración para la Suite RMA Teltonika."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from rma_engine.device_session import CommandResult, DeviceSession
from rma_engine.model_capabilities import resolve_profile
from rma_engine.models import DeviceMetadata, DiagnosticReport, RMAVerdict, TestStatus
from rma_engine.orchestrator import RMAOrchestrator
from rma_engine.report_generator import render_html_report, render_markdown_report, save_reports
from rma_engine.tests.test_cellular import run_cellular_tests
from rma_engine.tests.test_identification import run_identification_tests
from rma_engine.tests.test_system import run_system_tests


def test_model_capabilities_resolution():
    rut240 = resolve_profile("RUT24006E000")
    assert rut240.model == "RUT240"
    assert rut240.sim_slots == 1
    assert rut240.has_dual_sim_switch is False
    assert rut240.has_gps is False
    assert rut240.has_wifi is True

    rut955 = resolve_profile("RUT95500XXXX")
    assert rut955.model == "RUT955"
    assert rut955.sim_slots == 2
    assert rut955.has_dual_sim_switch is True
    assert rut955.has_gps is True
    assert rut955.has_rs232 is True
    assert rut955.has_rs485 is True
    assert rut955.has_relay is True

    trb140 = resolve_profile("TRB140")
    assert trb140.model == "TRB140"
    assert trb140.has_wifi is False
    assert trb140.ethernet_ports_count == 1


def test_identification_module_success():
    session = MagicMock(spec=DeviceSession)

    def fake_run(cmd, timeout=15.0):
        if "mnf_info --sn" in cmd:
            return CommandResult(cmd, 0, "1102938475\n", "")
        elif "mnf_info --mac" in cmd:
            return CommandResult(cmd, 0, "00:1E:42:1A:2B:3C\n", "")
        elif "mnf_info --name" in cmd:
            return CommandResult(cmd, 0, "RUT955003100\n", "")
        elif "mnf_info --hwver" in cmd:
            return CommandResult(cmd, 0, "0004\n", "")
        elif "mnf_info --batch" in cmd:
            return CommandResult(cmd, 0, "0012\n", "")
        elif "cat /etc/version" in cmd:
            return CommandResult(cmd, 0, "RUT9_R_00.07.06.3\n", "")
        elif "uname -r" in cmd:
            return CommandResult(cmd, 0, "5.4.229\n", "")
        return CommandResult(cmd, 0, "", "")

    session.run.side_effect = fake_run

    module, meta = run_identification_tests(session)
    assert module.status == TestStatus.PASS
    assert meta.serial_number == "1102938475"
    assert meta.mac_address == "00:1E:42:1A:2B:3C"
    assert meta.model_name == "RUT955"
    assert meta.hardware_revision == "0004"
    assert meta.batch_number == "0012"
    assert meta.firmware_version == "RUT9_R_00.07.06.3"


def test_system_module_flash_failure_detected():
    session = MagicMock(spec=DeviceSession)

    def fake_run(cmd, timeout=15.0):
        if "cat /proc/cpuinfo" in cmd:
            return CommandResult(cmd, 0, "system type : Qualcomm Atheros QCA9531\n", "")
        elif "free -m" in cmd:
            return CommandResult(cmd, 0, "Mem: 128 40 88 0 5 80\n", "")
        elif "flash_test" in cmd:
            # Simular memoria flash en Read-Only (falla de hardware común)
            return CommandResult(cmd, 0, "Read-only file system\nFAIL_RW\n", "")
        elif "thermal" in cmd:
            return CommandResult(cmd, 0, "42000\n", "")
        elif "dmesg" in cmd:
            return CommandResult(cmd, 0, "", "")
        return CommandResult(cmd, 0, "", "")

    session.run.side_effect = fake_run

    module = run_system_tests(session)
    assert module.status == TestStatus.FAIL
    flash_item = [i for i in module.items if "Flash" in i.name][0]
    assert flash_item.status == TestStatus.FAIL
    assert "Read-Only" in flash_item.message or "bloqueada" in flash_item.message


def test_cellular_module_defective_modem():
    session = MagicMock(spec=DeviceSession)
    session.run.return_value = CommandResult("gsmctl -i", -1, "", "gsmctl: modem not responding")

    profile = resolve_profile("RUT240")
    meta = DeviceMetadata(model_name="RUT240")

    module = run_cellular_tests(session, profile, meta)
    assert module.status == TestStatus.FAIL
    imei_item = [i for i in module.items if "IMEI" in i.name][0]
    assert imei_item.status == TestStatus.FAIL


def test_orchestrator_full_flow_approved(tmp_path):
    session = MagicMock(spec=DeviceSession)

    def fake_run(cmd, timeout=15.0):
        if "mnf_info --sn" in cmd:
            return CommandResult(cmd, 0, "1102938475\n", "")
        elif "mnf_info --mac" in cmd:
            return CommandResult(cmd, 0, "00:1E:42:AA:BB:CC\n", "")
        elif "mnf_info --name" in cmd:
            return CommandResult(cmd, 0, "RUT240\n", "")
        elif "mnf_info --hwver" in cmd:
            return CommandResult(cmd, 0, "0002\n", "")
        elif "mnf_info --batch" in cmd:
            return CommandResult(cmd, 0, "0010\n", "")
        elif "cat /proc/cpuinfo" in cmd:
            return CommandResult(cmd, 0, "system type: MIPS 24KEc\n", "")
        elif "free -m" in cmd:
            return CommandResult(cmd, 0, "Mem: 64 20 44 0 2 40\n", "")
        elif "flash_test" in cmd:
            return CommandResult(cmd, 0, "SUCCESS_RW\n", "")
        elif "gsmctl -i" in cmd:
            return CommandResult(cmd, 0, "864123049182345\n", "")
        elif "gsmctl -m" in cmd:
            return CommandResult(cmd, 0, "EC25-AF\nQuectel\n", "")
        elif "gsmctl -A" in cmd:
            return CommandResult(cmd, 0, "OK\n", "")
        elif "gsmctl -I" in cmd:
            return CommandResult(cmd, 0, "8956021948291048291\n", "")
        elif "gsmctl -q" in cmd:
            return CommandResult(cmd, 0, "18\n", "")
        elif "gsmctl -a" in cmd:
            return CommandResult(cmd, 0, "1\n", "")
        elif "ip -br link" in cmd:
            return CommandResult(cmd, 0, "eth0 UP\neth1 UP\n", "")
        elif "carrier" in cmd:
            return CommandResult(cmd, 0, "1\n", "")
        elif "iw dev" in cmd or "iwinfo" in cmd:
            return CommandResult(cmd, 0, "interface wlan0\nSSID: TestWiFi\n", "")
        elif "ubus call ioman.gpio" in cmd:
            return CommandResult(cmd, 0, '{"value":"0"}\nSUCCESS_DOUT\n', "")
        return CommandResult(cmd, 0, "", "")

    session.run.side_effect = fake_run

    orch = RMAOrchestrator(
        session=session,
        ticket_id="TICKET-1234",
        engineer_name="Ing. Test",
        client_name="Test Corp",
    )

    report = orch.execute()
    assert report.verdict == RMAVerdict.APPROVED
    assert len(report.defective_components) == 0

    # Guardar reportes y validar
    saved = save_reports(report, tmp_path)
    assert Path(saved["html"]).exists()
    assert Path(saved["json"]).exists()
    assert Path(saved["md"]).exists()

    html_content = Path(saved["html"]).read_text(encoding="utf-8")
    assert "TICKET-1234" in html_content
    assert "1102938475" in html_content
    assert "APROBADO" in html_content


def test_orchestrator_full_flow_defective():
    session = MagicMock(spec=DeviceSession)

    def fake_run(cmd, timeout=15.0):
        if "mnf_info --sn" in cmd:
            return CommandResult(cmd, 0, "9988776655\n", "")
        elif "mnf_info --mac" in cmd:
            return CommandResult(cmd, 0, "00:1E:42:99:88:77\n", "")
        elif "mnf_info --name" in cmd:
            return CommandResult(cmd, 0, "RUT955\n", "")
        elif "flash_test" in cmd:
            return CommandResult(cmd, 0, "FAIL_RW\n", "")
        elif "gsmctl -i" in cmd:
            return CommandResult(cmd, -1, "", "modem error")
        return CommandResult(cmd, 0, "", "")

    session.run.side_effect = fake_run

    orch = RMAOrchestrator(
        session=session,
        ticket_id="TICKET-FAIL-99",
        engineer_name="Ing. Test",
        client_name="Defective Corp",
    )

    report = orch.execute()
    assert report.verdict == RMAVerdict.DEFECTIVE
    assert len(report.defective_components) >= 2
