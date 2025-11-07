# Actualizaciones Requeridas para YouTube Downloads

## Requisitos del Sistema

- **Python 3.10 o superior** (requerido por yt-dlp para evitar advertencias de deprecación)
- FFmpeg (para procesamiento de audio/video)
- Deno/Node.js/Bun (recomendado para yt-dlp)

## Cambios Implementados

### 1. Actualización de yt-dlp
- ✅ Actualizado `requirements.txt` para usar `yt-dlp[default]>=2025.10.22`
- Esto instala yt-dlp con todas las dependencias opcionales necesarias

### 2. Configuración de Runtime JavaScript
- ✅ Agregado `js_runtimes: ['deno', 'node', 'bun']` en las opciones de yt-dlp
- ✅ Agregado `remote_components: 'ejs:github'` para descargar scripts EJS automáticamente

### 3. Ajustes en la Lógica de Formatos
- ✅ Permitir HLS como último recurso (ya no se bloquea completamente)
- ✅ Incluir `bestvideo+bestaudio/best` en la lista de formatos
- ✅ Priorizar formatos progresivos, pero permitir DASH y HLS como fallback

## Instalación Rápida

### Opción 1: Script Automático (Recomendado)

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Opción 2: Instalación Manual

1. Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

2. Instalar dependencias:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Pasos Adicionales Requeridos

### 1. Instalar Deno (Recomendado)
```bash
# macOS/Linux
curl -fsSL https://deno.land/install.sh | sh

# Asegúrate de agregar Deno al PATH
export PATH="$HOME/.deno/bin:$PATH"
```

### 2. Requisito: Python 3.10 o superior
```bash
python3 --version
# Debe mostrar Python 3.10 o superior

# Si no tienes Python 3.10+, instálalo:
# macOS (usando Homebrew)
brew install python@3.10

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv python3.10-dev

# O usa pyenv para gestionar versiones
pyenv install 3.10.0
pyenv local 3.10.0
```

### 3. Actualizar Dependencias
```bash
pip install -U "yt-dlp[default]"
```

### 4. Verificar FFmpeg
```bash
ffmpeg -version
# FFmpeg debe estar instalado y en el PATH
```

## Notas Importantes

- **Deno es el runtime recomendado** por yt-dlp para mayor seguridad
- Si Deno no está disponible, yt-dlp intentará usar Node.js o Bun
- Los formatos HLS ahora se permiten como último recurso cuando los formatos progresivos fallan
- La aplicación ahora usa `bestvideo+bestaudio/best` para permitir que yt-dlp combine pistas con ffmpeg

