# 02 — Protocolos de Telemetría: Modbus, MQTT y Data to Server

## 1. El Servicio "Data to Server"
Una de las funcionalidades más potentes de Teltonika RutOS es **Data to Server** (Servicio de Despacho de Datos).
Permite configurar el router para que recopile periódicamente variables del sistema, métricas del módem, telemetría GPS o registros Modbus de dispositivos externos, y los envíe automáticamente a un servidor central.

### Protocolos Soportados de Salida:
- **HTTP / HTTPS POST:** Envía payloads JSON o form-data a un webhook o API REST backend.
- **MQTT / MQTTS:** Publica en un broker MQTT en topics definidos con QoS 0, 1 o 2.
- **AWS Kinesis / Azure IoT Hub:** Para arquitecturas cloud masivas.

### Parámetros de Recopilación Típicos:
- `%TIMESTAMP%` : Marca de tiempo UTC.
- `%ROUTER_NAME%` / `%IMEI%` : Identificador del equipo.
- `%LAT%`, `%LON%`, `%SPEED%`: Coordenadas GPS y velocidad.
- `%SIGNAL%` / `%RSRP%` / `%OPERATOR%`: Calidad de señal celular.
- `%TEMP%` : Temperatura interna de la placa.
- `%INPUT1%`, `%INPUT2%`: Estado de entradas digitales y analógicas.
- Datos Modbus personalizados (bytes o enteros de PLCs conectados).

---

## 2. Modbus TCP & RTU en Routers RUT

Los routers Teltonika con interfaces seriales (como el `RUT955`, `RUT956`, `TRB245`) o Ethernet disponen de soporte nativo completo para **Modbus**:

### 2.1 Modbus TCP Slave (El Router expone sus variables internas)
Cualquier cliente SCADA, software central o script Python puede leer las variables internas del router mediante el protocolo Modbus TCP en el puerto 502.

#### Registros Modbus Clave de Teltonika (Direcciones Estándar):
| Dirección de Registro | Tipo | Descripción | Unidad / Valores |
|---|---|---|---|
| **1** | 16-bit Integer | Estado de la conexión celular | 0=Desconectado, 1=Conectado |
| **2** | 16-bit Integer | RSSI (Potencia de señal) | dBm |
| **3** | 16-bit Integer | Temperatura interna del dispositivo | Grados Celsius x 10 |
| **10 - 11** | 32-bit Float | Latitud GPS | Grados decimales |
| **12 - 13** | 32-bit Float | Longitud GPS | Grados decimales |
| **14** | 16-bit Integer | Velocidad GPS | km/h |
| **100** | 16-bit Integer | Estado entrada digital 1 (DIN1) | 0=Low, 1=High |
| **101** | 16-bit Integer | Estado entrada digital 2 (DIN2) | 0=Low, 1=High |
| **201** | Coil / Register | Estado salida digital 1 (DOUT1) | 0=Off, 1=On (Permite escritura) |

### 2.2 Modbus TCP/RTU Master (El Router lee sensores externos)
El router actúa como maestro: interroga periódicamente sensores de nivel, medidores de energía, inversores solares o PLCs mediante RS485 o Modbus TCP, y usa *Data to Server* para transmitir esos datos a la plataforma central de GrupoGeo.

---

## 3. MQTT Broker y Client Integrado
RutOS incluye el demonio **Mosquitto**:
1. **MQTT Broker Local:** Puede actuar como broker para dispositivos locales en la subred LAN de una faena o vehículo.
2. **MQTT Client / Bridge:** Permite establecer un bridge bidireccional contra el broker central en la nube con cifrado TLS/SSL y autenticación por certificado.
