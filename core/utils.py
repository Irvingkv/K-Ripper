"""
Módulo de utilidades para K-Ripper (detección de FFmpeg y análisis de URLs).
"""
import os
import sys

def obtener_ffmpeg_dir():
    """Retorna la ruta absoluta del directorio ffmpeg si existe ffmpeg.exe, o None."""
    ffmpeg_dir = os.path.join(os.getcwd(), 'ffmpeg')
    ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
    return ffmpeg_dir if os.path.exists(ffmpeg_exe) else None

def verificar_ffmpeg():
    """Valida la presencia de FFmpeg para ejecución en modo CLI o sale con error."""
    ffmpeg_dir = obtener_ffmpeg_dir()
    if not ffmpeg_dir:
        print("❌ Error: No se encontró 'ffmpeg.exe' en la carpeta 'ffmpeg'.")
        print("Por favor descarga FFmpeg y colócalo dentro de la carpeta 'ffmpeg/'.")
        sys.exit(1)
    return ffmpeg_dir

def detectar_tipo_url(url: str) -> str:
    """Identifica la plataforma o tipo de contenido a partir de la URL."""
    if not url or not url.strip():
        return "🔗 Pega un enlace de video, película, red social o flujo .m3u8"
    
    u = url.lower().strip()
    if '.m3u8' in u:
        return "🎬 Flujo Directo de Streaming (HLS .m3u8)"
    if '.mpd' in u:
        return "🎬 Flujo Directo DASH (.mpd)"
    if any(u.endswith(ext) or (ext + '?') in u for ext in ['.mp4', '.mkv', '.webm', '.avi']):
        return "🎥 Archivo de Video Directo"
    if any(d in u for d in ['youtube.com', 'youtu.be']):
        return "🔴 YouTube (Video o Playlist)"
    if 'tiktok.com' in u:
        return "🎵 TikTok (Video / Audio)"
    if 'instagram.com' in u:
        return "📸 Instagram (Reel o Publicación)"
    if any(d in u for d in ['twitter.com', 'x.com']):
        return "🐦 Twitter / X"
    if any(d in u for d in ['facebook.com', 'fb.watch']):
        return "📘 Facebook Video"
    if 'twitch.tv' in u:
        return "🟣 Twitch"
    if 'soundcloud.com' in u:
        return "🟠 SoundCloud"
    if any(h in u for h in ['streamtape', 'dood', 'filemoon', 'voe.', 'mixdrop', 'ok.ru', 'vidplay', 'mp4upload', 'upstream']):
        return "🍿 Servidor de Película / Streaming Externo"
    
    return "🌐 Enlace Web Multimedia"
