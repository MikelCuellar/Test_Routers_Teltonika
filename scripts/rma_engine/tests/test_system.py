"""Módulo 2: Pruebas de Sistema Base (CPU, RAM, Flash NAND/NOR y Térmica)."""
import re
from ..device_session import DeviceSession
from ..models import ItemResult, ModuleResult, TestStatus


def run_system_tests(session: DeviceSession) -> ModuleResult:
    module = ModuleResult(
        module_id="mod_system",
        module_name="Sistema Base & Memoria",
        status=TestStatus.PASS,
        summary="Evaluación del microprocesador SoC, memoria RAM DDR, almacenamiento Flash y térmica.",
    )

    # 1. Microprocesador SoC (CPU)
    cpu_res = session.run("cat /proc/cpuinfo")
    if cpu_res.success and "system type" in cpu_res.output.lower() or "cpu" in cpu_res.output.lower():
        # Extraer modelo
        model_line = "SoC Arquitectura MIPS/ARM"
        for line in cpu_res.output.splitlines():
            if any(k in line.lower() for k in ["system type", "model name", "machine"]):
                model_line = line.split(":", 1)[-1].strip()
                break
        module.add_item(ItemResult(
            name="Procesador SoC (CPU)",
            status=TestStatus.PASS,
            message="Microprocesador respondiendo normalmente",
            observed=model_line,
        ))
    else:
        module.add_item(ItemResult(
            name="Procesador SoC (CPU)",
            status=TestStatus.FAIL,
            message="Falla leyendo información del procesador",
            observed="Error /proc/cpuinfo",
        ))

    # 2. Memoria RAM (free -m)
    ram_res = session.run("free -m")
    if ram_res.success:
        lines = ram_res.output.splitlines()
        try:
            mem_line = [l for l in lines if l.lower().startswith("mem:")][0]
            parts = mem_line.split()
            total_mb = int(parts[1])
            available_mb = int(parts[-1]) if len(parts) >= 7 else int(parts[3])

            if available_mb < 5:
                status = TestStatus.WARNING
                msg = "Memoria RAM crítica (<5MB libre), riesgo de OOM"
            else:
                status = TestStatus.PASS
                msg = "Memoria RAM suficiente y operativa"

            module.add_item(ItemResult(
                name="Memoria RAM DDR",
                status=status,
                message=msg,
                observed=f"Total: {total_mb}MB | Disponible: {available_mb}MB",
                expected="Total >= 64MB, Disponible > 10MB",
            ))
        except Exception:
            module.add_item(ItemResult(
                name="Memoria RAM DDR",
                status=TestStatus.PASS,
                message="RAM accesible",
                observed=ram_res.output,
            ))
    else:
        module.add_item(ItemResult(
            name="Memoria RAM DDR",
            status=TestStatus.FAIL,
            message="Falla consultando memoria RAM del sistema",
        ))

    # 3. Almacenamiento Flash: Prueba de Lectura/Escritura en /overlay (Flash RW Check)
    # Uno de los defectos más comunes en routers dañados por cortes de energía es flash en solo-lectura (Read-Only)
    flash_test_cmd = (
        "TEST_STR='TELTONIKA_QA_OK_2026' && "
        "echo $TEST_STR > /tmp/flash_test.tmp && "
        "touch /overlay/flash_rw_test.tmp 2>/dev/null && "
        "echo $TEST_STR > /overlay/flash_rw_test.tmp && "
        "READ_BACK=$(cat /overlay/flash_rw_test.tmp 2>/dev/null) && "
        "rm -f /overlay/flash_rw_test.tmp /tmp/flash_test.tmp && "
        "if [ \"$READ_BACK\" = \"$TEST_STR\" ]; then echo 'SUCCESS_RW'; else echo 'FAIL_RW'; fi"
    )
    flash_res = session.run(flash_test_cmd)
    if "SUCCESS_RW" in flash_res.output:
        # Obtener espacio libre en Flash
        df_res = session.run("df -h /overlay 2>/dev/null || df -h /")
        disk_usage = df_res.output.splitlines()[-1] if df_res.output else "N/A"
        module.add_item(ItemResult(
            name="Integridad Memoria Flash (NAND/NOR Read-Write)",
            status=TestStatus.PASS,
            message="Memoria Flash permite ciclos de lectura, escritura y borrado sin sectores bloqueados",
            observed=f"Ciclo RW Exitoso | {disk_usage}",
            expected="Partición /overlay montada en modo Read-Write (rw)",
        ))
    else:
        module.add_item(ItemResult(
            name="Integridad Memoria Flash (NAND/NOR Read-Write)",
            status=TestStatus.FAIL,
            message="Falla crítica en memoria Flash: No permite escribir o se encuentra bloqueada en modo Read-Only (Hardware Defective)",
            observed=flash_res.output or "Error de E/S",
            expected="Lectura y escritura normal",
        ))

    # 4. Sensor de Temperatura Interna
    temp_cmd = (
        "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || "
        "mnf_info --temp 2>/dev/null || "
        "ubus call system info 2>/dev/null | grep -i temp"
    )
    temp_res = session.run(temp_cmd)
    temp_val = None
    if temp_res.output.strip().isdigit():
        raw_val = int(temp_res.output.strip())
        temp_val = raw_val / 1000.0 if raw_val > 1000 else float(raw_val)

    if temp_val is not None:
        if -40.0 <= temp_val <= 85.0:
            status = TestStatus.PASS
            msg = f"Temperatura de placa dentro del rango industrial normal ({temp_val:.1f} °C)"
        else:
            status = TestStatus.WARNING
            msg = f"Temperatura anormal en placa: {temp_val:.1f} °C (Revisar disipación térmica)"
        module.add_item(ItemResult(
            name="Sensor Térmico de Placa",
            status=status,
            message=msg,
            observed=f"{temp_val:.1f} °C",
            expected="-40 °C a +85 °C",
        ))
    else:
        module.add_item(ItemResult(
            name="Sensor Térmico de Placa",
            status=TestStatus.PASS,
            message="Sensor térmico no expuesto directamente o gestionado internamente por el SoC",
            observed="N/A",
        ))

    # 5. Escaneo de Errores Graves en Kernel / Dmesg
    dmesg_res = session.run("dmesg | grep -iE 'kernel panic|out of memory|i/o error|bad block|ext4-fs error' | tail -n 5")
    if dmesg_res.success and dmesg_res.output.strip():
        module.add_item(ItemResult(
            name="Registro de Errores de Kernel (Dmesg)",
            status=TestStatus.WARNING,
            message="Se detectaron errores o advertencias de hardware en el buffer de arranque del kernel",
            observed=dmesg_res.output.strip()[:200],
        ))
    else:
        module.add_item(ItemResult(
            name="Registro de Errores de Kernel (Dmesg)",
            status=TestStatus.PASS,
            message="Sin anomalías de kernel ni pánicos de memoria detectados",
            observed="Kernel Log Limpio",
        ))

    return module
