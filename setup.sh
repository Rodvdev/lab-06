#!/bin/bash
# Script de instalación para Lab 06 - API Flask
# Requiere Python 3.10 o superior

set -e  # Salir si hay algún error

echo "🚀 Configurando Lab 06 - API Flask"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo "📋 Verificando Python..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}❌ Error: Se requiere Python 3.10 o superior${NC}"
    echo "Versión actual: Python $PYTHON_VERSION"
    echo ""
    echo "Instala Python 3.10+ usando:"
    echo "  macOS: brew install python@3.10"
    echo "  Linux: sudo apt-get install python3.10"
    echo "  pyenv: pyenv install 3.10.0"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION detectado${NC}"
echo ""

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  El directorio venv ya existe. ¿Deseas recrearlo? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✅ Entorno virtual recreado${NC}"
    else
        echo "Usando entorno virtual existente"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Entorno virtual creado${NC}"
fi
echo ""

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate
echo -e "${GREEN}✅ Entorno virtual activado${NC}"
echo ""

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✅ pip actualizado${NC}"
echo ""

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencias instaladas${NC}"
echo ""

# Verificar FFmpeg
echo "🎬 Verificando FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1)
    echo -e "${GREEN}✅ FFmpeg encontrado: $FFMPEG_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  FFmpeg no encontrado${NC}"
    echo "FFmpeg es necesario para procesar audio/video"
    echo "Instala con:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: sudo apt-get install ffmpeg"
fi
echo ""

# Crear directorio de descargas si no existe
if [ ! -d "downloads" ]; then
    mkdir -p downloads
    echo -e "${GREEN}✅ Directorio downloads creado${NC}"
fi

echo ""
echo -e "${GREEN}✨ Instalación completada!${NC}"
echo ""
echo "Para ejecutar la aplicación:"
echo "  1. Activa el entorno virtual: source venv/bin/activate"
echo "  2. Ejecuta: python app.py"
echo "  3. Abre: http://127.0.0.1:5000"
echo ""
