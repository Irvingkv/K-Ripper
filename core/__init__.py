"""
Paquete core de K-Ripper.
"""
from .utils import obtener_ffmpeg_dir, verificar_ffmpeg, detectar_tipo_url
from .downloader import descargar_multimedia, crear_progress_hook

__all__ = [
    'obtener_ffmpeg_dir',
    'verificar_ffmpeg',
    'detectar_tipo_url',
    'descargar_multimedia',
    'crear_progress_hook',
]
