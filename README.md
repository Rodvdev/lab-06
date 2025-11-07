# Lab 06 - API Flask

Aplicación Flask para descargar videos de múltiples plataformas (YouTube, TikTok, Instagram, etc.) y consultar información de Pokémon.

## Requisitos del Sistema

- **Python 3.10 o superior** (requerido)
- **FFmpeg** (para procesamiento de audio/video)
- **Deno/Node.js/Bun** (recomendado para yt-dlp, opcional)

## Instalación y Configuración del Entorno

### 1. Verificar Python

```bash
python3 --version
# Debe mostrar Python 3.10 o superior
```

Si no tienes Python 3.10+, instálalo:

**macOS (usando Homebrew):**
```bash
brew install python@3.10
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv python3.10-dev
```

**Usando pyenv (recomendado):**
```bash
pyenv install 3.10.0
pyenv local 3.10.0
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias del proyecto
pip install -r requirements.txt
```

### 4. Verificar FFmpeg

```bash
ffmpeg -version
```

Si FFmpeg no está instalado:

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html)

### 5. (Opcional) Instalar Deno

Deno es recomendado por yt-dlp para mayor seguridad:

```bash
# macOS/Linux
curl -fsSL https://deno.land/install.sh | sh

# Agregar al PATH (agregar a ~/.bashrc o ~/.zshrc)
export PATH="$HOME/.deno/bin:$PATH"
```

## Ejecutar la Aplicación

```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Ejecutar la aplicación
python app.py
```

La aplicación estará disponible en: `http://127.0.0.1:5000`

## Estructura del Proyecto

```
lab-06/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── runtime.txt           # Versión de Python para despliegue
├── .python-version        # Versión de Python para pyenv
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── pokemon.html
│   └── download.html
├── static/               # Archivos estáticos
│   └── styles.css
└── downloads/            # Directorio de descargas (se crea automáticamente)
```

## API Endpoints

### Descarga de Videos

- `POST /api/download/start` - Iniciar descarga
  ```json
  {"url": "https://...", "quality": "best"}
  ```

- `GET /api/download/progress/<task_id>` - Consultar progreso

- `POST /api/detect-platform` - Detectar plataforma
  ```json
  {"url": "https://..."}
  ```

- `POST /api/formats/list` - Listar formatos disponibles
  ```json
  {"url": "https://..."}
  ```

- `GET /api/downloads/list` - Listar archivos descargados

### Pokémon

- `GET /pokemon` - Página de búsqueda de Pokémon
- `POST /pokemon` - Buscar Pokémon por nombre

## Uso desde Terminal (curl)

```bash
# Iniciar descarga
curl -X POST http://localhost:5000/api/download/start \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "quality": "best"}'

# Consultar progreso
curl http://localhost:5000/api/download/progress/TASK_ID

# Detectar plataforma
curl -X POST http://localhost:5000/api/detect-platform \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

## Notas Importantes

- Los archivos descargados se guardan en `downloads/` y se eliminan automáticamente después de 7 días
- La aplicación soporta múltiples plataformas: YouTube, TikTok, Instagram, Facebook, Twitter/X
- Para más detalles sobre actualizaciones, ver `README_UPDATES.md`

## Solución de Problemas

### Error: "Support for Python version 3.9 has been deprecated"
- Actualiza a Python 3.10 o superior
- Verifica la versión con `python3 --version`

### Error 403 al descargar videos
- La aplicación intenta automáticamente con diferentes configuraciones
- Algunos videos pueden estar protegidos o no disponibles

### FFmpeg no encontrado
- Asegúrate de que FFmpeg esté instalado y en el PATH
- Verifica con `ffmpeg -version`

## Desarrollo

Para desarrollo, se recomienda usar un entorno virtual y mantener las dependencias actualizadas:

```bash
# Activar entorno virtual
source venv/bin/activate

# Actualizar dependencias
pip install --upgrade -r requirements.txt

# Verificar instalación
pip list
```



