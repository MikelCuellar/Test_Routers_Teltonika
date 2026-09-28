"""Descubrimiento automático de routers y gateways Teltonika en la red local."""
import argparse
import concurrent.futures
import ipaddress
import socket
import ssl
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# OUIs de direcciones MAC registradas a Teltonika Networks
TELTONIKA_MAC_OUIS = {
    "00:1e:42",
    "d8:a9:8b",
    "b8:f8:83",
    "00:03:7f",
}

TELTONIKA_PORTS = [80, 443, 502, 22]


def check_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except Exception:
        return False


def probe_teltonika_http(ip: str) -> dict:
    """Verifica si el host responde como un router Teltonika / RutOS vía HTTP/HTTPS."""
    info = {"is_teltonika": False, "model": "Desconocido", "web_port": None}

    # Probar HTTPS (puerto 443) y HTTP (puerto 80)
    for scheme, port in [("https", 443), ("http", 80)]:
        url = f"{scheme}://{ip}:{port}"
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, headers={"User-Agent": "TeltonikaDiscovery/1.0"})
            with urllib.request.urlopen(req, timeout=1.5, context=ctx if scheme == "https" else None) as resp:
                headers = dict(resp.getheaders())
                body_sample = resp.read(2048).decode("utf-8", errors="ignore").lower()

                # Señales de Teltonika / RutOS
                server_hdr = headers.get("server", "").lower()
                if "rutos" in server_hdr or "teltonika" in server_hdr or "rutos" in body_sample or "teltonika" in body_sample:
                    info["is_teltonika"] = True
                    info["web_port"] = port
                    info["scheme"] = scheme

                    # Extraer modelo si aparece en el título o metatags
                    for cand in ["rut240", "rut241", "rut950", "rut955", "rut956", "rutx09", "rutx11", "rutx50", "trb140", "trb245"]:
                        if cand in body_sample:
                            info["model"] = cand.upper()
                            break
                    return info
        except Exception:
            continue

    return info


def scan_host(ip_str: str) -> dict:
    open_ports = []
    for port in TELTONIKA_PORTS:
        if check_port(ip_str, port):
            open_ports.append(port)

    if not open_ports:
        return None

    result = {"ip": ip_str, "open_ports": open_ports}
    if 80 in open_ports or 443 in open_ports:
        http_info = probe_teltonika_http(ip_str)
        result.update(http_info)

    return result


def main():
    parser = argparse.ArgumentParser(description="Escáner y Descubrimiento de Routers Teltonika")
    parser.add_argument("--subnet", default="192.168.1.0/24", help="Subred a escanear en formato CIDR (ej: 192.168.1.0/24)")
    parser.add_argument("--threads", type=int, default=50, help="Hilos concurrentes para escaneo rápido")

    args = parser.parse_args()

    try:
        network = ipaddress.ip_network(args.subnet, strict=False)
    except ValueError as e:
        print(f"Subred inválida: {e}")
        sys.exit(1)

    print(f"🔍 Escaneando {network.num_addresses} hosts en {args.subnet}...")
    hosts = [str(ip) for ip in network.hosts()]

    discovered = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(scan_host, ip): ip for ip in hosts}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                discovered.append(res)
                telto_tag = " [TELTONIKA]" if res.get("is_teltonika") else ""
                model_tag = f" ({res.get('model')})" if res.get("model") != "Desconocido" else ""
                print(f"  • {res['ip']}: Puertos abiertos {res['open_ports']}{telto_tag}{model_tag}")

    print("\n" + "=" * 50)
    print(f"Resumen: {len(discovered)} dispositivos respondiendo en la red.")
    teltonikas = [d for d in discovered if d.get("is_teltonika")]
    print(f"Dispositivos Teltonika identificados: {len(teltonikas)}")
    for t in teltonikas:
        print(f"  -> {t['ip']} ({t.get('model', 'RUT/TRB')}) - WebUI en puerto {t.get('web_port')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
