"""Cliente de comunicación con routers Teltonika RutOS (REST API y JSON-RPC UBUS)."""
import argparse
import json
import logging
import sys
from typing import Any, Dict, Optional
import requests

try:
    import urllib3
except ImportError:
    from requests.packages import urllib3  # type: ignore

# Desactivar advertencias de certificados autofirmados en entornos de laboratorio
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TeltonikaClient")


class TeltonikaRutOSClient:
    """Cliente para interactuar con routers Teltonika bajo RutOS."""

    def __init__(
        self,
        host: str = "192.168.1.1",
        port: int = 443,
        use_https: bool = True,
        verify_ssl: bool = False,
        token: Optional[str] = None,
        username: str = "admin",
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.scheme = "https" if use_https else "http"
        self.base_url = f"{self.scheme}://{self.host}:{self.port}"
        self.verify_ssl = verify_ssl
        self.token = token
        self.username = username
        self.password = password
        self.ubus_session_id: Optional[str] = None
        self.session = requests.Session()

    # --- 1. Autenticación JSON-RPC UBUS (Compatible con RutOS Legacy y v7) ---

    def login_ubus(self) -> bool:
        """Inicia sesión a través del endpoint UBUS RPC."""
        url = f"{self.base_url}/ubus"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                "00000000000000000000000000000000",
                "session",
                "login",
                {"username": self.username, "password": self.password or ""},
            ],
        }
        try:
            res = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=10)
            data = res.json()
            if "result" in data and len(data["result"]) > 1 and "ubus_rpc_session" in data["result"][1]:
                self.ubus_session_id = data["result"][1]["ubus_rpc_session"]
                logger.info("Autenticado exitosamente en UBUS RPC.")
                return True
            logger.error(f"Error de login en UBUS: {data}")
            return False
        except Exception as e:
            logger.error(f"Excepción conectando a UBUS ({url}): {e}")
            return False

    def call_ubus(self, ubus_object: str, ubus_method: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Ejecuta una llamada UBUS RPC."""
        if not self.ubus_session_id and not self.login_ubus():
            raise ConnectionError("No se pudo establecer sesión con UBUS")

        url = f"{self.base_url}/ubus"
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "call",
            "params": [self.ubus_session_id, ubus_object, ubus_method, params or {}],
        }
        try:
            res = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=10)
            data = res.json()
            if "result" in data and len(data["result"]) > 1:
                return data["result"][1]
            return data
        except Exception as e:
            logger.error(f"Error en llamada UBUS ({ubus_object}.{ubus_method}): {e}")
            return None

    # --- 2. Métodos REST API (RutOS 7+) ---

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_system_info_rest(self) -> Optional[Dict[str, Any]]:
        """Consulta información del sistema vía REST API."""
        url = f"{self.base_url}/api/system/info"
        try:
            res = self.session.get(url, headers=self._get_headers(), verify=self.verify_ssl, timeout=10)
            if res.status_code == 200:
                return res.json()
            logger.warning(f"REST API /api/system/info retornó {res.status_code}")
            return None
        except Exception as e:
            logger.debug(f"REST API no disponible: {e}")
            return None

    # --- 3. Métodos de Alto Nivel (con fallback automático REST -> UBUS) ---

    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del router (Modelo, FW, Serial, Uptime)."""
        rest_data = self.get_system_info_rest()
        if rest_data:
            return rest_data

        # Fallback a UBUS
        res = self.call_ubus("system", "info")
        board = self.call_ubus("system", "board")
        return {
            "source": "ubus",
            "system_info": res or {},
            "board_info": board or {},
        }

    def get_cellular_signal(self) -> Dict[str, Any]:
        """Obtiene calidad de señal celular (RSSI, RSRP, RSRQ, SINR, Operador)."""
        # Intentar consultar módem vía UBUS gsm.modem0
        res = self.call_ubus("gsm.modem0", "get_signal_query")
        if not res:
            res = self.call_ubus("network.interface.mob1s1a1", "status")
        return res or {"error": "Módem celular no disponible o sin respuesta"}

    def get_gps_location(self) -> Dict[str, Any]:
        """Obtiene coordenadas GNSS (Latitud, Longitud, Altitud, Velocidad)."""
        res = self.call_ubus("gps", "get_status")
        if not res:
            res = self.call_ubus("gps", "info")
        return res or {"error": "GPS no habilitado o sin fijación satelital (No Fix)"}

    def get_io_status(self) -> Dict[str, Any]:
        """Obtiene estado de entradas y salidas digitales/analógicas."""
        res = self.call_ubus("ioman", "status")
        return res or {"error": "Controlador I/O no disponible"}

    def set_digital_output(self, output_id: str = "dout1", state: int = 1) -> bool:
        """Activa (1) o desactiva (0) una salida digital o relé."""
        res = self.call_ubus("ioman", "set_state", {"pin": output_id, "state": state})
        return res is not None


def main():
    parser = argparse.ArgumentParser(description="Cliente Teltonika RutOS")
    parser.add_argument("--host", default="192.168.1.1", help="Dirección IP del router")
    parser.add_argument("--port", type=int, default=443, help="Puerto HTTP/HTTPS")
    parser.add_argument("--http", action="store_true", help="Usar HTTP en vez de HTTPS")
    parser.add_argument("--user", default="admin", help="Usuario administrador")
    parser.add_argument("--password", default="admin01", help="Contraseña de administrador")
    parser.add_argument("--token", help="Token Bearer de API (opcional)")
    parser.add_argument(
        "--action",
        choices=["info", "signal", "gps", "io", "set_output"],
        default="info",
        help="Acción a consultar",
    )
    parser.add_argument("--pin", default="dout1", help="Pin para set_output")
    parser.add_argument("--state", type=int, default=1, choices=[0, 1], help="Estado 0 o 1")

    args = parser.parse_args()

    client = TeltonikaRutOSClient(
        host=args.host,
        port=args.port,
        use_https=not args.http,
        verify_ssl=False,
        username=args.user,
        password=args.password,
        token=args.token,
    )

    if args.action == "info":
        res = client.get_system_info()
    elif args.action == "signal":
        res = client.get_cellular_signal()
    elif args.action == "gps":
        res = client.get_gps_location()
    elif args.action == "io":
        res = client.get_io_status()
    elif args.action == "set_output":
        ok = client.set_digital_output(args.pin, args.state)
        res = {"success": ok, "pin": args.pin, "state": args.state}
    else:
        res = {"error": "Acción no reconocida"}

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
