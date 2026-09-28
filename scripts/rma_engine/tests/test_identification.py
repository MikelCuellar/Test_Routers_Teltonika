"""Módulo 1: Pruebas de Identificación y Metadatos de Manufactura."""
import re
from typing import Tuple
from ..device_session import DeviceSession
from ..models import DeviceMetadata, ItemResult, ModuleResult, TestStatus


def run_identification_tests(session: DeviceSession) -> Tuple[ModuleResult, DeviceMetadata]:
    module = ModuleResult(
        module_id="mod_identification",
        module_name="Identificación y Metadatos de Fábrica",
        status=TestStatus.PASS,
        summary="Verificación de integridad de EEPROM de manufactura y metadatos de hardware.",
    )
    meta = DeviceMetadata()

    # 1. Serial Number (mnf_info --sn)
    res_sn = session.run("mnf_info --sn 2>/dev/null || cat /sys/devices/virtual/dmi/id/product_serial 2>/dev/null")
    sn = res_sn.output.strip()
    if sn and len(sn) >= 6:
        meta.serial_number = sn
        module.add_item(ItemResult(
            name="Número de Serie (Serial Number)",
            status=TestStatus.PASS,
            message="Serial number leído correctamente de EEPROM",
            observed=sn,
            expected="10 dígitos numéricos",
        ))
    else:
        module.add_item(ItemResult(
            name="Número de Serie (Serial Number)",
            status=TestStatus.FAIL,
            message="No se pudo leer el número de serie de fábrica (EEPROM vacía o corrupta)",
            observed=sn or "VACÍO",
        ))

    # 2. MAC Address (mnf_info --mac / --maceth)
    res_mac = session.run("mnf_info --mac 2>/dev/null || mnf_info --maceth 2>/dev/null || cat /sys/class/net/eth0/address 2>/dev/null")
    mac = res_mac.output.strip()
    mac_valid = bool(re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac))
    if mac and mac_valid:
        meta.mac_address = mac.upper()
        module.add_item(ItemResult(
            name="Dirección MAC de Fábrica",
            status=TestStatus.PASS,
            message="Dirección MAC física válida",
            observed=meta.mac_address,
            expected="Formato IEEE 802 XX:XX:XX:XX:XX:XX",
        ))
    else:
        module.add_item(ItemResult(
            name="Dirección MAC de Fábrica",
            status=TestStatus.FAIL,
            message="Dirección MAC inválida o ausente en memoria de fábrica",
            observed=mac or "N/A",
        ))

    # 3. Código de Producto / Nombre del Modelo (mnf_info --name)
    res_name = session.run("mnf_info --name 2>/dev/null || cat /tmp/sysinfo/model 2>/dev/null")
    prod_name = res_name.output.strip()
    if prod_name:
        meta.product_code = prod_name
        # Extraer modelo base (ej: RUT240, RUT955, etc.)
        for cand in ["RUT240", "RUT241", "RUT200", "RUT950", "RUT951", "RUT955", "RUT956", "RUTX09", "RUTX11", "RUTX50", "TRB140", "TRB245"]:
            if cand in prod_name.upper():
                meta.model_name = cand
                break
        if meta.model_name == "Desconocido":
            meta.model_name = prod_name.split()[0]

        module.add_item(ItemResult(
            name="Modelo & Código de Producto",
            status=TestStatus.PASS,
            message=f"Dispositivo identificado como {meta.model_name}",
            observed=prod_name,
        ))
    else:
        meta.model_name = "RUT_GENERIC"
        module.add_item(ItemResult(
            name="Modelo & Código de Producto",
            status=TestStatus.WARNING,
            message="No se pudo obtener el nombre exacto mediante mnf_info, asumiendo modelo genérico",
            observed="N/A",
        ))

    # 4. Hardware Revision (mnf_info --hwver)
    res_hw = session.run("mnf_info --hwver 2>/dev/null")
    hwver = res_hw.output.strip()
    if hwver:
        meta.hardware_revision = hwver
        module.add_item(ItemResult(
            name="Revisión de Hardware (HW Rev)",
            status=TestStatus.PASS,
            message="Revisión de placa leída exitosamente",
            observed=hwver,
        ))
    else:
        module.add_item(ItemResult(
            name="Revisión de Hardware (HW Rev)",
            status=TestStatus.WARNING,
            message="No se detectó campo de revisión de hardware",
            observed="N/A",
        ))

    # 5. Batch Number (mnf_info --batch)
    res_batch = session.run("mnf_info --batch 2>/dev/null")
    batch = res_batch.output.strip()
    if batch:
        meta.batch_number = batch
        module.add_item(ItemResult(
            name="Número de Lote (Batch Number)",
            status=TestStatus.PASS,
            message="Lote de fabricación verificado",
            observed=batch,
        ))

    # 6. Versión de Firmware y Kernel
    res_fw = session.run("cat /etc/version 2>/dev/null || cat /etc/openwrt_version 2>/dev/null")
    meta.firmware_version = res_fw.output.strip() or "Desconocido"

    res_kernel = session.run("uname -r")
    meta.kernel_version = res_kernel.output.strip() or "Desconocido"

    module.add_item(ItemResult(
        name="Versión de Firmware RutOS",
        status=TestStatus.PASS,
        message="Firmware activo registrado",
        observed=f"RutOS {meta.firmware_version} (Kernel {meta.kernel_version})",
    ))

    return module, meta
