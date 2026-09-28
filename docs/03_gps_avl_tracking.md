# 03 — Geolocalización, GNSS y Seguimiento AVL

## 1. Módulo GNSS en Routers Teltonika
Modelos como el `RUT955`, `RUT956`, `RUTX11` y `RUTX12` incorporan receptores GNSS multi-constelación compatibles con:
- **GPS** (EE. UU.)
- **GLONASS** (Rusia)
- **Galileo** (Unión Europea)
- **BeiDou** (China)

---

## 2. Métodos de Transmisión de Coordenadas

### 2.1 Reenvío de Sentencias NMEA (NMEA Forwarding)
El router puede reenviar el flujo sin procesar de tramas NMEA-0183 (como `$GPGGA`, `$GPRMC`, `$GPVTG`) a través de:
- **Socket TCP o UDP:** Hacia un servidor central o demonio local.
- **Puerto Serial / Consola:** Hacia una computadora de a bordo o display.

### 2.2 Protocolo TAVL y Code8 / Code8 Extended
Teltonika utiliza protocolos binarios optimizados para telemática vehicular (heredados de sus dispositivos de rastreo FMB):
- **Protocolo AVL:** Empaqueta en formato binario compacto (Big-Endian):
  - Timestamp (milisegundos desde Unix Epoch).
  - Prioridad del evento.
  - Longitud y Latitud (enteros con escala de 10^7).
  - Altitud, Rumbo (Ángulo), Satélites visibles, Velocidad.
  - Elementos IO (estados de encendido/ignición, entradas analógicas, odómetro).

### 2.3 Servicio "GPS to Server" Integrado en RutOS
En `Services > GPS > GPS to Server`, RutOS permite enviar paquetes de posición vía HTTP/HTTPS o TCP/UDP con intervalos configurables por:
- **Tiempo:** Cada $X$ segundos.
- **Distancia:** Cada $Y$ metros recorridos.
- **Ángulo de giro:** Cada vez que el vehículo cambia de rumbo más de $Z$ grados.

---

## 3. Geocercas Locales (Geofencing en el Dispositivo)
El router puede almacenar geocercas poligonales o circulares de forma local en su memoria:
- **Evento de Entrada:** Dispara una regla local (ej. cerrar un relé, enviar un SMS de alerta, publicar un evento MQTT).
- **Evento de Salida:** Notifica la salida de la zona de trabajo segura (ideal para maquinaria en [[Geotask]]).
