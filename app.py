#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 06 - API Flask
Requiere Python 3.10 o superior
"""
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
import os
import re
import requests
import threading
import uuid
import time
import random
import traceback
import warnings
import logging
from datetime import datetime
from yt_dlp import YoutubeDL
from difflib import get_close_matches

# Suprimir advertencias de deprecación de Python y yt-dlp
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*Support for Python version.*')
warnings.filterwarnings('ignore', message='.*deprecated.*')
warnings.filterwarnings('ignore', message='.*Python.*deprecated.*')
warnings.filterwarnings('ignore', message='.*version.*deprecated.*')

# Suprimir advertencias de yt-dlp específicamente
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'
os.environ['YOUTUBE_DL_NO_WARNINGS'] = '1'

# Configurar logging para suprimir advertencias de yt-dlp
yt_dlp_logger = logging.getLogger('yt_dlp')
yt_dlp_logger.setLevel(logging.ERROR)

# Verificar e inicializar yt-dlp correctamente
def verify_yt_dlp():
    """Verifica que yt-dlp esté correctamente instalado y funcional"""
    try:
        # Intentar importar y crear una instancia básica
        from yt_dlp import YoutubeDL
        ydl = YoutubeDL({'quiet': True, 'skip_download': True})
        # Verificar que el módulo extractor existe y es accesible
        try:
            import yt_dlp.extractor
            # Verificar que la función list_extractors existe antes de llamarla
            if hasattr(yt_dlp.extractor, 'list_extractors'):
                try:
                    # Intentar listar extractors disponibles (esto fuerza la carga)
                    _ = yt_dlp.extractor.list_extractors()
                except (ImportError, ModuleNotFoundError) as extractor_error:
                    # Si hay un error específico con extractors, registrar pero continuar
                    error_msg = str(extractor_error)
                    if 'extractor' in error_msg.lower() or 'extractors' in error_msg.lower():
                        print(f"Warning: Problema detectado con módulos de yt-dlp extractors: {extractor_error}")
                        print("Sugerencia: Ejecuta: pip install --upgrade --force-reinstall 'yt-dlp[default]'")
                        # No retornar False aquí, ya que yt-dlp puede funcionar parcialmente
        except (ImportError, ModuleNotFoundError) as e:
            # Si hay un error con extractors, registrar pero continuar
            # yt-dlp puede funcionar sin esto en algunos casos
            error_msg = str(e)
            if 'extractor' in error_msg.lower() or 'extractors' in error_msg.lower():
                print(f"Warning: Problema detectado con módulos de yt-dlp extractors: {e}")
                print("Sugerencia: Ejecuta: pip install --upgrade --force-reinstall 'yt-dlp[default]'")
        return True
    except Exception as e:
        print(f"Error verifying yt-dlp: {e}")
        return False

# Verificar yt-dlp al iniciar la aplicación
if not verify_yt_dlp():
    print("Warning: yt-dlp verification failed, but continuing anyway...")

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configuración de límites
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB máximo por archivo
MAX_FILE_AGE_DAYS = 7  # Días antes de eliminar archivos antiguos

# Almacenamiento de progreso de descargas
download_progress = {}
download_results = {}

def safe_filename(name: str, max_length: int = 100) -> str:
    """Crea un nombre de archivo seguro limitando su longitud"""
    name = re.sub(r"[\\/*?\"<>|:]", "_", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    # Limitar longitud del nombre
    if len(name) > max_length:
        name = name[:max_length].rstrip("_")
    return name or f"video_{int(datetime.now().timestamp())}"

def clean_youtube_url(url: str) -> str:
    """Limpia y convierte la URL de YouTube eliminando parámetros innecesarios que pueden causar problemas"""
    if not url:
        return url
    
    url_lower = url.lower()
    
    # Detectar y convertir diferentes formatos de URLs de YouTube
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        # Extraer video ID de diferentes formatos:
        # - https://www.youtube.com/watch?v=VIDEO_ID
        # - https://youtu.be/VIDEO_ID
        # - https://www.youtube.com/embed/VIDEO_ID
        # - https://m.youtube.com/watch?v=VIDEO_ID
        # - URLs con parámetros adicionales
        
        video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', url)
        if video_id_match:
            video_id = video_id_match.group(1)
            # Construir URL limpia y estándar
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            # Si no se encuentra el ID, intentar extraer de otros formatos
            # Formato youtu.be
            youtu_be_match = re.search(r'youtu\.be/([0-9A-Za-z_-]{11})', url)
            if youtu_be_match:
                video_id = youtu_be_match.group(1)
                return f"https://www.youtube.com/watch?v={video_id}"
    
    # Para otras plataformas, limpiar parámetros innecesarios comunes
    # TikTok, Instagram, etc. pueden tener parámetros que causan problemas
    if "tiktok.com" in url_lower:
        # Eliminar parámetros de tracking comunes
        url = re.sub(r'[?&](lang|q|t|is_from_webapp|is_from_ads)=[^&]*', '', url)
        url = url.rstrip('?&')
    
    return url

def cleanup_old_files():
    """Elimina archivos antiguos del directorio de descargas"""
    try:
        current_time = time.time()
        max_age_seconds = MAX_FILE_AGE_DAYS * 24 * 60 * 60
        
        files = [f for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f)) and not f.startswith('.')]
        deleted_count = 0
        
        for filename in files:
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception:
                    pass
        
        return deleted_count
    except Exception:
        return 0

def find_similar_pokemon(query: str, limit: int = 10) -> list:
    """Busca Pokémon similares al texto ingresado"""
    try:
        # Obtener el total de Pokémon disponibles
        url = "https://pokeapi.co/api/v2/pokemon?limit=1"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return []
        
        # Obtener el count total
        total_count = r.json().get("count", 1000)
        
        # Obtener lista de todos los Pokémon
        url_all = f"https://pokeapi.co/api/v2/pokemon?limit={total_count}"
        r_all = requests.get(url_all, timeout=15)
        if r_all.status_code != 200:
            return []
        
        data = r_all.json()
        all_pokemon_names = [p["name"] for p in data.get("results", [])]
        
        # Buscar coincidencias parciales (que contengan el texto)
        partial_matches = [name for name in all_pokemon_names if query.lower() in name.lower()]
        
        # Buscar coincidencias similares usando difflib
        similar_matches = get_close_matches(query.lower(), all_pokemon_names, n=limit * 2, cutoff=0.3)
        
        # Combinar y eliminar duplicados, priorizando coincidencias parciales
        combined = list(dict.fromkeys(partial_matches + similar_matches))
        
        return combined[:limit]
    except Exception:
        return []

def detect_platform(url: str) -> dict:
    """Detecta la plataforma de la URL para mostrar información visual.
    yt-dlp maneja automáticamente todas las plataformas soportadas."""
    url_lower = url.lower()
    
    # YouTube
    if "youtube.com" in url_lower or "youtu.be" in url_lower or "m.youtube.com" in url_lower:
        return {
            "name": "YouTube",
            "icon": "▶",
            "color": "#FF0000"
        }
    
    # TikTok
    if "tiktok.com" in url_lower or "vm.tiktok.com" in url_lower:
        return {
            "name": "TikTok",
            "icon": "🎵",
            "color": "#000000"
        }
    
    # Instagram
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return {
            "name": "Instagram",
            "icon": "📷",
            "color": "#E4405F"
        }
    
    # Facebook
    if "facebook.com" in url_lower or "fb.com" in url_lower:
        return {
            "name": "Facebook",
            "icon": "👥",
            "color": "#1877F2"
        }
    
    # Twitter/X
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return {
            "name": "Twitter/X",
            "icon": "🐦",
            "color": "#1DA1F2"
        }
    
    # Otras plataformas - yt-dlp las manejará automáticamente
    return {
        "name": "Video",
        "icon": "🎬",
        "color": "#666666"
    }

@app.context_processor
def inject_globals():
    return {"year": datetime.now().year}

@app.get("/")
def index():
    return redirect(url_for("pokemon"))

# -----------------------
# Pregunta 1: Pokémon
# -----------------------
@app.route("/pokemon", methods=["GET", "POST"])
def pokemon():
    context = {"title": "Pokémon", "query": None, "pokemon": None, "error": None, "suggestions": None}
    if request.method == "POST":
        name = (request.form.get("name") or "").strip().lower()
        context["query"] = name
        if not name:
            context["error"] = "Ingresa un nombre."
            return render_template("pokemon.html", **context)

        url = f"https://pokeapi.co/api/v2/pokemon/{name}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                # Buscar Pokémon similares
                suggestions = find_similar_pokemon(name, limit=10)
                if suggestions:
                    context["error"] = f"No se encontró el Pokémon '{name}'. ¿Quisiste decir alguno de estos?"
                    context["suggestions"] = suggestions
                else:
                    context["error"] = f"No se encontró el Pokémon '{name}' y no hay sugerencias disponibles."
                return render_template("pokemon.html", **context)

            data = r.json()
            types = [t["type"]["name"] for t in data.get("types", [])]
            moves = [m["move"]["name"] for m in data.get("moves", [])]
            sprites = {
                "front_default": data.get("sprites", {}).get("front_default"),
                "front_shiny": data.get("sprites", {}).get("front_shiny"),
                "back_default": data.get("sprites", {}).get("back_default"),
                "back_shiny": data.get("sprites", {}).get("back_shiny"),
            }

            context.update({
                "pokemon": {"name": data.get("name", name)},
                "types": types,
                "moves": moves,
                "sprites": sprites,
            })
        except requests.RequestException as e:
            context["error"] = f"Error consultando PokeAPI: {e}"
    return render_template("pokemon.html", **context)

# -----------------------
# Pregunta 2: Descarga video
# -----------------------

def download_video_task(task_id: str, url: str, quality: str):
    """Función que ejecuta la descarga de video en un hilo separado"""
    try:
        # Actualizar estado inicial
        download_progress[task_id] = {
            "status": "starting",
            "percent": 0,
            "message": "Iniciando descarga..."
        }
        
        clean_url = clean_youtube_url(url)
        is_youtube = "youtube.com" in clean_url.lower() or "youtu.be" in clean_url.lower()
        
        # Configurar opciones de descarga
        download_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 3,  # Reintentar hasta 3 veces
            'fragment_retries': 3,
            'noprogress': True,  # No mostrar barra de progreso en consola
            'suppress_warnings': True,  # Suprimir todas las advertencias
        }
        
        # Determinar formato según calidad solicitada
        if quality == "audio":
            download_opts['format'] = 'bestaudio/best'
            download_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality.startswith("height_"):
            # Extraer altura (ej: "height_720" -> 720)
            height = int(quality.replace("height_", ""))
            download_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
        else:
            # "best" o cualquier otro valor usa mejor calidad disponible
            download_opts['format'] = 'best'
        
        if is_youtube:
            # Usar múltiples clientes en orden de preferencia para evitar 403
            # tv y android suelen funcionar mejor que web
            download_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['android', 'tv', 'web'],  # android primero, luego tv, luego web
                }
            }
            # Agregar headers adicionales para evitar bloqueos
            download_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        
        # Callback para actualizar progreso
        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    download_progress[task_id] = {
                        "status": "downloading",
                        "percent": min(percent, 99),
                        "message": f"Descargando... {d.get('_percent_str', '')}"
                    }
                elif '_percent_str' in d:
                    download_progress[task_id] = {
                        "status": "downloading",
                        "percent": 50,  # Estimación si no hay total_bytes
                        "message": f"Descargando... {d['_percent_str']}"
                    }
            elif d['status'] == 'finished':
                download_progress[task_id] = {
                    "status": "processing",
                    "percent": 95,
                    "message": "Procesando archivo..."
                }
        
        download_opts['progress_hooks'] = [progress_hook]
        
        # Extraer información del video primero
        info_opts = download_opts.copy()
        info_opts['skip_download'] = True
        
        video_title = 'video'
        video_uploader = ''
        video_duration = 0
        video_thumbnail = ''
        duration_formatted = ""
        
        try:
            with YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                video_title = info.get('title', 'video')
                video_uploader = info.get('uploader', '')
                video_duration = info.get('duration', 0)
                video_thumbnail = info.get('thumbnail', '')
                
                # Formatear duración
                if video_duration:
                    hours = video_duration // 3600
                    minutes = (video_duration % 3600) // 60
                    seconds = video_duration % 60
                    if hours > 0:
                        duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_formatted = f"{minutes}:{seconds:02d}"
        except (ImportError, ModuleNotFoundError) as import_error:
            # Manejar errores de importación de módulos de yt-dlp
            error_msg = str(import_error)
            if 'extractor' in error_msg.lower() or 'extractors' in error_msg.lower():
                print(f"Error: Problema con módulos de yt-dlp. Reinstala yt-dlp: pip install --upgrade --force-reinstall yt-dlp[default]")
                raise Exception("Error de configuración de yt-dlp. Por favor, reinstala yt-dlp ejecutando: pip install --upgrade --force-reinstall 'yt-dlp[default]'")
            raise
        except Exception as info_error:
            # Si falla obtener info, continuar con valores por defecto
            # pero registrar el error
            print(f"Warning: No se pudo obtener información del video: {info_error}")
        
        # Realizar descarga con manejo de errores mejorado
        download_success = False
        last_error = None
        
        # Intentar descarga con diferentes estrategias si falla
        for attempt in range(2):
            try:
                with YoutubeDL(download_opts) as ydl:
                    ydl.download([clean_url])
                download_success = True
                break
            except (ImportError, ModuleNotFoundError) as import_error:
                # Manejar errores de importación de módulos de yt-dlp
                error_msg = str(import_error)
                if 'extractor' in error_msg.lower() or 'extractors' in error_msg.lower():
                    raise Exception("Error de configuración de yt-dlp. Por favor, reinstala yt-dlp ejecutando: pip install --upgrade --force-reinstall 'yt-dlp[default]'")
                raise
            except Exception as download_error:
                last_error = download_error
                error_str = str(download_error).lower()
                
                # Si es error 403 y es YouTube, intentar con cliente diferente
                if ("403" in error_str or "forbidden" in error_str) and is_youtube and attempt == 0:
                    # Cambiar a cliente web como último recurso
                    download_opts['extractor_args'] = {
                        'youtube': {
                            'player_client': ['web'],
                        }
                    }
                    download_progress[task_id] = {
                        "status": "downloading",
                        "percent": 10,
                        "message": "Reintentando con configuración alternativa..."
                    }
                    continue
                else:
                    # Si no es 403 o ya intentamos, lanzar el error
                    raise download_error
        
        if not download_success:
            raise last_error if last_error else Exception("Error desconocido al descargar")
        
        # Buscar el archivo descargado
        downloaded_files = [f for f in os.listdir(DOWNLOAD_DIR) 
                           if os.path.isfile(os.path.join(DOWNLOAD_DIR, f)) 
                           and not f.startswith('.')]
        
        # Encontrar el archivo más reciente (probablemente el que acabamos de descargar)
        if downloaded_files:
            downloaded_files.sort(key=lambda f: os.path.getmtime(os.path.join(DOWNLOAD_DIR, f)), reverse=True)
            filename = downloaded_files[0]
        else:
            raise Exception("No se encontró el archivo descargado")
        
        # Actualizar estado final
        download_progress[task_id] = {
            "status": "completed",
            "percent": 100,
            "message": "Descarga completada"
        }
        
        download_results[task_id] = {
            "filename": filename,
            "video_info": {
                "title": video_title,
                "uploader": video_uploader,
                "duration_formatted": duration_formatted,
                "thumbnail": video_thumbnail
            },
            "platform": detect_platform(url)
        }
        
    except Exception as e:
        error_str = str(e).lower()
        error_message = str(e)
        
        # Manejo específico de errores comunes
        if "403" in error_str or "forbidden" in error_str:
            error_message = "Error 403: Acceso denegado. El servidor bloqueó la descarga. Esto puede deberse a restricciones de la plataforma. Intenta más tarde o con otro video."
        elif "timeout" in error_str or "timed out" in error_str:
            error_message = "Timeout al descargar. El servidor no respondió a tiempo. Intenta nuevamente."
        elif "private video" in error_str or "sign in" in error_str or "private" in error_str:
            error_message = "Este video es privado o requiere autenticación."
        elif "video unavailable" in error_str or "unavailable" in error_str or "does not exist" in error_str:
            error_message = "Este video no está disponible o ha sido eliminado."
        elif "age-restricted" in error_str or "age restricted" in error_str:
            error_message = "Este video tiene restricción de edad."
        elif "region" in error_str or "not available in your country" in error_str:
            error_message = "Este video no está disponible en tu región."
        elif "http error" in error_str:
            # Extraer código de error HTTP si está disponible
            http_code_match = re.search(r'http error (\d+)', error_str)
            if http_code_match:
                http_code = http_code_match.group(1)
                if http_code == "403":
                    error_message = "Error 403: Acceso denegado. La plataforma bloqueó la descarga. Intenta más tarde."
                elif http_code == "429":
                    error_message = "Error 429: Demasiadas solicitudes. Espera unos minutos antes de intentar nuevamente."
                else:
                    error_message = f"Error HTTP {http_code}: No se pudo descargar el video."
            else:
                error_message = "Error de conexión HTTP. Verifica tu conexión a internet e intenta nuevamente."
        
        # Log del error completo para debugging
        print(f"Error en download_video_task para {url}:")
        print(traceback.format_exc())
        
        download_progress[task_id] = {
            "status": "error",
            "percent": 0,
            "message": error_message
        }
        
        download_results[task_id] = {
            "error": error_message
        }

@app.route("/api/detect-platform", methods=["POST"])
def api_detect_platform():
    """Detecta la plataforma de una URL"""
    try:
        data = request.get_json()
        url = (data.get("url") or "").strip()
        
        if not url:
            return jsonify({"error": "URL vacía"}), 400
        
        if not url.startswith("http"):
            return jsonify({"error": "URL inválida"}), 400
        
        platform = detect_platform(url)
        return jsonify(platform)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/formats/list", methods=["POST"])
def api_list_formats():
    """Obtiene la lista de formatos disponibles para una URL"""
    data = request.get_json()
    url = (data.get("url") or "").strip()
    
    if not url:
        return jsonify({"error": "URL vacía"}), 400
    
    if not url.startswith("http"):
        return jsonify({"error": "URL inválida"}), 400
    
    try:
        clean_url = clean_youtube_url(url)
        is_youtube = "youtube.com" in clean_url.lower() or "youtu.be" in clean_url.lower()
        
        list_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'skip_download': True,  # No intentar descargar, solo extraer información
            'noprogress': True,  # No mostrar barra de progreso en consola
            'suppress_warnings': True,  # Suprimir todas las advertencias
            # NO especificar 'format' - queremos listar todos los formatos disponibles
        }
        
        if is_youtube:
            # Usar clientes que no requieren PO Token para listar formatos
            list_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['tv', 'android', 'web'],  # tv y android no requieren PO Token
                }
            }
        
        info = None
        formats = []
        
        # Intentar extraer información con manejo robusto de errores
        # Usamos extract_info sin formato para obtener solo la lista de formatos disponibles
        try:
            with YoutubeDL(list_opts) as ydl:
                # Extraer información sin formato específico - esto lista todos los formatos disponibles
                # El parámetro download=False ya evita la descarga, pero skip_download es más explícito
                info = ydl.extract_info(clean_url, download=False)
                formats = info.get('formats', []) if info else []
        except (ImportError, ModuleNotFoundError) as import_error:
            # Manejar errores de importación de módulos de yt-dlp
            error_msg = str(import_error)
            if 'extractor' in error_msg.lower() or 'extractors' in error_msg.lower():
                return jsonify({
                    "error": "Error de configuración de yt-dlp",
                    "details": "Por favor, reinstala yt-dlp ejecutando: pip install --upgrade --force-reinstall 'yt-dlp[default]'"
                }), 500
            raise
        except Exception as extract_error:
            error_str = str(extract_error).lower()
            
            # Si el error es específicamente sobre formatos no disponibles, 
            # esto puede ser un problema de validación, no necesariamente un error fatal
            if "requested format is not available" in error_str or "format" in error_str:
                # Intentar con URL original si es diferente
                if clean_url != url:
                    try:
                        with YoutubeDL(list_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            formats = info.get('formats', []) if info else []
                            # Si funciona con URL original, continuar
                            if formats:
                                pass  # Continuar con el procesamiento
                            else:
                                raise extract_error
                    except Exception:
                        # Si ambas fallan, devolver respuesta parcial indicando que los formatos no están disponibles
                        # pero la descarga puede continuar
                        return jsonify({
                            'formats': [
                                {'value': 'best', 'label': 'Mejor disponible', 'height': None},
                                {'value': 'audio', 'label': 'Solo audio (MP3)', 'height': None}
                            ],
                            'available_heights': [],
                            'platform': detect_platform(url),
                            'warning': 'No se pudieron obtener los formatos específicos. Usa "Mejor disponible" para descargar.'
                        }), 200
                else:
                    # Devolver respuesta parcial en lugar de error 500
                    return jsonify({
                        'formats': [
                            {'value': 'best', 'label': 'Mejor disponible', 'height': None},
                            {'value': 'audio', 'label': 'Solo audio (MP3)', 'height': None}
                        ],
                        'available_heights': [],
                        'platform': detect_platform(url),
                        'warning': 'No se pudieron obtener los formatos específicos. Usa "Mejor disponible" para descargar.'
                    }), 200
            else:
                # Para otros errores, intentar con URL original
                if clean_url != url:
                    try:
                        with YoutubeDL(list_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                            formats = info.get('formats', []) if info else []
                    except Exception:
                        raise extract_error
                else:
                    raise extract_error
        
        # Si no hay formatos, intentar obtener del objeto info directamente
        if not formats and info:
            formats = info.get('formats', [])
        
        # Procesar formatos para extraer información útil
        processed_formats = []
        seen_heights = set()
        
        # Agrupar por altura y extraer información
        for fmt in formats:
            height = fmt.get('height')
            if height and isinstance(height, (int, float)):
                height = int(height)
                if height not in seen_heights:
                    seen_heights.add(height)
                    ext = fmt.get('ext', 'unknown')
                    vcodec = fmt.get('vcodec', 'unknown')
                    acodec = fmt.get('acodec', 'none')
                    has_video = vcodec != 'none' and vcodec != 'unknown'
                    has_audio = acodec != 'none' and acodec != 'unknown'
                    
                    processed_formats.append({
                        'height': height,
                        'ext': ext,
                        'has_video': has_video,
                        'has_audio': has_audio,
                        'format_id': fmt.get('format_id', ''),
                        'format_note': fmt.get('format_note', ''),
                        'filesize': fmt.get('filesize'),
                    })
        
        # Ordenar por altura descendente
        processed_formats.sort(key=lambda x: x['height'], reverse=True)
        
        # Agregar opciones especiales
        special_formats = [
            {'value': 'best', 'label': 'Mejor disponible', 'height': None},
            {'value': 'audio', 'label': 'Solo audio (MP3)', 'height': None},
        ]
        
        # Agregar formatos de video disponibles
        video_formats = [f for f in processed_formats if f['has_video']]
        for fmt in video_formats:
            label = f"{fmt['height']}p"
            if fmt['ext']:
                label += f" ({fmt['ext'].upper()})"
            special_formats.append({
                'value': f"height_{fmt['height']}",
                'label': label,
                'height': fmt['height']
            })
        
        return jsonify({
            'formats': special_formats,
            'available_heights': sorted(seen_heights, reverse=True),
            'platform': detect_platform(url)
        })
        
    except Exception as e:
        error_str = str(e).lower()
        # Log del error para debugging (en producción podrías usar logging)
        import traceback
        print(f"Error en api_list_formats: {str(e)}")
        print(traceback.format_exc())
        
        if "timeout" in error_str or "timed out" in error_str:
            return jsonify({"error": "Timeout al obtener formatos. El servidor no respondió a tiempo."}), 500
        elif "private video" in error_str or "sign in" in error_str or "private" in error_str:
            return jsonify({"error": "Este video es privado o requiere autenticación."}), 400
        elif "video unavailable" in error_str or "unavailable" in error_str or "does not exist" in error_str:
            return jsonify({"error": "Este video no está disponible."}), 400
        elif "age-restricted" in error_str or "age restricted" in error_str:
            return jsonify({"error": "Este video tiene restricción de edad."}), 400
        elif "region" in error_str or "not available in your country" in error_str:
            return jsonify({"error": "Este video no está disponible en tu región."}), 400
        else:
            # Devolver un error más descriptivo
            return jsonify({
                "error": f"Error al obtener formatos: {str(e)}",
                "details": "No se pudieron obtener los formatos disponibles. Intenta descargar directamente con 'Mejor disponible'."
            }), 500

@app.route("/api/download/start", methods=["POST"])
def api_download_start():
    """Inicia una descarga de video y devuelve un task_id"""
    try:
        data = request.get_json()
        url = (data.get("url") or "").strip()
        quality = (data.get("quality") or "best").strip()
        
        if not url:
            return jsonify({"error": "URL vacía"}), 400
        
        if not url.startswith("http"):
            return jsonify({"error": "URL inválida"}), 400
        
        # Generar task_id único
        task_id = str(uuid.uuid4())
        
        # Inicializar progreso
        download_progress[task_id] = {
            "status": "starting",
            "percent": 0,
            "message": "Iniciando descarga..."
        }
        
        # Iniciar descarga en un hilo separado
        thread = threading.Thread(target=download_video_task, args=(task_id, url, quality))
        thread.daemon = True
        thread.start()
        
        return jsonify({"task_id": task_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/progress/<task_id>")
def api_download_progress(task_id):
    """Consulta el progreso de una descarga"""
    try:
        if task_id not in download_progress:
            return jsonify({"error": "Task ID no encontrado"}), 404
        
        progress = download_progress[task_id].copy()
        
        # Si la descarga está completada o con error, incluir resultados
        if progress["status"] in ["completed", "error"]:
            if task_id in download_results:
                progress["result"] = download_results[task_id]
        
        return jsonify(progress)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["GET"])
def download():
    """Página de descarga de videos"""
    return render_template("download.html", title="Descargar Video")

@app.route("/downloads/<filename>")
def serve_download(filename):
    """Sirve archivos descargados"""
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/downloads/list")
def list_downloads():
    """Lista todos los archivos descargados disponibles"""
    try:
        files = [f for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f)) and not f.startswith('.')]
        
        downloads_list = []
        for filename in files:
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            
            downloads_list.append({
                "filename": filename,
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(file_mtime).isoformat(),
                "modified_readable": datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "url": url_for("serve_download", filename=filename)
            })
        
        # Ordenar por fecha de modificación (más recientes primero)
        downloads_list.sort(key=lambda x: x["modified"], reverse=True)
        
        return jsonify({
            "downloads": downloads_list,
            "count": len(downloads_list)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.before_request
def before_request():
    """Limpia archivos antiguos antes de cada request (solo ocasionalmente para no afectar performance)"""
    # Solo limpiar 1 de cada 100 requests para no afectar performance
    if random.randint(1, 100) == 1:
        cleanup_old_files()

if __name__ == "__main__":
    # Suprimir advertencias adicionales al iniciar
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    # Ejecuta: python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)

