"""
Interfaz gráfica moderna para K-Ripper construida con Tkinter.
"""
import sys
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from core import (
    obtener_ffmpeg_dir,
    detectar_tipo_url,
    descargar_multimedia,
    crear_progress_hook,
)

class ConsoleRedirector:
    """Redirige las salidas estándar hacia la cola de la interfaz para alimentar el log."""
    def __init__(self, output_queue):
        self.queue = output_queue

    def write(self, string):
        if "[download]" in string and "%" in string:
            return
        cleaned = string.replace('\r', '')
        if cleaned:
            self.queue.put(cleaned)

    def flush(self):
        pass

class DownloaderGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("K-Ripper - Universal Media & Movie Downloader")
        self.root.geometry("740x740")
        self.root.configure(bg="#0F172A")
        self.root.minsize(680, 650)
        
        self.formato = "video"
        self.ffmpeg_dir = obtener_ffmpeg_dir()
        self.download_queue = queue.Queue()
        self.is_downloading = False
        
        self._setup_styles()
        self._build_ui()
        self._check_ffmpeg()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.after(100, self._check_queue)
        
    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure(
            "Vertical.TScrollbar", 
            gripcount=0, 
            background="#334155", 
            darkcolor="#334155", 
            lightcolor="#334155", 
            troughcolor="#0F172A", 
            bordercolor="#0F172A",
            arrowcolor="#94A3B8"
        )
        self.style.map("Vertical.TScrollbar", background=[('active', '#475569'), ('pressed', '#1E293B')])
                       
        self.style.configure(
            "Horizontal.TProgressbar",
            thickness=8,
            troughcolor="#0F172A",
            background="#6366F1",
            bordercolor="#1E293B",
            lightcolor="#6366F1",
            darkcolor="#6366F1"
        )
                             
    def _build_ui(self):
        main_frame = tk.Frame(self.root, bg="#0F172A")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Cabecera
        header_frame = tk.Frame(main_frame, bg="#0F172A")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(header_frame, text="K-RIPPER DOWNLOADER", 
                               font=("Segoe UI", 17, "bold"), fg="#F8FAFC", bg="#0F172A")
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(header_frame, 
                                  text="Descarga de Películas (.m3u8), YouTube, TikTok, Instagram, Twitter y Servidores de Video", 
                                  font=("Segoe UI", 9), fg="#94A3B8", bg="#0F172A")
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # Tarjeta principal de configuración
        card = tk.Frame(main_frame, bg="#1E293B", bd=1, highlightbackground="#334155", highlightcolor="#334155")
        card.pack(fill="x", pady=(0, 12))
        
        card_inner = tk.Frame(card, bg="#1E293B")
        card_inner.pack(fill="x", padx=20, pady=16)
        
        # Campo de enlace
        lbl_link = tk.Label(card_inner, text="Enlace del Video, Película (.m3u8) o Playlist:", 
                            font=("Segoe UI", 10, "bold"), bg="#1E293B", fg="#F8FAFC")
        lbl_link.pack(anchor="w", pady=(0, 4))
        
        self.entry_border = tk.Frame(card_inner, bg="#334155", bd=1)
        self.entry_border.pack(fill="x", pady=(0, 4))
        
        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self._on_url_change)
        
        self.entry_link = tk.Entry(self.entry_border, textvariable=self.url_var,
                                   bg="#0F172A", fg="#F8FAFC", 
                                   insertbackground="#F8FAFC", bd=0, relief="flat",
                                   font=("Segoe UI", 10))
        self.entry_link.pack(fill="x", padx=10, pady=7)
        self.entry_link.bind("<FocusIn>", lambda e: self.entry_border.configure(bg="#6366F1"))
        self.entry_link.bind("<FocusOut>", lambda e: self.entry_border.configure(bg="#334155"))
        
        self.lbl_detector = tk.Label(card_inner, text="🔗 Pega un enlace de video, película, red social o flujo .m3u8",
                                     font=("Segoe UI", 8, "italic"), bg="#1E293B", fg="#38BDF8")
        self.lbl_detector.pack(anchor="w", pady=(0, 10))
        
        # Nombre personalizado opcional
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
        
        # Selector de formato
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
        
        # Indicadores de Progreso
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
        self.btn_download.bind("<Enter>", lambda e: self._on_download_hover(True))
        self.btn_download.bind("<Leave>", lambda e: self._on_download_hover(False))
        
        # Estado FFmpeg
        self.lbl_ffmpeg_status = tk.Label(card_inner, text="Buscando FFmpeg...", 
                                          font=("Segoe UI", 8, "italic"), bg="#1E293B", fg="#94A3B8")
        self.lbl_ffmpeg_status.pack(anchor="center", pady=(6, 0))
        
        # Registro en consola visual
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

    def _on_url_change(self, *args):
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

    def _check_ffmpeg(self):
        if self.ffmpeg_dir:
            self.lbl_ffmpeg_status.configure(text="✅ FFmpeg listo en la carpeta 'ffmpeg'", fg="#10B981")
            self.btn_download.configure(state="normal")
        else:
            self.lbl_ffmpeg_status.configure(text="❌ FFmpeg no encontrado en la carpeta 'ffmpeg'. Descarga requerida.", fg="#EF4444")
            self.btn_download.configure(state="disabled", bg="#475569", fg="#94A3B8", cursor="arrow")

    def _on_download_hover(self, hover):
        if self.is_downloading or not self.ffmpeg_dir:
            return
        self.btn_download.configure(bg="#059669" if hover else "#10B981")

    def start_download(self):
        url = self.entry_link.get().strip()
        custom_name = self.entry_name.get().strip()
        
        if not url:
            messagebox.showwarning("Enlace Vacío", "Por favor, pega el enlace del video, película (.m3u8) o red social.")
            return
            
        self.is_downloading = True
        
        self.btn_download.configure(text="⏳ DESCARGANDO...", state="disabled", bg="#475569", fg="#94A3B8", cursor="arrow")
        self.entry_link.configure(state="disabled")
        self.entry_name.configure(state="disabled")
        self.btn_audio.configure(state="disabled")
        self.btn_video.configure(state="disabled")
        
        self.lbl_progress_title.configure(text="Conectando con el servidor multimedia...", fg="#F8FAFC")
        self.progress_var.set(0.0)
        self.lbl_progress_stats.configure(text="0.0% | Velocidad: -- | Restante: --")
        
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = ConsoleRedirector(self.download_queue)
        sys.stderr = ConsoleRedirector(self.download_queue)
        
        self.thread = threading.Thread(target=self._run_download, args=(url, custom_name), daemon=True)
        self.thread.start()

    def _run_download(self, url, custom_name):
        try:
            hook = crear_progress_hook(self.download_queue)
            descargar_multimedia(url, self.ffmpeg_dir, self.formato, progress_hook=hook, custom_name=custom_name)
        except Exception as e:
            print(f"\n❌ Error al procesar la descarga: {str(e)}")
        finally:
            self.root.after(100, self._on_download_complete)

    def _on_download_complete(self):
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

    def _check_queue(self):
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
        self.root.after(100, self._check_queue)

    def _on_closing(self):
        if self.is_downloading:
            if messagebox.askyesno("Salir", "Hay una descarga activa en progreso. ¿Deseas interrumpirla y salir?"):
                self.root.destroy()
        else:
            self.root.destroy()
