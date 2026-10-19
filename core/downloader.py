"""
Motor de descargas multimedia para K-Ripper utilizando yt-dlp y ffmpeg.
"""
import os
import sys
import re
import yt_dlp

class BotStatusLogger:
    """Captura mensajes de yt-dlp para identificar bloqueos de seguridad o cookies bloqueadas."""
    def __init__(self):
        self.bot_bloqueo = False
        self.cookie_lock = False
    
    def debug(self, msg):
        pass
        
    def warning(self, msg):
        print(msg)
        
    def error(self, msg):
        m = msg.lower()
        if 'sign in' in m or 'bot' in m:
            self.bot_bloqueo = True
        elif any(k in m for k in ['cookie', 'database', 'locked', 'could not copy']):
            self.cookie_lock = True
        else:
            print(msg)

def crear_progress_hook(queue_obj):
    """Crea y retorna un hook de progreso de yt-dlp conectado a una cola de eventos."""
    def hook(d):
        status = d.get('status')
        filename = d.get('filename', '')
        title_name, _ = os.path.splitext(os.path.basename(filename))

        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percent = (downloaded / total * 100) if total > 0 else 0.0
            
            queue_obj.put({
                'type': 'progress',
                'percent': percent,
                'speed': d.get('_speed_str', 'N/A').strip(),
                'eta': d.get('_eta_str', 'N/A').strip(),
                'title': title_name
            })
        elif status == 'finished':
            queue_obj.put({
                'type': 'finished_video',
                'title': title_name
            })
    return hook

def descargar_multimedia(url: str, ffmpeg_dir: str, formato: str = 'video', 
                         progress_hook=None, custom_name: str = ""):
    """
    Descarga contenido multimedia de YouTube, redes sociales o transmisiones directas (.m3u8).
    """
    url = url.strip()
    is_youtube = ('youtube.com' in url.lower() or 'youtu.be' in url.lower())
    
    os.makedirs('musica', exist_ok=True)
    os.makedirs('videos', exist_ok=True)
    
    if custom_name and custom_name.strip():
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', custom_name.strip())
        outtmpl_audio = f'musica/{safe_name}.%(ext)s'
        outtmpl_video = f'videos/{safe_name}.%(ext)s'
    else:
        outtmpl_audio = 'musica/%(playlist_title&{}/|)s%(title,id)s.%(ext)s'
        outtmpl_video = 'videos/%(playlist_title&{}/|)s%(title,id)s.%(ext)s'

    opciones_base = {
        'ffmpeg_location': ffmpeg_dir,
        'ignoreerrors': True,
        'no_warnings': False,
        'quiet': False,
        'no_color': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
    }
    
    if is_youtube:
        opciones_base['extractor_args'] = {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        }
    
    if progress_hook:
        opciones_base['progress_hooks'] = [progress_hook]
        
    if formato == 'audio':
        opciones_base.update({
            'format': 'bestaudio/best',
            'outtmpl': outtmpl_audio,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
    else:
        opciones_base.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
            'outtmpl': outtmpl_video,
            'merge_output_format': 'mp4'
        })
    
    icono = "🎵" if formato == "audio" else "🎬"
    carpeta = "musica/" if formato == "audio" else "videos/"
    print(f"\n{icono} Iniciando descarga en formato {formato.upper()}...")
    print(f"📂 Carpeta de destino: {carpeta}\n")
    
    if is_youtube:
        estrategias = [
            (None, "Sin cookies"),
            (('edge',), "Edge"),
            (('firefox',), "Firefox"),
            (('brave',), "Brave"),
            (('opera',), "Opera"),
            (('chrome',), "Chrome")
        ]
    else:
        estrategias = [
            (None, "Conexión directa"),
            (('edge',), "Navegador Edge"),
            (('chrome',), "Navegador Chrome"),
            (('firefox',), "Navegador Firefox")
        ]
    
    descargado = False
    ultimo_fallo_fue_bot = False
    
    for config_cookies, nombre_estrategia in estrategias:
        opciones_actuales = dict(opciones_base)
        
        if config_cookies:
            opciones_actuales['cookiesfrombrowser'] = config_cookies
            print(f"🔄 Reintentando con sesión / cookies de {nombre_estrategia}...")
            
        logger = BotStatusLogger()
        opciones_actuales['logger'] = logger
        
        try:
            with yt_dlp.YoutubeDL(opciones_actuales) as ydl:
                resultado = ydl.download([url])
                
                if (not logger.bot_bloqueo and not logger.cookie_lock) and (resultado == 0 or resultado is None):
                    print("\n✅ Descarga completada exitosamente.")
                    descargado = True
                    break
                elif logger.bot_bloqueo:
                    ultimo_fallo_fue_bot = True
                elif logger.cookie_lock:
                    print(f"⚠️ Las cookies de {nombre_estrategia} estaban ocupadas (navegador abierto). Saltando...")
                    continue
                elif resultado == 1 and not logger.bot_bloqueo and config_cookies is None:
                    print("\n✅ Proceso finalizado.")
                    descargado = True
                    break
                    
        except KeyboardInterrupt:
            print("\n❌ Cancelado por el usuario.")
            sys.exit(1)
        except Exception as e:
            print(f"Aviso: {e}")
            
    if not descargado:
        if ultimo_fallo_fue_bot:
            print("\n❌ Bloqueo de seguridad detectado en el sitio.")
            print("💡 SOLUCIÓN: Cierra completamente navegadores como Chrome/Edge/Firefox para permitir leer las sesiones.")
        else:
            print("\n❌ No se pudo completar la descarga. Verifica que el enlace siga activo y sea accesible.")
