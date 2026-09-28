"""Script principal y CLI para ejecutar el diagnóstico automatizado RMA en routers Teltonika."""
import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

# Configurar codificación UTF-8 para consola Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rma_engine.device_session import DeviceSession
from rma_engine.models import RMAVerdict, TestStatus
from rma_engine.orchestrator import RMAOrchestrator
from rma_engine.report_generator import save_reports


def print_banner():
    banner = """
======================================================================
  📡 SUITE DE DIAGNÓSTICO Y CERTIFICACIÓN RMA — TELTONIKA NETWORKS
  Departamento de Garantías y Laboratorio de Hardware | GrupoGeo
======================================================================
"""
    print(banner)


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Ejecutor de Diagnóstico RMA para Routers Teltonika")
    parser.add_argument("--host", default=os.getenv("TELTONIKA_HOST", "192.168.1.1"), help="IP del router bajo prueba")
    parser.add_argument("--port", type=int, default=22, help="Puerto SSH (default 22)")
    parser.add_argument("--user", default=os.getenv("TELTONIKA_USERNAME", "root"), help="Usuario SSH (root o admin)")
    parser.add_argument("--password", default=os.getenv("TELTONIKA_PASSWORD", "admin01"), help="Contraseña del router")
    parser.add_argument("--ticket", default=f"RMA-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}", help="Número de Ticket o Caso RMA")
    parser.add_argument("--engineer", default="Ingeniero de Garantías", help="Nombre del técnico/ingeniero evaluador")
    parser.add_argument("--client", default="Cliente / Contratista", help="Nombre de la empresa o cliente")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent.parent / "reports"), help="Directorio para guardar reportes")
    parser.add_argument("--upload-supramemory", action="store_true", help="Archivar automáticamente el reporte en Supramemory")

    args = parser.parse_args()

    print(f"🎯 Conectando a {args.host}:{args.port} como '{args.user}'...")
    session = DeviceSession(
        host=args.host,
        port=args.port,
        username=args.user,
        password=args.password,
    )

    if not session.connect():
        print(f"\n❌ ERROR: No fue posible establecer comunicación con el router en {args.host}:{args.port}.")
        print("   Verifique que:")
        print("   1. El router esté encendido y conectado por cable Ethernet al puesto de prueba.")
        print("   2. Su PC tenga una IP en el mismo rango (ej: 192.168.1.150 / 255.255.255.0).")
        print("   3. Las credenciales de acceso (usuario y contraseña) sean correctas.")
        sys.exit(10)

    print("🔌 Conexión establecida. Iniciando matriz de pruebas automáticas...\n")

    def progress_callback(step_name: str, step_num: int, total_steps: int):
        print(f"  [{step_num}/{total_steps}] ⏳ Ejecutando {step_name}...")

    orchestrator = RMAOrchestrator(
        session=session,
        ticket_id=args.ticket,
        engineer_name=args.engineer,
        client_name=args.client,
    )

    report = orchestrator.execute(progress_callback=progress_callback)
    session.close()

    # Imprimir resumen en consola
    stats = report.get_stats()
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DEL DIAGNÓSTICO DE HARDWARE:")
    print("-" * 70)
    print(f"  • Dispositivo : {report.device.model_name} (Código: {report.device.product_code})")
    print(f"  • N° de Serie : {report.device.serial_number}")
    print(f"  • MAC LAN     : {report.device.mac_address}")
    print(f"  • IMEI Módem  : {report.device.modem_imei}")
    print(f"  • HW Rev / Lote: Rev {report.device.hardware_revision} | Lote {report.device.batch_number}")
    print(f"  • Firmware    : {report.device.firmware_version}")
    print("-" * 70)
    print(f"  • Pruebas Aprobadas (PASS)   : {stats['pass']}")
    print(f"  • Fallas Detectadas (FAIL)   : {stats['fail']}")
    print(f"  • Advertencias (WARNING)     : {stats['warning']}")
    print(f"  • No Equipadas (N/A)         : {stats['not_equipped']}")
    print("=" * 70)

    if report.verdict == RMAVerdict.APPROVED:
        print(f"\n✅ DICTAMEN FINAL: {report.verdict.value}")
        print("   -> El router no presenta fallas de hardware. Apto para entrega / reingreso a inventario.")
    elif report.verdict == RMAVerdict.DEFECTIVE:
        print(f"\n❌ DICTAMEN FINAL: {report.verdict.value}")
        print("   -> Componentes averiados detectados:")
        for comp in report.defective_components:
            print(f"      • {comp}")
        print("   -> Procedimiento: Generar solicitud de cambio en garantía con el fabricante (Teltonika RMA).")
    else:
        print(f"\n⚠️ DICTAMEN FINAL: {report.verdict.value}")
        for obs in report.observations:
            print(f"      • {obs}")

    # Guardar reportes en disco
    out_dir = Path(args.output_dir)
    saved = save_reports(report, out_dir)
    print("\n📄 Informes técnicos generados:")
    print(f"   • HTML Interactivo : {saved['html']}")
    print(f"   • JSON Estructurado: {saved['json']}")
    print(f"   • Markdown         : {saved['md']}")

    # Subida a Supramemory si se solicitó
    if args.upload_supramemory:
        try:
            print("\n🧠 Archivando certificado en Supramemory...")
            cli_path = Path(__file__).resolve().parent.parent.parent / ".agents" / "skills" / "supramemory" / "supramemory_cli.py"
            if cli_path.exists():
                note_id = f"rma-{report.ticket_id.lower()}-{report.device.serial_number.lower()}"
                title = f"Certificado RMA: {report.device.model_name} (S/N: {report.device.serial_number}) — {report.verdict.name}"
                md_content = Path(saved['md']).read_text(encoding="utf-8")
                subprocess.run([
                    sys.executable,
                    str(cli_path),
                    "create",
                    "--title", title,
                    "--id", note_id,
                    "--tags", "rma,garantia,teltonika,hardware,diagnostico",
                    "--content", md_content,
                ], check=False)
                print("   ✅ Certificado archivado en el grafo de Supramemory.")
        except Exception as e:
            print(f"   ⚠️ No se pudo subir a Supramemory: {e}")

    print("\n🏁 Proceso de diagnóstico finalizado con éxito.\n")

    # Código de retorno del script
    if report.verdict == RMAVerdict.APPROVED:
        sys.exit(0)
    elif report.verdict == RMAVerdict.DEFECTIVE:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
