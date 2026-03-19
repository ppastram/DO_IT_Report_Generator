#!/bin/bash
# DO IT Report Generator — Lanzador para Mac/Linux
# En Mac es mejor usar "Generar Reporte.command" (doble clic abre Terminal).

cd "$(dirname "$0")"

# Verificar Python 3
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "  ============================================"
    echo "   Python 3 no está instalado."
    echo "   Descárgalo en: https://python.org"
    echo "  ============================================"
    echo ""
    exit 1
fi

# Instalar/reparar Pillow si falta o tiene error de arquitectura
if ! python3 -c "from PIL import Image" 2>/dev/null; then
    echo "Instalando dependencias..."
    python3 -m pip install --force-reinstall pillow -q
fi

# Ejecutar la app
python3 app.py
