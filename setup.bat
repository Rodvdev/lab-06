@echo off
REM Script de instalación para Lab 06 - API Flask (Windows)
REM Requiere Python 3.10 o superior

echo 🚀 Configurando Lab 06 - API Flask
echo.

REM Verificar Python
echo 📋 Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python no encontrado
    echo Instala Python 3.10+ desde https://www.python.org/downloads/
    exit /b 1
)

python --version
echo ✅ Python detectado
echo.

REM Crear entorno virtual
echo 📦 Creando entorno virtual...
if exist venv (
    echo ⚠️  El directorio venv ya existe. ¿Deseas recrearlo? (S/N)
    set /p response=
    if /i "%response%"=="S" (
        rmdir /s /q venv
        python -m venv venv
        echo ✅ Entorno virtual recreado
    ) else (
        echo Usando entorno virtual existente
    )
) else (
    python -m venv venv
    echo ✅ Entorno virtual creado
)
echo.

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat
echo ✅ Entorno virtual activado
echo.

REM Actualizar pip
echo ⬆️  Actualizando pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip actualizado
echo.

REM Instalar dependencias
echo 📥 Instalando dependencias...
pip install -r requirements.txt
echo ✅ Dependencias instaladas
echo.

REM Verificar FFmpeg
echo 🎬 Verificando FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FFmpeg no encontrado
    echo FFmpeg es necesario para procesar audio/video
    echo Descarga desde https://ffmpeg.org/download.html
) else (
    echo ✅ FFmpeg encontrado
)
echo.

REM Crear directorio de descargas si no existe
if not exist downloads (
    mkdir downloads
    echo ✅ Directorio downloads creado
)

echo.
echo ✨ Instalación completada!
echo.
echo Para ejecutar la aplicación:
echo   1. Activa el entorno virtual: venv\Scripts\activate
echo   2. Ejecuta: python app.py
echo   3. Abre: http://127.0.0.1:5000
echo.

pause



