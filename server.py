"""
K-Ripper - Servidor Web Local (FastAPI + Uvicorn)
Permite usar K-Ripper desde el navegador web local o desde cualquier
dispositivo conectado a la misma red WiFi (móviles, tablets, laptops).
"""
import os
import sys
import json
import socket
import asyncio
import queue
import threading
import webbrowser
from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core import (
    obtener_ffmpeg_dir,
    verificar_ffmpeg,
    detectar_tipo_url,
    descargar_multimedia,
    crear_progress_hook,
)

app = FastAPI(title="K-Ripper Web")

# Estado global de la aplicación
class AppState:
    def __init__(self):
        self.is_downloading = False
        self.current_job = None
        self.event_subscribers = []
        self.log_history = []
        self.download_queue = queue.Queue()

state = AppState()

def get_local_ip():
    """Detecta la IP local de la computadora en la red WiFi/LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class DownloadRequest(BaseModel):
    url: str
    format: str = "video"  # 'video' o 'audio'
    custom_name: Optional[str] = ""

class WebConsoleRedirector:
    """Captura prints y salidas de consola para transmitirlos vía SSE al navegador."""
    def __init__(self, target_queue):
        self.queue = target_queue

    def write(self, string):
        if "[download]" in string and "%" in string:
            return
        cleaned = string.replace('\r', '').strip()
        if cleaned:
            self.queue.put({'type': 'log', 'message': cleaned})

    def flush(self):
        pass

def worker_thread(url: str, ffmpeg_dir: str, formato: str, custom_name: str):
    """Hilo secundario que ejecuta la descarga con yt-dlp."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = WebConsoleRedirector(state.download_queue)
    sys.stderr = WebConsoleRedirector(state.download_queue)
    
    try:
        hook = crear_progress_hook(state.download_queue)
        state.download_queue.put({'type': 'status', 'status': 'starting', 'message': 'Iniciando conexión...'})
        descargar_multimedia(url, ffmpeg_dir, formato=formato, progress_hook=hook, custom_name=custom_name)
        state.download_queue.put({'type': 'status', 'status': 'completed', 'message': 'Descarga completada'})
    except Exception as e:
        state.download_queue.put({'type': 'status', 'status': 'error', 'message': f'Error: {str(e)}'})
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        state.is_downloading = False

@app.get("/api/info")
def get_info():
    """Retorna información del sistema, IP local y estado de FFmpeg."""
    ffmpeg_dir = obtener_ffmpeg_dir()
    return {
        "ffmpeg_ready": ffmpeg_dir is not None,
        "ffmpeg_path": ffmpeg_dir or "No encontrado en carpeta 'ffmpeg/'",
        "local_ip": get_local_ip(),
        "port": 8000,
        "is_downloading": state.is_downloading,
        "url_hint": "http://" + get_local_ip() + ":8000"
    }

@app.post("/api/detect")
def detect_url(req: DownloadRequest):
    """Detecta el tipo de sitio a partir de la URL."""
    tipo = detectar_tipo_url(req.url)
    return {"tipo": tipo}

@app.post("/api/download")
def start_download(req: DownloadRequest):
    """Inicia una descarga en segundo plano."""
    if state.is_downloading:
        return JSONResponse(status_code=400, content={"error": "Ya hay una descarga en curso"})
    
    ffmpeg_dir = obtener_ffmpeg_dir()
    if not ffmpeg_dir:
        return JSONResponse(status_code=400, content={"error": "FFmpeg no encontrado en la carpeta 'ffmpeg/'"})
    
    if not req.url or not req.url.strip():
        return JSONResponse(status_code=400, content={"error": "El enlace no puede estar vacío"})
    
    state.is_downloading = True
    t = threading.Thread(
        target=worker_thread,
        args=(req.url, ffmpeg_dir, req.format, req.custom_name or ""),
        daemon=True
    )
    t.start()
    return {"success": True, "message": "Descarga iniciada"}

@app.get("/api/events")
async def event_stream(request: Request):
    """Transmite eventos en tiempo real al navegador (SSE: Server-Sent Events)."""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                # Comprobar si hay eventos en la cola sin bloquear el event loop
                while not state.download_queue.empty():
                    item = state.download_queue.get_nowait()
                    yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                pass
            await asyncio.sleep(0.2)
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Montar archivos estáticos para la interfaz web
web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
os.makedirs(web_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")

def start_server(open_browser: bool = True, host: str = "0.0.0.0", port: int = 8000):
    """Ejecuta el servidor Uvicorn y opcionalmente abre el navegador."""
    import uvicorn
    local_ip = get_local_ip()
    print("=" * 65)
    print("  🚀 K-RIPPER WEB SERVER INICIADO")
    print(f"  💻 En esta PC:     http://localhost:{port}")
    print(f"  📱 En tu red WiFi: http://{local_ip}:{port}")
    print("=" * 65)
    
    if open_browser:
        # Abrir navegador tras 1.2 segundos para asegurar que el servidor esté activo
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
        
    uvicorn.run(app, host=host, port=port, log_level="warning")

if __name__ == "__main__":
    start_server()
