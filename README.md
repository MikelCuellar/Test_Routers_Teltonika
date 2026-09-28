# Test_Routers_Teltonika 📡

> **Laboratorio de Integración, Diagnóstico Automatizado & RMA para Routers y Gateways Industriales Teltonika Networks (RutOS)**  
> **GrupoGeo & Antigravity** | Septiembre 2026

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-10%2F10%20passing-brightgreen.svg)]()
[![Teltonika RutOS](https://img.shields.io/badge/platform-RutOS%20%2F%20OpenWrt-orange.svg)](https://wiki.teltonika-networks.com)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

---

## 🎯 1. Propósito y Alcance del Proyecto

**Test_Routers_Teltonika** es la plataforma técnica desarrollada para:
1. **Departamento de Garantías & Servicio Técnico (RMA):** Banco de pruebas automatizado que evalúa exhaustivamente el 100% de los subsistemas de hardware de routers y gateways retornados por clientes o antes de su despliegue en terreno, emitiendo un informe técnico y un veredicto legal/operativo automático.
2. **I+D y Pruebas de Integración GrupoGeo:** Validación de capacidades de conectividad crítica, telemetría industrial (Modbus/MQTT), rastreo geodésico (GNSS/AVL) y telecontrol para plataformas como [[Geotask]] y Tótems inteligentes.

---

## 🧭 2. Modelos Soportados y Catálogo de Capacidades

El motor de diagnóstico resuelve automáticamente la matriz de hardware del equipo bajo prueba según su modelo de placa EEPROM:

| Familia | Modelos Verificados | Interfaces y Subsistemas Detectados |
|---|---|---|
| **RUT Compact** | `RUT240`, `RUT241`, `RUT200` | 4G LTE Cat 4, 1x SIM, 2x Ethernet (WAN/LAN), Wi-Fi 2.4 GHz, E/S Digital |
| **RUT Industrial Avanzado** | `RUT950`, `RUT951`, `RUT955`, `RUT956` | Dual SIM Failover, 4x Ethernet, GPS/GNSS, Wi-Fi, RS232, RS485, Relé mecánico, Entradas/Salidas optoacopladas |
| **RUTX Alta Velocidad** | `RUTX09`, `RUTX11`, `RUTX12`, `RUTX50` | LTE Cat 6/12 / 5G Sub-6, Gigabit Ethernet (4x), Wi-Fi AC Dual Band, GNSS, BLE |
| **TRB Gateways** | `TRB140`, `TRB141`, `TRB142`, `TRB145`, `TRB245` | Módems ultra-compactos, Ethernet único, puertos serie RS232/RS485 aislados, GPIO industrial |

---

## 🔬 3. Módulos del Motor de Diagnóstico RMA

El motor ejecuta 7 módulos de prueba independientes que analizan las funciones físicas y lógicas del router:

```
scripts/rma_engine/
├── device_session.py        # Sesión interactiva SSH/CLI con fallback inteligente (root / admin)
├── model_capabilities.py    # Base de conocimiento de especificaciones de hardware por modelo
├── models.py                # Dataclasses de resultados, métricas RF y veredictos
├── orchestrator.py          # Coordinador secuencial y adaptador de capacidades
├── report_generator.py      # Generador multi-formato: HTML interactivo, JSON y Markdown
└── tests/
    ├── test_identification.py  # Placa base, EEPROM (mnf_info), Serial, MAC, Batch y HW Revision
    ├── test_system.py          # SoC CPU, RAM, ciclo Flash R/W (/overlay), térmica y kernel panics
    ├── test_cellular.py        # Módem AT, IMEI, lector SIM 1, multiplexor SIM 2 y métricas RF (RSSI/RSRP)
    ├── test_ethernet.py        # Switch PHY, detección de carrier físico, velocidad, dúplex y CRC errors
    ├── test_wifi.py            # Radio WLAN, potencia TX dBm y escaneo espectral de balizas RF
    ├── test_gps.py             # Demonio GNSS (gpsctl), satélites visibles y trama NMEA / fix
    └── test_io_serial.py       # Optoacopladores DIN, DOUT, conmutación de Relé y bucles UART RS232/485
```

---

## 📋 4. Veredictos del Departamento de Garantías

Al finalizar el escaneo, el sistema califica el estado del equipo emitiendo uno de los siguientes veredictos formales:

- 🟢 **`APPROVED_PERFECT` (Aprobado):** El dispositivo no presenta fallas. 100% operativo. Listo para reinstalación o devolución a stock.
- 🔴 **`DEFECTIVE_WARRANTY_VALID` (Defectuoso de Fábrica / Aplica Garantía):** Se detectó falla en componente interno (e.g. Flash ROM bloqueada en solo lectura, falla interna de módem celular, zócalo de SIM inoperativo) sin evidencia de abuso eléctrico externo.
- ⚠️ **`PHYSICAL_TAMPERING_DETECTED` (Manipulación No Autorizada):** Número de serie en EEPROM no coincide con carcasa o registros de fabricación, o software alterado de forma irreversible.
- ⚡ **`REJECTED_CUSTOMER_DAMAGE` (Rechazado por Daño Externo):** Puertos Ethernet quemados por sobretensión, puertos seriales con transceptor reventado o inversión de polaridad.

---

## 📂 5. Estructura del Proyecto

```
Test_Routers_Teltonika/
├── .env.example                     # Plantilla de credenciales y variables de entorno
├── .gitignore                       # Filtro seguro de archivos locales, venv y secretos
├── README.md                        # Este documento maestro
├── requirements.txt                 # Dependencias Python
├── docs/                            # Documentación técnica de RutOS
│   ├── 01_arquitectura_rutos.md     # Estructura del SO, UCI, UBUS, JSON-RPC
│   ├── 02_protocolos_telemetria.md  # Modbus TCP/RTU y MQTT Data to Server
│   ├── 03_gps_avl_tracking.md       # AVL, telemetría vehicular y geofencing
│   └── 04_seguridad_y_redes.md      # VPNs (WireGuard/IPsec), Firewall y RMS
├── reports/                         # Informes generados por la suite RMA
│   ├── RMA_RMA-2026-001_1102938475.html
│   └── RMA_RMA-2026-002_9928172635.html
├── scripts/
│   ├── run_rma_test.py              # CLI principal de pruebas para ingenieros
│   ├── teltonika_api_client.py      # Cliente REST / JSON-RPC de RutOS
│   ├── ping_and_discovery.py        # Descubrimiento de routers en la red local
│   ├── modbus_tester.py             # Sonda y lectura de registros Modbus
│   ├── mqtt_telemetry_listener.py   # Servidor listener para Data to Server
│   └── rma_engine/                  # Motor central de diagnóstico
└── tests/                           # Suite de verificación unitaria (Pytest)
    ├── test_client.py
    └── test_rma_engine.py
```

---

## ⚡ 6. Puesta en Marcha y Uso

### 6.1 Instalación del Entorno
```powershell
# Clonar repositorio
git clone https://github.com/MikelCuellar/Test_Routers_Teltonika.git
cd Test_Routers_Teltonika

# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 6.2 Ejecutar Suite de Diagnóstico RMA en un Router
Conecte el router mediante cable Ethernet a la PC (IP de fábrica: `192.168.1.1`):

```powershell
# Diagnóstico estándar con generación de reportes HTML/JSON/Markdown:
python scripts/run_rma_test.py --host 192.168.1.1 --user root --password admin01 --ticket RMA-2026-001 --inspector "Ing. Laboratorio"

# Diagnóstico con sincronización directa hacia Supramemory:
python scripts/run_rma_test.py --host 192.168.1.1 --password admin01 --ticket RMA-2026-001 --upload-supramemory
```

### 6.3 Ejecución de Pruebas Unitarias
```powershell
pytest tests/ -v
```

---

## 📊 7. Visualización de Reportes

Los reportes HTML generados en la carpeta `reports/` son interactivos, autónomos (no requieren conexión a internet) y cuentan con estilos `@media print` para exportación directa a PDF desde el navegador web.

---

## 🔗 8. Integración con el Ecosistema GrupoGeo
- **[[Supramemory]]** — Registro en la bóveda de conocimiento y sincronización de diagnósticos (`https://supramemory.grupogeo.cl`).
- **[[Credenciales-y-Accesos-Maestros]]** — Parámetros de conexión y llaves API del grupo.
- **[[Geotask]]** — Plataforma de campo que utiliza estos routers para telemetría vehicular e IoT.

