"""Gestor de sesión de bajo nivel con routers Teltonika vía SSH y RutOS API."""
import logging
import time
from dataclasses import dataclass
from typing import Optional
import paramiko

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DeviceSession")


@dataclass
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @property
    def output(self) -> str:
        return self.stdout.strip()


class DeviceSession:
    """Sesión SSH industrial con routers Teltonika RutOS."""

    def __init__(
        self,
        host: str = "192.168.1.1",
        port: int = 22,
        username: str = "root",
        password: str = "admin01",
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None
        self._connected = False

    def connect(self) -> bool:
        """Establece la conexión SSH con el router."""
        if self._connected and self.client:
            return True

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Intentar conectar con usuario root (o admin)
        users_to_try = [self.username]
        if self.username != "root":
            users_to_try.append("root")
        if self.username != "admin":
            users_to_try.append("admin")

        last_error = None
        for u in users_to_try:
            try:
                logger.info(f"Intentando conexión SSH hacia {self.host}:{self.port} con usuario '{u}'...")
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=u,
                    password=self.password,
                    timeout=self.timeout,
                    banner_timeout=self.timeout,
                    auth_timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False,
                )
                self._connected = True
                self.username = u
                logger.info(f"✅ Conectado exitosamente por SSH como '{u}'.")
                return True
            except Exception as e:
                last_error = e
                logger.debug(f"Fallo login con usuario '{u}': {e}")

        logger.error(f"❌ No se pudo conectar vía SSH a {self.host}:{self.port}: {last_error}")
        return False

    def run(self, cmd: str, timeout: float = 15.0) -> CommandResult:
        """Ejecuta un comando en RutOS y retorna CommandResult."""
        if not self._connected or not self.client:
            if not self.connect():
                return CommandResult(command=cmd, exit_code=-1, stdout="", stderr="Sin conexión SSH")

        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode("utf-8", errors="replace")
            err_str = stderr.read().decode("utf-8", errors="replace")
            return CommandResult(command=cmd, exit_code=exit_code, stdout=out_str, stderr=err_str)
        except Exception as e:
            logger.error(f"Error ejecutando '{cmd}': {e}")
            return CommandResult(command=cmd, exit_code=-2, stdout="", stderr=str(e))

    def read_file(self, path: str) -> Optional[str]:
        """Lee el contenido de un archivo del router vía cat."""
        res = self.run(f"cat '{path}' 2>/dev/null")
        if res.success:
            return res.stdout
        return None

    def close(self) -> None:
        """Cierra la conexión SSH."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self._connected = False
        self.client = None
