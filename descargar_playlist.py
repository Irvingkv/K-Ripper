import os
import sys
import re
import queue
import threading
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp

def obtener_ffmpeg_dir():
    """Verifica si ffmpeg existe y retorna su ruta, o None si no existe"""
    ffmpeg_dir = os.path.join(os.getcwd(), 'ffmpeg')
    ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
    if os.path.exists(ffmpeg_exe):
        return ffmpeg_dir
    return None

def verificar_ffmpeg():
    """Verifica que ffmpeg existe en el directorio especificado (usado para CLI)"""
    ffmpeg_dir = obtener_ffmpeg_dir()
    if not ffmpeg_dir:
        print(f"❌ Error: No se encontró ffmpeg.exe en la carpeta 'ffmpeg'")
        print("Por favor, descarga ffmpeg y colócalo en la carpeta 'ffmpeg'")
        sys.exit(1)
    return ffmpeg_dir

def detectar_tipo_url(url):
    """Identifica la plataforma o tipo de contenido según la URL"""
    if not url or not url.strip():
        return "🔗 Pega un enlace de video, película, red social o flujo .m3u8"
    
    u = url.lower().strip()
    if '.m3u8' in u:
        return "🎬 Flujo Directo de Streaming (HLS .m3u8) - Ideal para películas"
    if '.mpd' in u:
        return "🎬 Flujo Directo DASH (.mpd)"
    if any(u.endswith(ext) or (ext + '?') in u for ext in ['.mp4', '.mkv', '.webm', '.avi']):
        return "🎥 Archivo de Video Directo"
    if any(domain in u for domain in ['youtube.com', 'youtu.be']):
        return "🔴 YouTube (Video o Playlist)"
    if 'tiktok.com' in u:
        return "🎵 TikTok (Video / Audio)"
    if 'instagram.com' in u:
        return "📸 Instagram (Reel o Publicación)"
    if any(domain in u for domain in ['twitter.com', 'x.com']):
        return "🐦 Twitter / X"
    if any(domain in u for domain in ['facebook.com', 'fb.watch']):
        return "📘 Facebook Video"
    if 'twitch.tv' in u:
        return "🟣 Twitch (Clip o Transmisión)"
    if 'soundcloud.com' in u:
        return "🟠 SoundCloud"
    if any(host in u for host in ['streamtape', 'dood', 'filemoon', 'voe.', 'mixdrop', 'ok.ru', 'vidplay', 'mp4upload', 'upstream']):
        return "🍿 Servidor de Película / Streaming Externo"
    
    return "🌐 Enlace Web Multimedia / Universal"

class BotStatusLogger(object):
    def __init__(self):
        self.bot_bloqueo = False
        self.cookie_lock = False
    
    def debug(self, msg):
        print(msg)
        
    def warning(self, msg):
        print(msg)
        
    def error(self, msg):
        m = msg.lower()
        if 'sign in' in m or 'bot' in m:
            self.bot_bloqueo = True
        elif 'cookie' in m or 'database' in m or 'locked' in m or 'could not copy' in m:
            self.cookie_lock = True
        else:
            print(msg)

def descargar_multimedia(url, ffmpeg_dir, formato='video', progress_hook=None, custom_name=""):
    """
    Descarga videos, playlists, redes sociales o transmisiones directas (.m3u8)
    usando yt-dlp y ffmpeg con evasión inteligente de bloqueos.
    """
    url = url.strip()
    is_youtube = ('youtube.com' in url.lower() or 'youtu.be' in url.lower())
    
    # Asegurar que existan carpetas destino
    os.makedirs('musica', exist_ok=True)
    os.makedirs('videos', exist_ok=True)
    
    # Configurar el nombre de archivo / ruta de salida
    if custom_name and custom_name.strip():
        # Limpiar caracteres prohibidos en nombres de archivo de Windows
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', custom_name.strip())
        outtmpl_audio = f'musica/{safe_name}.%(ext)s'
        outtmpl_video = f'videos/{safe_name}.%(ext)s'
    else:
        # Si tiene playlist la agrupa en subcarpeta; si es video suelto, va directo
        outtmpl_audio = 'musica/%(playlist_title&{}/|)s%(title,id)s.%(ext)s'
        outtmpl_video = 'videos/%(playlist_title&{}/|)s%(title,id)s.%(ext)s'

    # OPCIONES BASE CON USER-AGENT MODERNO
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
    
    # Extractor específico para YouTube
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
    else:  # video
        opciones_base.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
            'outtmpl': outtmpl_video,
            'merge_output_format': 'mp4'
        })
    
    icono = "🎵" if formato == "audio" else "🎬"
    carpeta = "musica/" if formato == "audio" else "videos/"
    print(f"\n{icono} Iniciando descarga en formato {formato.upper()}...")
    print(f"📂 Carpeta de destino: {carpeta}\n")
    
    # Estrategias de conexión
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

class ConsoleRedirector:
    def __init__(self, queue):
        self.queue = queue

    def write(self, string):
        if "[download]" in string and "%" in string:
            return
        cleaned = string.replace('\r', '')
        if cleaned:
            self.queue.put(cleaned)

    def flush(self):
        pass

def crear_progress_hook(queue_obj):
    def hook(d):
        if d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            
            percent = 0.0
            if total > 0:
                percent = (downloaded / total) * 100
                
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            
            filename = d.get('filename', '')
            title = os.path.basename(filename)
            title_name, _ = os.path.splitext(title)
            
            queue_obj.put({
                'type': 'progress',
                'percent': percent,
                'speed': speed,
                'eta': eta,
                'title': title_name
            })
        elif d.get('status') == 'finished':
            filename = d.get('filename', '')
            title = os.path.basename(filename)
            title_name, _ = os.path.splitext(title)
            queue_obj.put({
                'type': 'finished_video',
                'title': title_name
            })
    return hook

class DownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("K-Ripper - Universal Media & Movie Downloader")
        self.root.geometry("740x740")
        self.root.configure(bg="#0F172A")
        self.root.minsize(680, 650)
        
        self.formato = "video"  # Por defecto Video (ideal para películas y clips)
        self.ffmpeg_dir = obtener_ffmpeg_dir()
        self.download_queue = queue.Queue()
        self.is_downloading = False
        
        self.setup_styles()
        self.build_ui()
        self.check_ffmpeg()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.check_queue)
        
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure("Vertical.TScrollbar", 
                             gripcount=0, 
                             background="#334155", 
                             darkcolor="#334155", 
                             lightcolor="#334155", 
                             troughcolor="#0F172A", 
                             bordercolor="#0F172A",
                             arrowcolor="#94A3B8")
        self.style.map("Vertical.TScrollbar",
                       background=[('active', '#475569'), ('pressed', '#1E293B')])
                       
        self.style.configure("Horizontal.TProgressbar",
                             thickness=8,
                             troughcolor="#0F172A",
                             background="#6366F1",
                             bordercolor="#1E293B",
                             lightcolor="#6366F1",
                             darkcolor="#6366F1")
                             
    def build_ui(self):
        main_frame = tk.Frame(self.root, bg="#0F172A")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # 1. Cabecera
        header_frame = tk.Frame(main_frame, bg="#0F172A")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(header_frame, text="K-RIPPER DOWNLOADER", 
                               font=("Segoe UI", 17, "bold"), fg="#F8FAFC", bg="#0F172A")
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(header_frame, 
                                  text="Descarga de Películas (.m3u8), YouTube, TikTok, Instagram, Twitter y Servidores de Video", 
                                  font=("Segoe UI", 9), fg="#94A3B8", bg="#0F172A")
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # 2. Tarjeta de Configuración
        card = tk.Frame(main_frame, bg="#1E293B", bd=1, highlightbackground="#334155", highlightcolor="#334155")
        card.pack(fill="x", pady=(0, 12))
        
        card_inner = tk.Frame(card, bg="#1E293B")
        card_inner.pack(fill="x", padx=20, pady=16)
        
        # Entrada de Enlace
        lbl_link = tk.Label(card_inner, text="Enlace del Video, Película (.m3u8) o Playlist:", 
                            font=("Segoe UI", 10, "bold"), bg="#1E293B", fg="#F8FAFC")
        lbl_link.pack(anchor="w", pady=(0, 4))
        
        self.entry_border = tk.Frame(card_inner, bg="#334155", bd=1)
        self.entry_border.pack(fill="x", pady=(0, 4))
        
        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self.on_url_change)
        
        self.entry_link = tk.Entry(self.entry_border, textvariable=self.url_var,
                                   bg="#0F172A", fg="#F8FAFC", 
                                   insertbackground="#F8FAFC", bd=0, relief="flat",
                                   font=("Segoe UI", 10))
        self.entry_link.pack(fill="x", padx=10, pady=7)
        self.entry_link.bind("<FocusIn>", lambda e: self.entry_border.configure(bg="#6366F1"))
        self.entry_link.bind("<FocusOut>", lambda e: self.entry_border.configure(bg="#334155"))
        
        # Badge de detección de plataforma
        self.lbl_detector = tk.Label(card_inner, text="🔗 Pega un enlace de video, película, red social o flujo .m3u8",
                                     font=("Segoe UI", 8, "italic"), bg="#1E293B", fg="#38BDF8")
        self.lbl_detector.pack(anchor="w", pady=(0, 10))
        
        # Campo opcional: Nombre de Película / Archivo
        lbl_name = tk.Label(card_inner, text="Nombre del Archivo o Película (Opcional):", 
                            font=("Segoe UI", 9, "bold"), bg="#1E293B", fg="#CBD5E1")
        lbl_name.pack(anchor="w", pady=(0, 3))
        
        self.entry_name_border = tk.Frame(card_inner, bg="#334155", bd=1)
        self.entry_name_border.pack(fill="x", pady=(0, 12))
        
        self.entry_name = tk.Entry(self.entry_name_border, bg="#0F172A", fg="#F8FAFC",
                                   insertbackground="#F8FAFC", bd=0, relief="flat",
                                   font=("Segoe UI", 9))
        self.entry_name.pack(fill="x", padx=10, pady=6)
        self.entry_name.bind("<FocusIn>", lambda e: self.entry_name_border.configure(bg="#6366F1"))
        self.entry_name.bind("<FocusOut>", lambda e: self.entry_name_border.configure(bg="#334155"))
        
        # Selección de Formato
        lbl_format = tk.Label(card_inner, text="Formato de Descarga:", 
                              font=("Segoe UI", 9, "bold"), bg="#1E293B", fg="#CBD5E1")
        lbl_format.pack(anchor="w", pady=(0, 4))
        
        format_selector_frame = tk.Frame(card_inner, bg="#0F172A", bd=1, highlightbackground="#334155", highlightcolor="#334155")
        format_selector_frame.pack(fill="x", pady=(0, 15))
        
        self.btn_video = tk.Button(format_selector_frame, text="🎬 Video (MP4) - Película / Clip", 
                                   bg="#6366F1", fg="#F8FAFC", 
                                   activebackground="#4F46E5", activeforeground="#F8FAFC",
                                   font=("Segoe UI", 9, "bold"), bd=0, relief="flat",
                                   pady=7, cursor="hand2", command=self.set_format_video)
        self.btn_video.pack(side="left", expand=True, fill="x")
        
        self.btn_audio = tk.Button(format_selector_frame, text="🎵 Audio (MP3)", 
                                   bg="#0F172A", fg="#94A3B8", 
                                   activebackground="#1E293B", activeforeground="#94A3B8",
                                   font=("Segoe UI", 9), bd=0, relief="flat",
                                   pady=7, cursor="hand2", command=self.set_format_audio)
        self.btn_audio.pack(side="right", expand=True, fill="x")
        
        # Barra y Estado de Progreso
        self.progress_frame = tk.Frame(card_inner, bg="#1E293B")
        self.progress_frame.pack(fill="x", pady=(0, 12))
        
        self.lbl_progress_title = tk.Label(self.progress_frame, text="Listo para iniciar descarga.", 
                                           font=("Segoe UI", 9), bg="#1E293B", fg="#94A3B8",
                                           anchor="w", justify="left")
        self.lbl_progress_title.pack(fill="x", pady=(0, 4))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, style="Horizontal.TProgressbar", 
                                            mode="determinate", variable=self.progress_var)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        self.lbl_progress_stats = tk.Label(self.progress_frame, text="0.0% | Velocidad: -- | Restante: --", 
                                           font=("Segoe UI", 9), bg="#1E293B", fg="#94A3B8")
        self.lbl_progress_stats.pack(anchor="w")
        
        # Botón de Descarga
        self.btn_download = tk.Button(card_inner, text="🚀 INICIAR DESCARGA", 
                                      bg="#10B981", fg="#F8FAFC", 
                                      activebackground="#059669", activeforeground="#F8FAFC",
                                      font=("Segoe UI", 11, "bold"), bd=0, relief="flat",
                                      pady=10, cursor="hand2", command=self.start_download)
        self.btn_download.pack(fill="x", pady=(4, 0))
        self.btn_download.bind("<Enter>", lambda e: self.on_download_hover(True))
        self.btn_download.bind("<Leave>", lambda e: self.on_download_hover(False))
        
        # Estado FFmpeg
        self.lbl_ffmpeg_status = tk.Label(card_inner, text="Buscando FFmpeg...", 
                                          font=("Segoe UI", 8, "italic"), bg="#1E293B", fg="#94A3B8")
        self.lbl_ffmpeg_status.pack(anchor="center", pady=(6, 0))
        
        # 3. Registro (Log)
        log_lbl = tk.Label(main_frame, text="REGISTRO DE PROCESO", 
                           font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#0F172A")
        log_lbl.pack(anchor="w", pady=(8, 4))
        
        log_border = tk.Frame(main_frame, bg="#334155", bd=1)
        log_border.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_border, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_border, bg="#0F172A", fg="#E2E8F0", 
                                insertbackground="#F8FAFC", bd=0, relief="flat",
                                font=("Consolas", 9), yscrollcommand=scrollbar.set,
                                state="disabled", wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scrollbar.configure(command=self.log_text.yview)

    def on_url_change(self, *args):
        url = self.url_var.get()
        tipo = detectar_tipo_url(url)
        self.lbl_detector.configure(text=tipo)

    def set_format_audio(self):
        if self.is_downloading:
            return
        self.formato = "audio"
        self.btn_audio.configure(bg="#6366F1", fg="#F8FAFC", font=("Segoe UI", 9, "bold"))
        self.btn_video.configure(bg="#0F172A", fg="#94A3B8", font=("Segoe UI", 9))
        
    def set_format_video(self):
        if self.is_downloading:
            return
        self.formato = "video"
        self.btn_audio.configure(bg="#0F172A", fg="#94A3B8", font=("Segoe UI", 9))
        self.btn_video.configure(bg="#6366F1", fg="#F8FAFC", font=("Segoe UI", 9, "bold"))

    def check_ffmpeg(self):
        if self.ffmpeg_dir:
            self.lbl_ffmpeg_status.configure(text="✅ FFmpeg listo en la carpeta 'ffmpeg'", fg="#10B981")
            self.btn_download.configure(state="normal")
        else:
            self.lbl_ffmpeg_status.configure(text="❌ FFmpeg no encontrado en la carpeta 'ffmpeg'. Descarga requerida.", fg="#EF4444")
            self.btn_download.configure(state="disabled", bg="#475569", fg="#94A3B8", cursor="arrow")

    def on_download_hover(self, hover):
        if self.is_downloading or not self.ffmpeg_dir:
            return
        if hover:
            self.btn_download.configure(bg="#059669")
        else:
            self.btn_download.configure(bg="#10B981")

    def start_download(self):
        url = self.entry_link.get().strip()
        custom_name = self.entry_name.get().strip()
        
        if not url:
            messagebox.showwarning("Enlace Vacío", "Por favor, pega el enlace del video, película (.m3u8) o red social.")
            return
            
        self.is_downloading = True
        
        # Deshabilitar controles
        self.btn_download.configure(text="⏳ DESCARGANDO...", state="disabled", bg="#475569", fg="#94A3B8", cursor="arrow")
        self.entry_link.configure(state="disabled")
        self.entry_name.configure(state="disabled")
        self.btn_audio.configure(state="disabled")
        self.btn_video.configure(state="disabled")
        
        self.lbl_progress_title.configure(text="Conectando con el servidor multimedia...", fg="#F8FAFC")
        self.progress_var.set(0.0)
        self.lbl_progress_stats.configure(text="0.0% | Velocidad: -- | Restante: --")
        
        # Limpiar registro
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        
        # Redirigir consola
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = ConsoleRedirector(self.download_queue)
        sys.stderr = ConsoleRedirector(self.download_queue)
        
        # Iniciar hilo de descarga
        self.thread = threading.Thread(target=self.run_download, args=(url, custom_name))
        self.thread.daemon = True
        self.thread.start()

    def run_download(self, url, custom_name):
        try:
            hook = crear_progress_hook(self.download_queue)
            descargar_multimedia(url, self.ffmpeg_dir, self.formato, progress_hook=hook, custom_name=custom_name)
        except Exception as e:
            print(f"\n❌ Error al procesar la descarga: {str(e)}")
        finally:
            self.root.after(100, self.on_download_complete)

    def on_download_complete(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        
        self.is_downloading = False
        
        self.btn_download.configure(text="🚀 INICIAR DESCARGA", state="normal", bg="#10B981", fg="#F8FAFC", cursor="hand2")
        self.entry_link.configure(state="normal")
        self.entry_name.configure(state="normal")
        self.btn_audio.configure(state="normal")
        self.btn_video.configure(state="normal")
        
        if self.formato == "audio":
            self.set_format_audio()
        else:
            self.set_format_video()
        
        self.lbl_progress_title.configure(text="Proceso finalizado. Revisa el registro.", fg="#10B981")
        messagebox.showinfo("Proceso Terminado", "La descarga ha concluido. Revisa la carpeta correspondiente y el registro de eventos.")

    def check_queue(self):
        try:
            while True:
                item = self.download_queue.get_nowait()
                if isinstance(item, dict):
                    if item.get('type') == 'progress':
                        percent = item.get('percent', 0.0)
                        speed = item.get('speed', 'N/A')
                        eta = item.get('eta', 'N/A')
                        title = item.get('title', 'Descargando...')
                        
                        self.progress_var.set(percent)
                        self.lbl_progress_title.configure(text=f"Descargando: {title}", fg="#F8FAFC")
                        self.lbl_progress_stats.configure(text=f"{percent:.1f}% | Velocidad: {speed} | Restante: {eta}")
                        
                    elif item.get('type') == 'finished_video':
                        title = item.get('title', '')
                        self.log_text.configure(state='normal')
                        self.log_text.insert('end', f"✅ Guardado: {title}\n")
                        self.log_text.see('end')
                        self.log_text.configure(state='disabled')
                        
                elif isinstance(item, str):
                    self.log_text.configure(state='normal')
                    self.log_text.insert('end', item)
                    self.log_text.see('end')
                    self.log_text.configure(state='disabled')
                    
                self.download_queue.task_done()
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def on_closing(self):
        if self.is_downloading:
            if messagebox.askyesno("Salir", "Hay una descarga activa en progreso. ¿Deseas interrumpirla y salir?"):
                self.root.destroy()
        else:
            self.root.destroy()

def cli_main():
    """Función para ejecutar desde la consola de comandos"""
    print("=" * 60)
    print("  K-RIPPER - DESCARGADOR MULTIMEDIA (PELÍCULAS, SERIES, REDES)")
    print("=" * 60)
    
    ffmpeg_dir = verificar_ffmpeg()
    print("✅ FFmpeg encontrado\n")

    print("📌 Formato de salida:")
    print("   1. Video (MP4) [Ideal para películas y clips]")
    print("   2. Audio (MP3)")
    opcion_formato = input("Elige una opción (1 o 2) [Por defecto: 1]: ").strip()
    formato = 'audio' if opcion_formato == '2' else 'video'
    print(f"✅ Formato: {formato.upper()}\n")
    
    url = input("Pega el enlace (URL web, video, o .m3u8): ").strip()
    if not url:
        print("❌ Error: No se proporcionó ningún enlace.")
        sys.exit(1)
        
    custom_name = input("Nombre personalizado para el archivo (opcional, presiona Enter para omitir): ").strip()
    
    descargar_multimedia(url, ffmpeg_dir, formato, custom_name=custom_name)

def main():
    if len(sys.argv) > 1:
        cli_main()
    else:
        try:
            root = tk.Tk()
            app = DownloaderGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"No se pudo iniciar la interfaz gráfica: {e}")
            print("Iniciando en consola...")
            cli_main()

if __name__ == "__main__":
    main()
