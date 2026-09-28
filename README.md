# Test_Routers_Teltonika 📡

> **Proyecto de Investigación & Laboratorio de Integración de Routers y Gateways Industriales Teltonika (RutOS)**  
> **GrupoGeo & Antigravity** | Septiembre 2026

---

## 🎯 1. Propósito y Alcance de la Investigación

El proyecto **Test_Routers_Teltonika** es un entorno de pruebas, ingeniería inversa, integración y validación técnica para routers y gateways celulares industriales **Teltonika Networks** (series RUT, TRB y RUTX).

Su objetivo principal es investigar y desarrollar las capacidades de conectividad, telemetría y control remoto requeridas por los productos de **GrupoGeo** (como [[Geotask]] para cuadrillas y maquinaria en terreno, y sistemas IoT/Totem en locaciones remotas):

1. **Conectividad Crítica en Terreno:** Failover celular Multi-SIM, redundancia WAN/4G/5G y túneles VPN punto a punto (WireGuard, OpenVPN, IPsec).
2. **Telemetría y Adquisición de Datos:** Integración con protocolos industriales **Modbus TCP/RTU**, **MQTT**, **SNMP** y el servicio nativo **Data to Server** de RutOS.
3. **Geolocalización & AVL:** Extracción de coordenadas GPS/GNSS en tiempo real, cálculo de velocidad, altitud y eventos de geovallado.
4. **Control de E/S & Sensores:** Monitoreo y activación remota de entradas y salidas digitales/analógicas (relés, encendido de motores, sensores de combustible, temperatura).
5. **Automatización y Gestión de Flota:** Integración con la API REST y JSON-RPC de RutOS, gestión remota mediante **Teltonika RMS** y scripting local en CLI (UCI/UBUS/Shell).

---

## 🧭 2. Modelos y Dispositivos de Interés

| Familia | Modelos Típicos | Tecnologías Clave | Casos de Uso en GrupoGeo |
|---|---|---|---|
| **RUT Compact** | `RUT240`, `RUT241`, `RUT200` | 4G LTE Cat 4, Wi-Fi 802.11n, 2x Ethernet, Digital I/O | Conectividad de tótems, kioscos autónomos y enlaces básicos. |
| **RUT Industrial Avanzado** | `RUT950`, `RUT951`, `RUT955`, `RUT956` | Dual SIM, 4x Ethernet, GPS/GNSS, RS232, RS485, I/O múltiple | Monitoreo vehicular pesado, maquinaria [[Geotask]], telemetría Modbus. |
| **RUTX Alta Velocidad** | `RUTX09`, `RUTX11`, `RUTX12`, `RUTX50` | Cat 6 / Cat 12 / 5G, Gigabit Ethernet, Wi-Fi AC Dual Band, BLE | Nodos centrales de faena, streaming de video y alta concurrencia. |
| **TRB Gateways** | `TRB140`, `TRB141`, `TRB142`, `TRB145`, `TRB245` | Ultra-compactos, bajo consumo, Ethernet / RS232 / RS485 / GPIO | Sensores remotos, telemetría de medidores eléctricos e hídricos. |

---

## 📂 3. Estructura del Repositorio

```
Test_Routers_Teltonika/
├── README.md                      # Documento maestro del laboratorio
├── requirements.txt               # Dependencias Python para herramientas de test
├── .env.example                   # Variables de entorno y credenciales de laboratorio
├── docs/                          # Guías técnicas y especificaciones
│   ├── 01_arquitectura_rutos.md   # Sistema operativo RutOS (OpenWrt, UCI, UBUS, APIs)
│   ├── 02_protocolos_telemetria.md# Modbus TCP/RTU, MQTT, Data to Server
│   ├── 03_gps_avl_tracking.md     # GNSS, NMEA, tramas AVL y geocercas
│   └── 04_seguridad_y_redes.md    # WireGuard, OpenVPN, RMS, Failover y Firewall
├── scripts/                       # Scripts y herramientas de prueba en Python
│   ├── teltonika_api_client.py    # Cliente Python para RutOS REST API / JSON-RPC
│   ├── mqtt_telemetry_listener.py # Receptor MQTT para eventos y telemetría
│   ├── modbus_tester.py           # Consulta de registros Modbus en routers RUT
│   └── ping_and_discovery.py      # Escáner de red para descubrimiento de dispositivos
├── configs/                       # Plantillas y backups de configuración
│   └── uci_templates/             # Ejemplos de configuración UCI
└── tests/                         # Pruebas automatizadas de los módulos
    └── test_client.py
```

---

## ⚡ 4. Puesta en Marcha Rápida

### 4.1 Requisitos Previos
- Python 3.10+
- Router o Gateway Teltonika conectado en la red local (IP por defecto usualmente `192.168.1.1`).
- Acceso con credenciales de administrador (usuario `admin`).

### 4.2 Instalación
```powershell
cd C:\Users\mik10\Desarollo\Test_Routers_Teltonika
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.3 Configuración de Variables
Copiar `.env.example` a `.env` y configurar la IP y clave de acceso del router de prueba:
```powershell
cp .env.example .env
```

### 4.4 Ejecución de Pruebas
1. **Descubrir routers en la subred:**
   ```powershell
   python scripts/ping_and_discovery.py --subnet 192.168.1.0/24
   ```
2. **Consultar estado y telemetría vía API:**
   ```powershell
   python scripts/teltonika_api_client.py --host 192.168.1.1 --user admin --pass TuPassword
   ```
3. **Escuchar telemetría MQTT (Data to Server):**
   ```powershell
   python scripts/mqtt_telemetry_listener.py --port 1883 --topic "teltonika/#"
   ```

---

## 🔗 5. Enlaces y Referencias de Conocimiento
- [[Supramemory]] — Memoria viva del ecosistema GrupoGeo.
- [[Credenciales-y-Accesos-Maestros]] — Parámetros de redes y servidores seguros.
- [[Geotask]] — Plataforma de operaciones en terreno candidata para integración.
- [Teltonika Networks Wiki Oficial](https://wiki.teltonika-networks.com)
