# Conexión a la base de datos (Optimizado para Local + Túneles TCP Remotos como Pinggy.io)
import os
import re
import json
from pathlib import Path

RUTA_RECURSOS = Path(__file__).resolve().parent
RUTA_PROYECTO = RUTA_RECURSOS.parent
ARCHIVO_DB_CONFIG = RUTA_RECURSOS / "db_config.json"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=RUTA_PROYECTO / ".env")
    load_dotenv(dotenv_path=RUTA_RECURSOS / "Menus" / "Ventas" / "Gemini_api.env")
except ImportError:
    pass

CONFIG_DEFAULT = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "dbfarmacia",
}

# Conexión persistente reutilizable para evitar latencia de handshake TCP/SSH en túneles Pinggy.io
_CONEXION_ACTIVA = None
_FIRMA_CONFIG_ACTIVA = None


class ConexionPersistenteWrapper:
    """
    Envuelve una conexión MySQL real para reutilizar el mismo socket TCP entre consultas.
    Cuando los DAOs llaman a `con.close()` en su bloque `finally`, cierra los cursores
    abiertos pero mantiene vivo el túnel TCP para que la siguiente consulta sea instantánea.
    """

    def __init__(self, raw_conn):
        self._raw = raw_conn

    def cursor(self, *args, **kwargs):
        if kwargs.get("buffered") is None:
            kwargs["buffered"] = True
        return self._raw.cursor(*args, **kwargs)

    def commit(self):
        return self._raw.commit()

    def rollback(self):
        return self._raw.rollback()

    def is_connected(self):
        return self._raw.is_connected()

    def ping(self, reconnect=True, attempts=2, delay=1):
        return self._raw.ping(reconnect=reconnect, attempts=attempts, delay=delay)

    def close(self):
        # No cerramos el socket subyacente en cada consulta para evitar 300-600ms de handshake en Pinggy;
        # nos aseguramos de limpiar cualquier transacción pendiente.
        try:
            if getattr(self._raw, "in_transaction", False):
                self._raw.rollback()
        except Exception:
            pass

    def cerrar_definitivamente(self):
        try:
            self._raw.close()
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._raw, name)


def cerrar_pool_conexiones():
    """Cierra físicamente la conexión persistente (útil al cambiar de servidor o cerrar la app)."""
    global _CONEXION_ACTIVA, _FIRMA_CONFIG_ACTIVA
    if _CONEXION_ACTIVA is not None:
        try:
            _CONEXION_ACTIVA.cerrar_definitivamente()
        except Exception:
            pass
    _CONEXION_ACTIVA = None
    _FIRMA_CONFIG_ACTIVA = None


def parsear_url_tunel(texto):
    """
    Extrae (host, port) desde una URL de túnel Pinggy/Ngrok o cadena host:puerto.
    Ejemplos soportados:
      - 'tcp://rnxyz-189-203.a.free.pinggy.link:43219'
      - 'rnxyz-189-203.a.free.pinggy.link:43219'
      - 'localhost:3306'
      - 'localhost' -> ('localhost', 3306)
    """
    limpio = str(texto or "").strip()
    if not limpio:
        return "localhost", 3306

    limpio = re.sub(r"^[a-zA-Z0-9+\-.]+://", "", limpio)
    limpio = limpio.split("/")[0].strip()

    if ":" in limpio:
        partes = limpio.rsplit(":", 1)
        host = partes[0].strip() or "localhost"
        try:
            port = int(partes[1].strip())
        except ValueError:
            port = 3306
        return host, port

    return limpio, 3306


def obtener_config_db():
    """
    Lee la configuración de conexión con la siguiente prioridad:
    1. Archivo Recursos/db_config.json (si fue configurado desde la interfaz o existe).
    2. Variables de entorno (.env): DB_URL (o PINGGY_URL) y DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.
    3. Valores por defecto (localhost:3306).
    """
    cfg = dict(CONFIG_DEFAULT)

    # 1. Variables de entorno (.env)
    url_env = os.getenv("DB_URL") or os.getenv("PINGGY_URL")
    if url_env:
        h_env, p_env = parsear_url_tunel(url_env)
        cfg["host"] = h_env
        cfg["port"] = p_env

    if os.getenv("DB_HOST"):
        h_env, p_env = parsear_url_tunel(os.getenv("DB_HOST"))
        cfg["host"] = h_env
        if ":" in str(os.getenv("DB_HOST")):
            cfg["port"] = p_env

    if os.getenv("DB_PORT"):
        try:
            cfg["port"] = int(os.getenv("DB_PORT"))
        except ValueError:
            pass
    if os.getenv("DB_USER"):
        cfg["user"] = os.getenv("DB_USER")
    if os.getenv("DB_PASSWORD") is not None:
        cfg["password"] = os.getenv("DB_PASSWORD")
    if os.getenv("DB_NAME"):
        cfg["database"] = os.getenv("DB_NAME")

    # 2. Archivo Recursos/db_config.json (configurado desde el botón en Login)
    if ARCHIVO_DB_CONFIG.exists():
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(ARCHIVO_DB_CONFIG, "r", encoding=enc) as f:
                    datos = json.load(f)
                if isinstance(datos, dict):
                    cfg["host"] = str(datos.get("host") or cfg["host"]).strip()
                    cfg["port"] = int(datos.get("port") or cfg["port"])
                    cfg["user"] = str(datos.get("user") or cfg["user"]).strip()
                    cfg["password"] = str(
                        datos.get("password") if datos.get("password") is not None else cfg["password"]
                    )
                    cfg["database"] = str(datos.get("database") or cfg["database"]).strip()
                break
            except Exception:
                continue

    return cfg


def guardar_config_db(host="localhost", port=3306, user="root", password="", database="dbfarmacia"):
    """Guarda la configuración de conexión activa en Recursos/db_config.json y reinicia la conexión persistente."""
    host_limpio, port_extraido = parsear_url_tunel(f"{host}:{port}" if ":" not in str(host) else str(host))
    try:
        port_final = int(port) if ":" not in str(host) else port_extraido
    except ValueError:
        port_final = port_extraido

    datos = {
        "host": host_limpio,
        "port": port_final,
        "user": str(user or "root").strip(),
        "password": str(password or ""),
        "database": str(database or "dbfarmacia").strip(),
    }
    with open(ARCHIVO_DB_CONFIG, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

    cerrar_pool_conexiones()
    return datos


def conectar(forzar_nueva=False):
    """
    Devuelve una conexión MySQL activa.
    Reutiliza la conexión abierta mediante `ConexionPersistenteWrapper` para eliminar la latencia
    de apertura de sockets a través de Pinggy.io, reconectando automáticamente si el túnel se reinició.
    """
    global _CONEXION_ACTIVA, _FIRMA_CONFIG_ACTIVA
    import mysql.connector

    cfg = obtener_config_db()
    firma = (cfg["host"], int(cfg["port"]), cfg["user"], cfg["password"], cfg["database"])

    if not forzar_nueva and _CONEXION_ACTIVA is not None and _FIRMA_CONFIG_ACTIVA == firma:
        try:
            _CONEXION_ACTIVA.ping(reconnect=True, attempts=2, delay=1)
            if _CONEXION_ACTIVA.is_connected():
                return _CONEXION_ACTIVA
        except Exception:
            cerrar_pool_conexiones()

    cerrar_pool_conexiones()
    es_remoto = cfg["host"] not in ("localhost", "127.0.0.1")
    timeout_seg = 8 if es_remoto else 4

    raw_conn = mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=int(cfg["port"]),
        connection_timeout=timeout_seg,
        autocommit=True,
        use_pure=True,
    )
    _CONEXION_ACTIVA = ConexionPersistenteWrapper(raw_conn)
    _FIRMA_CONFIG_ACTIVA = firma
    return _CONEXION_ACTIVA
