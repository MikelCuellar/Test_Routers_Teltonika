"""Orquestador central de la Suite de Diagnóstico RMA Teltonika."""
import logging
import time
from typing import Callable, Optional
from .device_session import DeviceSession
from .model_capabilities import resolve_profile
from .models import DeviceMetadata, DiagnosticReport
from .tests.test_cellular import run_cellular_tests
from .tests.test_ethernet import run_ethernet_tests
from .tests.test_gps import run_gps_tests
from .tests.test_identification import run_identification_tests
from .tests.test_io_serial import run_io_serial_tests
from .tests.test_system import run_system_tests
from .tests.test_wifi import run_wifi_tests

logger = logging.getLogger("RMAOrchestrator")


class RMAOrchestrator:
    """Ejecuta secuencialmente la batería de pruebas de hardware y compila el informe de garantía."""

    def __init__(
        self,
        session: DeviceSession,
        ticket_id: str = "TICKET-AUTO",
        engineer_name: str = "Ingeniero de Garantías",
        client_name: str = "Cliente Corporativo",
    ):
        self.session = session
        self.ticket_id = ticket_id
        self.engineer_name = engineer_name
        self.client_name = client_name

    def execute(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> DiagnosticReport:
        """Ejecuta todos los módulos de prueba y retorna DiagnosticReport."""
        report = DiagnosticReport(
            ticket_id=self.ticket_id,
            engineer_name=self.engineer_name,
            client_name=self.client_name,
        )

        steps = [
            ("Módulo 1: Identificación y Metadatos de Fábrica", 1),
            ("Módulo 2: Sistema Base, CPU, RAM y Flash", 2),
            ("Módulo 3: Módem Celular, SIM1/2 y Etapa RF", 3),
            ("Módulo 4: Switch Ethernet y Puertos Físicos", 4),
            ("Módulo 5: Radio Wi-Fi y Escaneo de Espectro", 5),
            ("Módulo 6: Receptor Satelital GNSS / GPS", 6),
            ("Módulo 7: Entradas/Salidas y Puertos Seriales", 7),
        ]
        total_steps = len(steps)

        # 1. Identificación
        if progress_callback:
            progress_callback(steps[0][0], 1, total_steps)
        mod_ident, meta = run_identification_tests(self.session)
        report.device = meta
        report.modules.append(mod_ident)

        # Resolver perfil de hardware del modelo
        profile = resolve_profile(meta.model_name or meta.product_code)
        logger.info(f"Perfil de hardware resuelto: {profile.model} (Familia: {profile.family})")

        # 2. Sistema Base
        if progress_callback:
            progress_callback(steps[1][0], 2, total_steps)
        mod_sys = run_system_tests(self.session)
        report.modules.append(mod_sys)

        # 3. Celular y SIM
        if progress_callback:
            progress_callback(steps[2][0], 3, total_steps)
        mod_cell = run_cellular_tests(self.session, profile, meta)
        report.modules.append(mod_cell)

        # 4. Ethernet
        if progress_callback:
            progress_callback(steps[3][0], 4, total_steps)
        mod_eth = run_ethernet_tests(self.session, profile)
        report.modules.append(mod_eth)

        # 5. Wi-Fi
        if progress_callback:
            progress_callback(steps[4][0], 5, total_steps)
        mod_wifi = run_wifi_tests(self.session, profile)
        report.modules.append(mod_wifi)

        # 6. GPS
        if progress_callback:
            progress_callback(steps[5][0], 6, total_steps)
        mod_gps = run_gps_tests(self.session, profile)
        report.modules.append(mod_gps)

        # 7. I/O y Seriales
        if progress_callback:
            progress_callback(steps[6][0], 7, total_steps)
        mod_io = run_io_serial_tests(self.session, profile)
        report.modules.append(mod_io)

        # Calcular dictamen final
        report.calculate_verdict()

        return report
