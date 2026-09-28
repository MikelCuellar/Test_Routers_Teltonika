"""Módulo 3: Pruebas Exhaustivas de Módem Celular, Ranuras SIM y RF."""
import re
import time
from typing import Optional
from ..device_session import DeviceSession
from ..model_capabilities import HardwareProfile
from ..models import DeviceMetadata, ItemResult, ModuleResult, TestStatus


def run_cellular_tests(session: DeviceSession, profile: HardwareProfile, meta: DeviceMetadata) -> ModuleResult:
    module = ModuleResult(
        module_id="mod_cellular",
        module_name="Módem Celular & Ranuras SIM",
        status=TestStatus.PASS,
        summary="Pruebas de comunicación AT, chipset LTE/5G, lectores de tarjeta SIM1/SIM2 y etapa RF.",
    )

    # 1. Detección del Módem Celular e IMEI (gsmctl -i)
    res_imei = session.run("gsmctl -i 2>/dev/null")
    imei = res_imei.output.strip()
    imei_clean = re.sub(r"[^\d]", "", imei)

    if imei_clean and len(imei_clean) == 15:
        meta.modem_imei = imei_clean
        module.add_item(ItemResult(
            name="Chipset Celular & IMEI",
            status=TestStatus.PASS,
            message="Módem interno responde en bus serie/USB con IMEI válido",
            observed=f"IMEI: {imei_clean}",
            expected="15 dígitos numéricos",
        ))
    else:
        module.add_item(ItemResult(
            name="Chipset Celular & IMEI",
            status=TestStatus.FAIL,
            message="Módem celular no responde a comandos o no es detectado en placa (Hardware Defective)",
            observed=imei or "SIN RESPUESTA",
            expected="IMEI válido de 15 dígitos",
        ))
        # Si el módem no responde, el resto de pruebas celulares fallan
        return module

    # 2. Fabricante, Modelo y Firmware del Módem
    res_modem_info = session.run("gsmctl -m 2>/dev/null && gsmctl -w 2>/dev/null && gsmctl -y 2>/dev/null")
    lines = [l.strip() for l in res_modem_info.output.splitlines() if l.strip()]
    if lines:
        meta.modem_model = lines[0]
        meta.modem_firmware = lines[-1] if len(lines) > 1 else "N/A"
        module.add_item(ItemResult(
            name="Modelo & Firmware del Módem",
            status=TestStatus.PASS,
            message="Información del módulo celular obtenida exitosamente",
            observed=f"{meta.modem_model} | FW: {meta.modem_firmware}",
        ))

    # 3. Prueba de Comandos AT Básicos (gsmctl -A "AT")
    at_res = session.run("gsmctl -A 'AT' 2>/dev/null")
    if "OK" in at_res.output:
        module.add_item(ItemResult(
            name="Canal de Comandos AT (Modem UART/CDC-ACM)",
            status=TestStatus.PASS,
            message="Canal serie AT bidireccional completamente operativo",
            observed="Respuesta 'OK' recibida",
            expected="OK",
        ))
    else:
        module.add_item(ItemResult(
            name="Canal de Comandos AT (Modem UART/CDC-ACM)",
            status=TestStatus.FAIL,
            message="Módem no responde a comandos AT en puerto de control",
            observed=at_res.output or "Timeout",
        ))

    # 4. Lector de Tarjeta SIM 1 (ICCID)
    sim1_res = session.run("gsmctl -I 2>/dev/null")
    iccid = sim1_res.output.strip()
    iccid_clean = re.sub(r"[^\d]", "", iccid)

    if iccid_clean and len(iccid_clean) >= 18:
        module.add_item(ItemResult(
            name="Ranura SIM 1 (Lectura de Chip)",
            status=TestStatus.PASS,
            message="Tarjeta SIM reconocida físicamente (contactos y bus ISO 7816 íntegros)",
            observed=f"ICCID: {iccid_clean}",
            expected="ICCID de 19 o 20 dígitos",
        ))
    else:
        # Si no hay SIM en el laboratorio, se cataloga como WARNING para que el técnico la inserte
        module.add_item(ItemResult(
            name="Ranura SIM 1 (Lectura de Chip)",
            status=TestStatus.WARNING,
            message="No se detecta tarjeta SIM en ranura 1 (Insertar SIM de pruebas para validar circuito)",
            observed=iccid or "Sin SIM insertada",
            expected="ICCID válido",
        ))

    # 5. Prueba de Ranura Dual-SIM y Multiplexor de Conmutación (si aplica al modelo)
    if profile.has_dual_sim_switch and profile.sim_slots >= 2:
        # Obtener ranura activa actual
        curr_sim_res = session.run("gsmctl --sim 2>/dev/null || ubus call sim get 2>/dev/null")
        curr_sim = "sim1" if "1" in curr_sim_res.output else "sim2"

        # Probar conmutación a SIM 2
        switch_res = session.run("gsmctl -S switch 2>/dev/null || ubus call sim switch '{\"sim\":\"sim2\"}' 2>/dev/null")
        time.sleep(2)  # Dar tiempo al multiplexor de conmutar líneas eléctricas

        # Leer respuesta en la otra ranura
        sim2_read = session.run("gsmctl -I 2>/dev/null || gsmctl --sim 2>/dev/null")
        
        # Restaurar a ranura original
        session.run("gsmctl -S switch 2>/dev/null || ubus call sim switch '{\"sim\":\"sim1\"}' 2>/dev/null")

        if switch_res.success:
            module.add_item(ItemResult(
                name="Multiplexor Dual-SIM (Conmutación SIM1 <-> SIM2)",
                status=TestStatus.PASS,
                message="Circuito de conmutación de ranura dual responde y ejecuta cambio por hardware",
                observed=f"Conmutación ejecutada exitosamente | Lectura: {sim2_read.output.strip()[:30]}",
            ))
        else:
            module.add_item(ItemResult(
                name="Multiplexor Dual-SIM (Conmutación SIM1 <-> SIM2)",
                status=TestStatus.FAIL,
                message="Falla en circuito conmutador Dual-SIM (Relé electrónico o integrado de conmutación dañado)",
                observed=switch_res.stderr or "Error de conmutación",
            ))
    elif profile.sim_slots < 2:
        module.add_item(ItemResult(
            name="Multiplexor Dual-SIM",
            status=TestStatus.NOT_EQUIPPED,
            message="Este modelo es Single SIM por diseño de hardware",
        ))

    # 6. Etapa de Radiofrecuencia (RF) y Calidad de Señal
    res_signal = session.run("gsmctl -q 2>/dev/null")
    rssi_str = res_signal.output.strip()
    try:
        rssi_val = int(rssi_str)
        if 0 <= rssi_val <= 31:
            # Índice CSQ estándar (0-31) -> convertir a dBm
            rssi_dbm = -113 + (rssi_val * 2)
        elif rssi_val < 0:
            rssi_dbm = rssi_val
        else:
            rssi_dbm = -rssi_val

        # Criterio: Señal válida si está entre -115 y -40 dBm
        if -115 <= rssi_dbm <= -40:
            status = TestStatus.PASS
            msg = f"Etapa de recepción RF y antena móvil operativa (RSSI: {rssi_dbm} dBm)"
        else:
            status = TestStatus.WARNING
            msg = f"Nivel de señal bajo o antena desconectada (RSSI: {rssi_dbm} dBm)"

        # Obtener RSRP y RSRQ si están disponibles
        rsrp_res = session.run("gsmctl -X 2>/dev/null")
        rsrq_res = session.run("gsmctl -Z 2>/dev/null")
        extra_rf = f" | RSRP: {rsrp_res.output.strip()} dBm | RSRQ: {rsrq_res.output.strip()} dB" if rsrp_res.output else ""

        module.add_item(ItemResult(
            name="Sensibilidad de Radiofrecuencia RF (Señal Celular)",
            status=status,
            message=msg,
            observed=f"RSSI: {rssi_dbm} dBm{extra_rf}",
            expected="-110 dBm a -50 dBm",
        ))
    except Exception:
        module.add_item(ItemResult(
            name="Sensibilidad de Radiofrecuencia RF (Señal Celular)",
            status=TestStatus.WARNING,
            message="Sin señal celular detectable (Verificar si la antena 4G/5G y SIM están conectadas)",
            observed=rssi_str or "0 / Sin señal",
        ))

    # 7. Estado de Registro en Red de Operador
    reg_res = session.run("gsmctl -a 2>/dev/null")
    oper_res = session.run("gsmctl -o 2>/dev/null")
    reg_code = reg_res.output.strip()
    oper_name = oper_res.output.strip()

    # 1=Home, 5=Roaming
    if reg_code in ["1", "5"]:
        module.add_item(ItemResult(
            name="Registro en Red Móvil (Base Station Attach)",
            status=TestStatus.PASS,
            message=f"Módem sincronizado y autenticado con radiobase ({oper_name or 'Operador Activo'})",
            observed=f"Estado: Registrado ({reg_code}) | Operador: {oper_name}",
        ))
    else:
        module.add_item(ItemResult(
            name="Registro en Red Móvil (Base Station Attach)",
            status=TestStatus.WARNING,
            message=f"Módem no registrado en red (Estado: {reg_code}). Requiere SIM con plan activo y cobertura.",
            observed=f"Código de registro: {reg_code}",
        ))

    return module
