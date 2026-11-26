#!/usr/bin/env bash
# ==============================================================================
# Lanzador Automático para Sistemas Linux / macOS - Farmacia CUCEI
# ==============================================================================

set -e

# Ubicar el directorio donde se encuentra este script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="Librerias"
VENV_PY="$SCRIPT_DIR/$VENV_DIR/bin/python"
SCRIPT_NAME="Login-menu.py"
REQ_FILE="requirements.txt"

echo "==================================================="
echo "         INICIANDO SISTEMA FARMACIA CUCEI          "
echo "==================================================="
echo ""

# 1. Detectar intérprete de Python 3 del sistema
PYTHON_BIN=""
for candidato in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidato" >/dev/null 2>&1; then
        PYTHON_BIN="$candidato"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "[ERROR] No se encontró Python 3 instalado en el sistema."
    echo "Instálalo con: sudo apt install python3 python3-venv python3-tk"
    exit 1
fi

# 2. Verificar que python3-tk (Tkinter) esté disponible en Linux
if ! "$PYTHON_BIN" -c "import tkinter" >/dev/null 2>&1; then
    echo "[ADVERTENCIA] El módulo 'tkinter' no está instalado en tu distribución Linux."
    echo "Por favor instálalo ejecutando según tu distribución:"
    echo "  Ubuntu/Debian/Mint : sudo apt update && sudo apt install -y python3-tk python3-venv"
    echo "  Fedora/RHEL        : sudo dnf install -y python3-tkinter"
    echo "  Arch/Manjaro       : sudo pacman -S tk"
    exit 1
fi

# 3. Verificar o recrear el entorno virtual (si no existe o si fue creado en Windows)
RECREAR_VENV=0
if [ ! -x "$VENV_PY" ]; then
    RECREAR_VENV=1
else
    if ! "$VENV_PY" --version >/dev/null 2>&1; then
        RECREAR_VENV=1
    fi
fi

if [ "$RECREAR_VENV" -eq 1 ]; then
    if [ -d "$VENV_DIR" ]; then
        echo "[Aviso] Limpiando entorno virtual anterior (o de otro sistema operativo)..."
        rm -rf "$VENV_DIR"
    fi
    echo "[1/3] Creando entorno virtual '$VENV_DIR' con $PYTHON_BIN..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# 4. Verificar e instalar dependencias de requirements.txt
if ! "$VENV_PY" -c "import mysql.connector, fpdf, dotenv, google.genai" >/dev/null 2>&1; then
    echo "[2/3] Instalando dependencias desde '$REQ_FILE'..."
    "$VENV_PY" -m pip install --upgrade pip
    "$VENV_PY" -m pip install -r "$REQ_FILE"
    echo ""
    echo "Instalación completada con éxito."
    echo ""
fi

# 5. Ejecutar la aplicación principal
echo "[Ejecutando] Iniciando '$SCRIPT_NAME'..."
echo ""
"$VENV_PY" "$SCRIPT_NAME"
