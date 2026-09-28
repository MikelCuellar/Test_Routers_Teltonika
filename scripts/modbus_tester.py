"""Herramienta de prueba de lectura/escritura Modbus TCP para routers Teltonika RUT/TRB."""
import argparse
import struct
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    print("Error: Requiere 'pymodbus'. Instálala con 'pip install pymodbus'.")
    sys.exit(1)


def decode_float32(reg1: int, reg2: int) -> float:
    """Decodifica dos registros de 16 bits en un flotante IEEE 754 de 32 bits."""
    raw = struct.pack(">HH", reg1, reg2)
    return struct.unpack(">f", raw)[0]


def test_modbus(host: str, port: int, slave_id: int):
    print(f"🔌 Conectando a {host}:{port} (Modbus Slave ID: {slave_id})...")
    client = ModbusTcpClient(host, port=port, timeout=5)
    if not client.connect():
        print(f"❌ No se pudo establecer conexión Modbus TCP con {host}:{port}")
        return

    print("✅ Conexión establecida. Leyendo registros de estado Teltonika...")

    try:
        # 1. Leer registros de estado básicos (Registros 1 al 5)
        # Reg 1: Estado de conexión
        # Reg 2: Señal (RSSI)
        # Reg 3: Temperatura interna
        rr = client.read_holding_registers(address=1, count=5, slave=slave_id)
        if not rr.isError():
            conn_status = "Conectado" if rr.registers[0] == 1 else "Desconectado"
            rssi = rr.registers[1]
            temp = rr.registers[2] / 10.0 if rr.registers[2] > 0 else "N/A"
            print(f"\n📊 Métricas de Sistema:")
            print(f"   • Estado Celular: {conn_status} (Reg 1={rr.registers[0]})")
            print(f"   • Señal RSSI: -{rssi} dBm (Reg 2={rssi})")
            print(f"   • Temperatura: {temp} °C (Reg 3={rr.registers[2]})")
        else:
            print(f"⚠️ Error leyendo registros 1-5: {rr}")

        # 2. Leer Coordenadas GPS (Registros 10 al 14)
        gps_rr = client.read_holding_registers(address=10, count=5, slave=slave_id)
        if not gps_rr.isError() and len(gps_rr.registers) >= 4:
            lat = decode_float32(gps_rr.registers[0], gps_rr.registers[1])
            lon = decode_float32(gps_rr.registers[2], gps_rr.registers[3])
            speed = gps_rr.registers[4]
            print(f"\n📍 Geolocalización GPS:")
            print(f"   • Latitud : {lat:.6f}")
            print(f"   • Longitud: {lon:.6f}")
            print(f"   • Velocidad: {speed} km/h")
        else:
            print("ℹ️ GPS: Sin fijación satelital o registros no activos.")

        # 3. Leer Entradas Digitales (Registros 100 y 101)
        io_rr = client.read_holding_registers(address=100, count=2, slave=slave_id)
        if not io_rr.isError():
            print(f"\n⚡ Entradas Digitales (I/O):")
            print(f"   • DIN 1 (Reg 100): {'HIGH (1)' if io_rr.registers[0] == 1 else 'LOW (0)'}")
            print(f"   • DIN 2 (Reg 101): {'HIGH (1)' if io_rr.registers[1] == 1 else 'LOW (0)'}")

    except Exception as e:
        print(f"❌ Error durante la comunicación Modbus: {e}")
    finally:
        client.close()
        print("\n🔒 Conexión cerrada.")


def main():
    parser = argparse.ArgumentParser(description="Lector Modbus TCP para Teltonika")
    parser.add_argument("--host", default="192.168.1.1", help="IP del router")
    parser.add_argument("--port", type=int, default=502, help="Puerto Modbus TCP (default 502)")
    parser.add_argument("--slave", type=int, default=1, help="ID de esclavo Modbus (default 1)")

    args = parser.parse_args()
    test_modbus(args.host, args.port, args.slave)


if __name__ == "__main__":
    main()
