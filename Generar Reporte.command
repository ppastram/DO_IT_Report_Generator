#!/bin/bash
# DO IT Report Generator — Lanzador para macOS
# Doble clic en este archivo para abrir la app en Terminal.

cd "$(dirname "$0")"

# Verificar Python 3
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "  ============================================"
    echo "   Python 3 no está instalado."
    echo "   Descárgalo en: https://python.org"
    echo "  ============================================"
    echo ""
    echo "Presiona Enter para cerrar..."
    read
    exit 1
fi

# Instalar/reparar Pillow si falta o tiene error de arquitectura
# Usamos "from PIL import Image" porque es lo que dispara la carga del binario nativo
if ! python3 -c "from PIL import Image" 2>/dev/null; then
    echo "Instalando dependencias..."
    python3 -m pip install --force-reinstall pillow -q
fi

# Ejecutar la app
python3 app.py
STATUS=$?

# Si hubo un error, mantener la ventana abierta
if [ $STATUS -ne 0 ]; then
    echo ""
    echo "Ocurrió un error. Presiona Enter para cerrar..."
    read
fi
