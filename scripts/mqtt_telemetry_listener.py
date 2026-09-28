"""Receptor MQTT para telemetría y eventos enviados por routers Teltonika (Data to Server)."""
import argparse
import datetime
import json
import logging
import sys

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: Requiere la librería paho-mqtt. Instálala con 'pip install paho-mqtt'.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TeltonikaMQTT")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Conectado exitosamente al broker MQTT. Suscribiendo al topic: {userdata['topic']}")
        client.subscribe(userdata["topic"])
    else:
        logger.error(f"Fallo al conectar con el broker MQTT (código {rc})")


def on_message(client, userdata, msg):
    payload_raw = msg.payload.decode("utf-8", errors="replace")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 60)
    print(f"📡 MENSAJE RECIBIDO | Topic: {msg.topic} | Hora: {timestamp}")
    print("-" * 60)

    try:
        data = json.loads(payload_raw)
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Analizar campos comunes de telemetría Teltonika
        if "lat" in data and "lon" in data:
            print(f"📍 GPS Detectado: Lat={data.get('lat')}, Lon={data.get('lon')}, Vel={data.get('speed', 0)} km/h")
        if "rsrp" in data or "rssi" in data:
            print(f"📶 Señal Celular: RSRP={data.get('rsrp')} dBm, RSSI={data.get('rssi')} dBm")
        if "temperature" in data or "temp" in data:
            print(f"🌡️ Temperatura: {data.get('temperature') or data.get('temp')} °C")
    except json.JSONDecodeError:
        print("Texto plano / no-JSON:")
        print(payload_raw)
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Receptor de Telemetría MQTT para Teltonika")
    parser.add_argument("--broker", default="localhost", help="Host del broker MQTT")
    parser.add_argument("--port", type=int, default=1883, help="Puerto del broker MQTT")
    parser.add_argument("--topic", default="teltonika/#", help="Topic a suscribir (ej. teltonika/#)")
    parser.add_argument("--user", help="Usuario MQTT (opcional)")
    parser.add_argument("--password", help="Contraseña MQTT (opcional)")

    args = parser.parse_args()

    client = mqtt.Client(userdata={"topic": args.topic})
    if args.user:
        client.username_pw_set(args.user, args.password)

    client.on_connect = on_connect
    client.on_message = on_message

    logger.info(f"Conectando a {args.broker}:{args.port}...")
    try:
        client.connect(args.broker, args.port, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Deteniendo receptor MQTT.")
        client.disconnect()
    except Exception as e:
        logger.error(f"Error conectando a broker: {e}")


if __name__ == "__main__":
    main()
