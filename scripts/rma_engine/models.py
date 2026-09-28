"""Modelos de datos y estados para la Suite de Diagnóstico RMA Teltonika."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import datetime


class TestStatus(str, Enum):
    __test__ = False
    PASS = "PASS"                  # Prueba superada exitosamente
    FAIL = "FAIL"                  # Falla confirmada de hardware o función crítica
    WARNING = "WARNING"            # Advertencia / Métrica subóptima pero no determinante
    NOT_EQUIPPED = "NOT_EQUIPPED"  # El modelo no dispone físicamente de este componente
    SKIPPED = "SKIPPED"            # Prueba omitida por el usuario o falta de periférico


class RMAVerdict(str, Enum):
    APPROVED = "APROBADO (SIN DEFECTO DE HARDWARE)"
    DEFECTIVE = "DEFECTUOSO (FALLA DE HARDWARE CONFIRMADA)"
    OBSERVATION = "OBSERVACIÓN (REVISION DE FIRMWARE / CONFIGURACIÓN)"


@dataclass
class ItemResult:
    """Resultado de una comprobación individual dentro de un módulo."""
    name: str
    status: TestStatus
    message: str
    observed: Optional[str] = None
    expected: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "observed": self.observed,
            "expected": self.expected,
            "details": self.details,
        }


@dataclass
class ModuleResult:
    """Resultado consolidado de un módulo de prueba (ej: Módem Celular)."""
    module_id: str
    module_name: str
    status: TestStatus
    items: List[ItemResult] = field(default_factory=list)
    summary: str = ""

    def add_item(self, item: ItemResult) -> None:
        self.items.append(item)
        self._recalculate_status()

    def _recalculate_status(self) -> None:
        # Si hay al menos un FAIL -> Módulo es FAIL
        # Si no hay FAIL pero hay WARNING -> Módulo es WARNING
        # Si todos son NOT_EQUIPPED o SKIPPED -> NOT_EQUIPPED / SKIPPED
        # Si todo es PASS -> PASS
        statuses = [i.status for i in self.items]
        if TestStatus.FAIL in statuses:
            self.status = TestStatus.FAIL
        elif TestStatus.WARNING in statuses:
            self.status = TestStatus.WARNING
        elif all(s == TestStatus.NOT_EQUIPPED for s in statuses):
            self.status = TestStatus.NOT_EQUIPPED
        elif all(s in (TestStatus.PASS, TestStatus.NOT_EQUIPPED, TestStatus.SKIPPED) for s in statuses):
            self.status = TestStatus.PASS
        else:
            self.status = TestStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "status": self.status.value,
            "summary": self.summary,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class DeviceMetadata:
    """Metadatos de fábrica y de hardware extraídos del router."""
    model_name: str = "Desconocido"
    product_code: str = "N/A"
    serial_number: str = "N/A"
    mac_address: str = "N/A"
    hardware_revision: str = "N/A"
    batch_number: str = "N/A"
    firmware_version: str = "N/A"
    kernel_version: str = "N/A"
    modem_model: str = "N/A"
    modem_imei: str = "N/A"
    modem_firmware: str = "N/A"

    def to_dict(self) -> Dict[str, str]:
        return {
            "model_name": self.model_name,
            "product_code": self.product_code,
            "serial_number": self.serial_number,
            "mac_address": self.mac_address,
            "hardware_revision": self.hardware_revision,
            "batch_number": self.batch_number,
            "firmware_version": self.firmware_version,
            "kernel_version": self.kernel_version,
            "modem_model": self.modem_model,
            "modem_imei": self.modem_imei,
            "modem_firmware": self.modem_firmware,
        }


@dataclass
class DiagnosticReport:
    """Reporte técnico maestro de certificación RMA."""
    ticket_id: str
    engineer_name: str
    client_name: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    device: DeviceMetadata = field(default_factory=DeviceMetadata)
    modules: List[ModuleResult] = field(default_factory=list)
    verdict: RMAVerdict = RMAVerdict.APPROVED
    defective_components: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)

    def calculate_verdict(self) -> None:
        self.defective_components = []
        self.observations = []

        has_fail = False
        has_warn = False

        for mod in self.modules:
            for item in mod.items:
                if item.status == TestStatus.FAIL:
                    has_fail = True
                    self.defective_components.append(f"{mod.module_name}: {item.name} — {item.message}")
                elif item.status == TestStatus.WARNING:
                    has_warn = True
                    self.observations.append(f"{mod.module_name}: {item.name} — {item.message}")

        if has_fail:
            self.verdict = RMAVerdict.DEFECTIVE
        elif has_warn:
            self.verdict = RMAVerdict.OBSERVATION
        else:
            self.verdict = RMAVerdict.APPROVED

    def get_stats(self) -> Dict[str, int]:
        total = 0
        passes = 0
        fails = 0
        warnings = 0
        not_eq = 0
        for m in self.modules:
            for i in m.items:
                total += 1
                if i.status == TestStatus.PASS:
                    passes += 1
                elif i.status == TestStatus.FAIL:
                    fails += 1
                elif i.status == TestStatus.WARNING:
                    warnings += 1
                elif i.status == TestStatus.NOT_EQUIPPED:
                    not_eq += 1
        return {
            "total_checks": total,
            "pass": passes,
            "fail": fails,
            "warning": warnings,
            "not_equipped": not_eq,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "engineer_name": self.engineer_name,
            "client_name": self.client_name,
            "timestamp": self.timestamp,
            "verdict": self.verdict.value,
            "defective_components": self.defective_components,
            "observations": self.observations,
            "stats": self.get_stats(),
            "device": self.device.to_dict(),
            "modules": [m.to_dict() for m in self.modules],
        }
