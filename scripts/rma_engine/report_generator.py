"""Generador de Informes Técnicos de Certificación RMA (HTML interactivo, JSON y Markdown)."""
import json
from pathlib import Path
from typing import Optional
from .models import DiagnosticReport, RMAVerdict, TestStatus


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Certificado de Diagnóstico RMA — {{ report.device.model_name }} [{{ report.device.serial_number }}]</title>
  <style>
    :root {
      --bg: #0f1117;
      --card-bg: #181b24;
      --card-border: #292d3d;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --accent: #00d26a;
      --danger: #f85149;
      --warning: #e3b341;
      --info: #58a6ff;
      --na: #6e7681;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 30px 20px;
    }
    .container { max-width: 1000px; margin: 0 auto; }
    
    /* Header */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid var(--card-border);
      padding-bottom: 20px;
      margin-bottom: 25px;
    }
    .brand h1 { font-size: 24px; font-weight: 700; color: #fff; }
    .brand p { font-size: 13px; color: var(--text-muted); }
    .ticket-badge {
      background: #21262d;
      border: 1px solid #30363d;
      padding: 8px 16px;
      border-radius: 8px;
      text-align: right;
    }
    .ticket-badge .ticket-num { font-size: 16px; font-weight: 700; color: var(--info); font-family: monospace; }
    .ticket-badge .ticket-date { font-size: 12px; color: var(--text-muted); }

    /* Verdict Banner */
    .verdict-banner {
      padding: 20px;
      border-radius: 12px;
      margin-bottom: 25px;
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .verdict-banner.approved {
      background: rgba(0, 210, 106, 0.12);
      border: 1px solid var(--accent);
    }
    .verdict-banner.defective {
      background: rgba(248, 81, 73, 0.12);
      border: 1px solid var(--danger);
    }
    .verdict-banner.observation {
      background: rgba(227, 179, 65, 0.12);
      border: 1px solid var(--warning);
    }
    .verdict-icon { font-size: 40px; }
    .verdict-title { font-size: 18px; font-weight: 700; }
    .verdict-desc { font-size: 14px; color: var(--text-muted); }

    /* Defective components box */
    .defective-box {
      background: rgba(248, 81, 73, 0.1);
      border-left: 4px solid var(--danger);
      padding: 15px;
      border-radius: 4px;
      margin-bottom: 25px;
    }
    .defective-box h3 { font-size: 15px; color: var(--danger); margin-bottom: 8px; }
    .defective-box ul { padding-left: 20px; font-size: 13.5px; }

    /* Metadata Grid */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 15px;
      margin-bottom: 30px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 15px;
    }
    .card-label { font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; }
    .card-value { font-size: 15px; font-weight: 600; color: #fff; margin-top: 4px; word-break: break-all; }

    /* Stats Bar */
    .stats-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 30px;
    }
    .stat-pill {
      flex: 1;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 12px;
      text-align: center;
    }
    .stat-num { font-size: 22px; font-weight: 700; }
    .stat-num.pass { color: var(--accent); }
    .stat-num.fail { color: var(--danger); }
    .stat-num.warn { color: var(--warning); }
    .stat-num.na { color: var(--na); }
    .stat-lbl { font-size: 11px; color: var(--text-muted); text-transform: uppercase; margin-top: 2px; }

    /* Test Modules */
    .module-section { margin-bottom: 25px; }
    .module-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #1c212d;
      padding: 12px 18px;
      border-radius: 8px 8px 0 0;
      border: 1px solid var(--card-border);
      border-bottom: none;
    }
    .module-title { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 10px; }
    .test-table {
      width: 100%;
      border-collapse: collapse;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 0 0 8px 8px;
      overflow: hidden;
    }
    .test-table th, .test-table td {
      padding: 10px 15px;
      font-size: 13px;
      text-align: left;
      border-bottom: 1px solid #252936;
    }
    .test-table th { background: #161922; color: var(--text-muted); font-weight: 600; }
    .test-table tr:last-child td { border-bottom: none; }
    
    /* Badges */
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      text-align: center;
      min-width: 60px;
    }
    .badge.pass { background: rgba(0, 210, 106, 0.15); color: var(--accent); border: 1px solid var(--accent); }
    .badge.fail { background: rgba(248, 81, 73, 0.15); color: var(--danger); border: 1px solid var(--danger); }
    .badge.warning { background: rgba(227, 179, 65, 0.15); color: var(--warning); border: 1px solid var(--warning); }
    .badge.not_equipped { background: rgba(110, 118, 129, 0.15); color: var(--na); border: 1px solid var(--na); }
    
    /* Footer Sign-off */
    .footer-sign {
      display: flex;
      justify-content: space-between;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--card-border);
      font-size: 13px;
      color: var(--text-muted);
    }
    @media print {
      body { background: #fff; color: #000; padding: 0; }
      .card, .test-table, .stat-pill, .module-header { background: #fff !important; color: #000 !important; border-color: #ddd !important; }
      .header, .footer-sign { border-color: #ddd !important; }
      .card-value, .brand h1, .module-title { color: #000 !important; }
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <div class="brand">
        <h1>Certificado de Diagnóstico & Certificación RMA</h1>
        <p>Departamento de Garantías y Laboratorio de Hardware — GrupoGeo</p>
      </div>
      <div class="ticket-badge">
        <div class="ticket-num">RMA: {{ report.ticket_id }}</div>
        <div class="ticket-date">{{ report.timestamp }}</div>
      </div>
    </div>

    <!-- Dictamen Principal -->
    {% if report.verdict.name == 'APPROVED' %}
    <div class="verdict-banner approved">
      <div class="verdict-icon">✅</div>
      <div>
        <div class="verdict-title" style="color: var(--accent);">{{ report.verdict.value }}</div>
        <div class="verdict-desc">El equipo superó satisfactoriamente todas las pruebas de hardware, RF, enlaces y memoria. Apto para entrega / reingreso a stock.</div>
      </div>
    </div>
    {% elif report.verdict.name == 'DEFECTIVE' %}
    <div class="verdict-banner defective">
      <div class="verdict-icon">❌</div>
      <div>
        <div class="verdict-title" style="color: var(--danger);">{{ report.verdict.value }}</div>
        <div class="verdict-desc">Se identificaron fallas físicas determinantes en uno o más subsistemas de hardware. Procede trámite de garantía con fabricante (RMA).</div>
      </div>
    </div>
    {% else %}
    <div class="verdict-banner observation">
      <div class="verdict-icon">⚠️</div>
      <div>
        <div class="verdict-title" style="color: var(--warning);">{{ report.verdict.value }}</div>
        <div class="verdict-desc">Fallas no determinantes o advertencias de configuración/señal detectadas. Requiere revisión técnica o re-flasheo de firmware.</div>
      </div>
    </div>
    {% endif %}

    <!-- Componentes Defectuosos -->
    {% if report.defective_components %}
    <div class="defective-box">
      <h3>⚠️ Componentes con Falla de Hardware Confirmada:</h3>
      <ul>
        {% for comp in report.defective_components %}
        <li><strong>{{ comp }}</strong></li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    <!-- Resumen de Métricas -->
    <div class="stats-bar">
      <div class="stat-pill">
        <div class="stat-num pass">{{ report.get_stats().pass }}</div>
        <div class="stat-lbl">Pruebas Aprobadas</div>
      </div>
      <div class="stat-pill">
        <div class="stat-num fail">{{ report.get_stats().fail }}</div>
        <div class="stat-lbl">Fallas Detectadas</div>
      </div>
      <div class="stat-pill">
        <div class="stat-num warn">{{ report.get_stats().warning }}</div>
        <div class="stat-lbl">Advertencias</div>
      </div>
      <div class="stat-pill">
        <div class="stat-num na">{{ report.get_stats().not_equipped }}</div>
        <div class="stat-lbl">No Equipadas</div>
      </div>
    </div>

    <!-- Metadatos de Dispositivo -->
    <div class="grid">
      <div class="card">
        <div class="card-label">Modelo & Código</div>
        <div class="card-value">{{ report.device.model_name }} ({{ report.device.product_code }})</div>
      </div>
      <div class="card">
        <div class="card-label">Número de Serie (S/N)</div>
        <div class="card-value" style="font-family: monospace;">{{ report.device.serial_number }}</div>
      </div>
      <div class="card">
        <div class="card-label">Dirección MAC LAN</div>
        <div class="card-value" style="font-family: monospace;">{{ report.device.mac_address }}</div>
      </div>
      <div class="card">
        <div class="card-label">IMEI Celular</div>
        <div class="card-value" style="font-family: monospace;">{{ report.device.modem_imei }}</div>
      </div>
      <div class="card">
        <div class="card-label">HW Revision & Batch</div>
        <div class="card-value">Rev: {{ report.device.hardware_revision }} | Lote: {{ report.device.batch_number }}</div>
      </div>
      <div class="card">
        <div class="card-label">Firmware RutOS</div>
        <div class="card-value">{{ report.device.firmware_version }}</div>
      </div>
    </div>

    <!-- Detalle de Módulos de Prueba -->
    {% for mod in report.modules %}
    <div class="module-section">
      <div class="module-header">
        <div class="module-title">
          <span>{{ mod.module_name }}</span>
        </div>
        <span class="badge {{ mod.status.value.lower() }}">{{ mod.status.value }}</span>
      </div>
      <table class="test-table">
        <thead>
          <tr>
            <th style="width: 25%;">Prueba</th>
            <th style="width: 15%;">Estado</th>
            <th style="width: 30%;">Valor Observado</th>
            <th style="width: 30%;">Diagnóstico / Criterio</th>
          </tr>
        </thead>
        <tbody>
          {% for item in mod.items %}
          <tr>
            <td><strong>{{ item.name }}</strong></td>
            <td><span class="badge {{ item.status.value.lower() }}">{{ item.status.value }}</span></td>
            <td style="color: #cad1d9;">{{ item.observed or 'N/A' }}</td>
            <td style="color: var(--text-muted);">{{ item.message }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endfor %}

    <!-- Footer Sign-off -->
    <div class="footer-sign">
      <div>
        <strong>Ingeniero Responsable:</strong> {{ report.engineer_name }}<br>
        <strong>Cliente / Solicitante:</strong> {{ report.client_name }}
      </div>
      <div style="text-align: right;">
        <strong>Certificación Técnica GrupoGeo</strong><br>
        Documento generado automáticamente por Suite RMA Teltonika v1.0
      </div>
    </div>
  </div>
</body>
</html>
"""


def render_html_report(report: DiagnosticReport) -> str:
    """Renderiza el reporte de diagnóstico a HTML mediante Jinja2."""
    try:
        from jinja2 import Template
        tmpl = Template(HTML_TEMPLATE)
        return tmpl.render(report=report)
    except Exception as e:
        # Fallback simple sin jinja2 si ocurriera algún imprevisto
        return f"<html><body><h1>Reporte RMA: {report.ticket_id}</h1><p>Dictamen: {report.verdict.value}</p></body></html>"


def render_markdown_report(report: DiagnosticReport) -> str:
    """Renderiza una versión Markdown concisa para terminal o Supramemory."""
    stats = report.get_stats()
    lines = [
        f"# Informe de Certificación RMA — {report.device.model_name} (S/N: {report.device.serial_number})",
        "",
        f"- **Ticket RMA:** `{report.ticket_id}`",
        f"- **Fecha:** {report.timestamp}",
        f"- **Ingeniero:** {report.engineer_name}",
        f"- **Dictamen:** **{report.verdict.value}**",
        "",
        "## Resumen de Pruebas",
        f"- **Aprobadas:** {stats['pass']}",
        f"- **Fallas:** {stats['fail']}",
        f"- **Advertencias:** {stats['warning']}",
        f"- **No Equipadas:** {stats['not_equipped']}",
        "",
    ]

    if report.defective_components:
        lines.append("### ⚠️ Componentes Defectuosos:")
        for c in report.defective_components:
            lines.append(f"- ❌ {c}")
        lines.append("")

    lines.append("## Detalle por Módulos")
    for mod in report.modules:
        lines.append(f"### {mod.module_name} `[{mod.status.value}]`")
        for item in mod.items:
            icon = "✅" if item.status == TestStatus.PASS else ("❌" if item.status == TestStatus.FAIL else ("⚠️" if item.status == TestStatus.WARNING else "⚪"))
            obs = f" *(Observado: {item.observed})*" if item.observed else ""
            lines.append(f"- {icon} **{item.name}**: {item.message}{obs}")
        lines.append("")

    return "\n".join(lines)


def save_reports(report: DiagnosticReport, output_dir: Path) -> dict:
    """Guarda el reporte en disco en formatos HTML, JSON y Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_sn = report.device.serial_number if report.device.serial_number != "N/A" else "UNKNOWN"
    base_name = f"RMA_{report.ticket_id}_{clean_sn}"

    html_path = output_dir / f"{base_name}.html"
    json_path = output_dir / f"{base_name}.json"
    md_path = output_dir / f"{base_name}.md"

    # Guardar HTML
    html_content = render_html_report(report)
    html_path.write_text(html_content, encoding="utf-8")

    # Guardar JSON
    json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    # Guardar Markdown
    md_path.write_text(render_markdown_report(report), encoding="utf-8")

    return {
        "html": str(html_path),
        "json": str(json_path),
        "md": str(md_path),
    }
