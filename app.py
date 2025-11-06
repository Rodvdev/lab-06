from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
import re
import requests
from datetime import datetime
from yt_dlp import YoutubeDL
from difflib import get_close_matches

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def safe_filename(name: str) -> str:
    name = re.sub(r"[\\/*?\"<>|:]", "_", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    return name or f"video_{int(datetime.now().timestamp())}"

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
    """Detecta la plataforma de la URL (YouTube, TikTok, Instagram)"""
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
    
    # Plataforma desconocida
    return {
        "name": "Desconocida",
        "icon": "🔗",
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
@app.route("/download", methods=["GET", "POST"])
def download():
    context = {
        "title": "Descargar Video", 
        "file_ready": False, 
        "filename": None, 
        "error": None,
        "platform": None,
        "video_info": None,
        "url": None
    }
    
    if request.method == "POST":
        url = (request.form.get("url") or "").strip()
        quality = (request.form.get("quality") or "best").strip()
        context["url"] = url

        if not url.startswith("http"):
            context["error"] = "Ingresa una URL válida (https://...)."
            return render_template("download.html", **context)

        # Detectar plataforma
        platform = detect_platform(url)
        context["platform"] = platform

        # Validar que sea una plataforma soportada
        if platform["name"] == "Desconocida":
            context["error"] = f"Plataforma no reconocida. Por favor, ingresa una URL de YouTube, TikTok o Instagram."
            return render_template("download.html", **context)

        # Selección de formato
        if quality == "best":
            ydl_format = "bestvideo+bestaudio/best"
        elif quality == "720":
            ydl_format = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif quality == "480":
            ydl_format = "bestvideo[height<=480]+bestaudio/best[height<=480]"
        elif quality == "audio":
            ydl_format = "bestaudio/best"
        else:
            ydl_format = "bestvideo+bestaudio/best"

        # Nombre base seguro
        base = safe_filename("descarga")
        outtmpl = os.path.join(DOWNLOAD_DIR, f"{base}-%(title).80s.%(ext)s")

        ydl_opts = {
            "outtmpl": outtmpl,
            "format": ydl_format,
            "noplaylist": True,
            "ignoreerrors": False,
            "quiet": False,
            "no_warnings": False,
            "merge_output_format": "mp4",  # si hay que unir audio+video
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"} if quality != "audio" else
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                # Primero obtener información sin descargar
                info = ydl.extract_info(url, download=False)
                
                # Guardar información del video
                video_title = info.get("title", "Sin título")
                video_duration = info.get("duration", 0)
                video_uploader = info.get("uploader", "Desconocido")
                video_thumbnail = info.get("thumbnail")
                
                # Formatear duración
                if video_duration:
                    minutes = video_duration // 60
                    seconds = video_duration % 60
                    duration_formatted = f"{minutes}:{seconds:02d}"
                else:
                    duration_formatted = None
                
                context["video_info"] = {
                    "title": video_title,
                    "duration": video_duration,
                    "duration_formatted": duration_formatted,
                    "uploader": video_uploader,
                    "thumbnail": video_thumbnail
                }
                
                # Ahora descargar
                ydl.download([url])
                
                # Obtener el nombre del archivo descargado
                final_path = ydl.prepare_filename(info)
                
                # Si el archivo tiene extensión diferente, buscarlo
                if not os.path.exists(final_path):
                    # Buscar archivos recientes en downloads
                    files = os.listdir(DOWNLOAD_DIR)
                    if files:
                        # Ordenar por fecha de modificación
                        files_with_path = [(os.path.join(DOWNLOAD_DIR, f), os.path.getmtime(os.path.join(DOWNLOAD_DIR, f))) for f in files]
                        files_with_path.sort(key=lambda x: x[1], reverse=True)
                        final_path = files_with_path[0][0]

            filename = os.path.basename(final_path)
            context.update({"file_ready": True, "filename": filename})
        except Exception as e:
            error_msg = str(e)
            # Mensajes de error más amigables según la plataforma
            if platform["name"] == "YouTube":
                if "Private video" in error_msg or "Sign in" in error_msg:
                    context["error"] = "Este video de YouTube es privado o requiere autenticación."
                elif "Video unavailable" in error_msg:
                    context["error"] = "Este video de YouTube no está disponible."
                else:
                    context["error"] = f"Error al descargar de YouTube: {error_msg}"
            elif platform["name"] == "TikTok":
                context["error"] = f"Error al descargar de TikTok: {error_msg}"
            elif platform["name"] == "Instagram":
                context["error"] = f"Error al descargar de Instagram: {error_msg}"
            else:
                context["error"] = f"No se pudo descargar: {error_msg}"

    return render_template("download.html", **context)

@app.get("/downloads/<path:filename>")
def serve_download(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    # Ejecuta: python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)

