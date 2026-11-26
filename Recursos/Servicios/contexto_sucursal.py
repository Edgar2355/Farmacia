import json
from pathlib import Path

RUTA_RECURSOS = Path(__file__).resolve().parents[1]
ARCHIVO_SUCURSAL = RUTA_RECURSOS / "sucursal.json"

SUCURSAL_DEFAULT = {"id": 1, "direccion": "Sucursal Principal"}


def obtener_sucursal():
    """Lee la sucursal activa desde Recursos/sucursal.json soportando UTF-8 y Latin-1/CP1252."""
    if ARCHIVO_SUCURSAL.exists():
        for codificacion in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(ARCHIVO_SUCURSAL, "r", encoding=codificacion) as archivo:
                    datos = json.load(archivo)
                if isinstance(datos, dict) and "id" in datos and "direccion" in datos:
                    # Si estaba en latin-1/cp1252, re-guardarlo normalizado en UTF-8
                    if codificacion != "utf-8":
                        guardar_sucursal(datos)
                    return datos
            except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                continue

    guardar_sucursal(SUCURSAL_DEFAULT)
    return dict(SUCURSAL_DEFAULT)


def guardar_sucursal(sucursal_dict):
    """Guarda la sucursal activa en Recursos/sucursal.json en codificación UTF-8."""
    datos = {
        "id": int(sucursal_dict.get("id", 0)),
        "direccion": str(sucursal_dict.get("direccion", "No especificado")),
    }
    with open(ARCHIVO_SUCURSAL, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)
    return datos
