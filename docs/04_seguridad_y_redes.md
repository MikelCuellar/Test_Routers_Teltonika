# 04 — Seguridad, Conectividad Remota, VPNs y RMS

## 1. Conmutación por Error y Redundancia (WAN Failover)
En operaciones de terreno, la disponibilidad continua del enlace es crítica:
1. **Multi-SIM / Dual SIM:** Modelos como RUT950/955/956 permiten insertar dos tarjetas SIM (ej. Entel y Movistar en Chile).
   - Conmutación automática ante pérdida de señal, límite de datos, fallo de ping ICMP o error de registro de red.
2. **WAN Backup:** La conexión cableada (Ethernet WAN) tiene prioridad; si cae el enlace fijo, el módem 4G/5G asume el tráfico de forma transparente en menos de 10 segundos.

---

## 2. Redes Privadas Virtuales (VPNs)

RutOS soporta los protocolos industriales y modernos de VPN más robustos:

### 2.1 WireGuard
- Protocolo criptográfico de última generación, ligero y de máximo rendimiento en procesadores embebidos.
- Ideal para conectar routers de terreno directamente a los servidores cloud de GrupoGeo con mínimo consumo de CPU y latencia despreciable.

### 2.2 OpenVPN
- Soporte en modos Cliente y Servidor (TUN/TAP), con autenticación por clave pública/privada (PKI / certificados X.509).
- Compatible con autenticación de dos factores o tokens dinámicos.

### 2.3 IPsec / IKEv2
- Utilizado para enlaces corporativos con firewalls perimetrales (Fortinet, Cisco, pfSense).

### 2.4 ZeroTier & Tailscale
- Redes mesh overlay que permiten acceso directo sin necesidad de IP pública estática en la tarjeta SIM del router (superando las restricciones de CGNAT impuestas por operadores móviles).

---

## 3. Teltonika RMS (Remote Management System)
**RMS** es la plataforma cloud SaaS de Teltonika para administración centralizada:
- **RMS Management:** Monitoreo de estado de flota, actualización masiva de firmwares, respaldos de configuración, alertas por correo.
- **RMS Connect:** Túneles seguros para acceder por HTTP, SSH, RDP o VNC a los dispositivos conectados detrás de la LAN del router (PLCs, cámaras, pantallas, PCs) sin abrir puertos en internet.
- **RMS VPN:** Creación de redes privadas bajo demanda con un solo clic.

---

## 4. Hardening y Seguridad Perimetral
- **Firewall:** Filtrado de paquetes basado en zonas LAN/WAN.
- **Prevención de Ataques:** Módulo `fail2ban` integrado contra intentos de fuerza bruta en SSH y WebUI.
- **Control de Acceso:** Bloqueo de gestión remota desde la interfaz WAN pública a menos que se acceda vía VPN.
