# 01 — Arquitectura RutOS: Sistema Operativo, CLI y APIs

## 1. ¿Qué es RutOS?
**RutOS** es el sistema operativo unificado que impulsa todos los routers, gateways y switches de **Teltonika Networks**. Está construido sobre el kernel de Linux y la distribución de código abierto **OpenWrt**, pero con una capa empresarial propietaria optimizada para:
- Estabilidad industrial continua (Watchdog de hardware y software).
- Conectividad celular multi-tecnología (2G/3G/4G/5G).
- Redundancia avanzada y conmutación por error (Failover / Dual-SIM / VRRP).
- Interfaces web modernas y APIs de automatización.

---

## 2. Subsistemas Centrales de RutOS

### 2.1 UCI (Unified Configuration Interface)
UCI es el sistema centralizado de gestión de configuración de OpenWrt/RutOS.
Todos los servicios se configuran a través de archivos de texto plano ubicados en `/etc/config/`:
- `/etc/config/network` : Interfaces LAN, WAN, WWAN, VLANs.
- `/etc/config/wireless`: Radios Wi-Fi y SSIDs.
- `/etc/config/firewall`: Reglas de filtrado iptables/nftables, NAT y reenvío de puertos.
- `/etc/config/simcard` : Configuración de SIM1/SIM2, APN, PIN y roaming.
- `/etc/config/modbus`  : Configuración de servicios Modbus Master/Slave.
- `/etc/config/datalogger` o `data_sender`: Reglas de Data to Server.

#### Comandos CLI esenciales de UCI:
```bash
# Leer configuración
uci show network
uci get network.lan.ipaddr

# Modificar configuración
uci set network.lan.ipaddr='192.168.10.1'

# Confirmar y aplicar cambios
uci commit network
/etc/init.d/network restart
```

### 2.2 UBUS (Micro Bus System)
UBUS es el bus de mensajes IPC (Inter-Process Communication) en espacio de usuario. Permite interactuar con los demonios internos del sistema en tiempo real.
```bash
# Listar objetos y métodos disponibles
ubus list
ubus -v list gsm.modem0

# Consultar información del módem celular (señal, IMSI, IMEI, operador)
ubus call gsm.modem0 get_signal_query
ubus call network.interface.mob1s1a1 status
```

---

## 3. Interfaces de Programación (APIs)

RutOS ofrece dos métodos principales de interacción programática:

### 3.1 REST API (RutOS v7+)
En versiones modernas (RutOS 7.0+), Teltonika incorporó una API REST nativa con autenticación mediante Token Bearer.
- **Base URL:** `https://<ROUTER_IP>/api/`
- **Autenticación:** Generación de token en `System > Administration > API` o mediante endpoint de login.
- **Headers:** `Authorization: Bearer <TOKEN>`

#### Endpoints Clave:
- `GET /api/system/info` : Versión de firmware, número de serie, modelo, uptime.
- `GET /api/modem/status`: Estado del módem celular, RSSI, RSRP, RSRQ, SINR, celda activa.
- `GET /api/gps/location`: Última posición GNSS conocida (latitud, longitud, altitud, satélites).
- `POST /api/io/output`  : Control de salidas digitales / relés.

### 3.2 JSON-RPC API (RutOS Legacy & v7)
Permite invocar métodos de UBUS directamente a través de HTTP POST mediante JSON-RPC 2.0.
- **Endpoint:** `https://<ROUTER_IP>/ubus`
- **Flujo de llamada:**
  1. `call("session", "login", {"username": "admin", "password": "..."})` -> Retorna `ubus_rpc_session`.
  2. `call("<object>", "<method>", { ... })` pasando la sesión.

---

## 4. Acceso por Consola y Scripting Local
- **SSH:** Acceso seguro por puerto 22 o puerto personalizado.
- **Package Manager (OPKG):** Permite instalar paquetes adicionales compilados para la arquitectura MIPS/ARM del router (ej. Python, tcpdump, mosquitto-client).
- **Crontab:** Tareas programadas en `/etc/crontabs/root`.
- **Hotplug Scripts:** Scripts ejecutados ante eventos de hardware (cambio de estado de SIM, pérdida de enlace WAN, activación de entrada digital) en `/etc/hotplug.d/`.
