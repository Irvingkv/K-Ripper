# K-Ripper 🎬🎵

**K-Ripper** es una herramienta potente y elegante para descargar contenido multimedia (videos, música, listas de reproducción completas y transmisiones de streaming directo `.m3u8` / `.mpd`) con interfaz gráfica moderna (Tkinter) y soporte de consola (CLI).

## 🚀 Características
- **Plataformas Soportadas**: YouTube (videos y playlists), TikTok, Instagram (Reels y Posts), Twitter / X, Facebook, Twitch, SoundCloud y flujos directos HLS (.m3u8) de webs de películas y series.
- **Formatos de Salida**: 
  - 🎬 **Video (MP4)**: Resolución óptima con audio sincronizado.
  - 🎵 **Audio (MP3)**: Extracción directa a 192 kbps.
- **Detector Dinámico de Enlaces**: Identifica automáticamente el tipo de contenido al pegar la URL.
- **Nombres Personalizados**: Permite asignar títulos personalizados (ideal para películas o series que no contienen metadatos en su flujo `.m3u8`).
- **Evasión Anti-Bot**: Uso de cabeceras de navegador real y reintentos automáticos con sesiones de navegadores locales si el sitio requiere autenticación.

## 📋 Requisitos
1. **Python 3.8 o superior**
2. **Dependencias de Python**:
   ```bash
   pip install -r requirements.txt
   ```
3. **FFmpeg**:
   - Descarga FFmpeg y coloca `ffmpeg.exe` dentro de una carpeta llamada `ffmpeg` en la raíz del proyecto:
     ```
     K-Ripper/
     ├── ffmpeg/
     │   └── ffmpeg.exe
     ├── descargar_playlist.py
     ├── requirements.txt
     └── README.md
     ```

## ▶️ Uso

### Modo Interfaz Gráfica (GUI)
```bash
python descargar_playlist.py
```

### Modo Consola (CLI)
```bash
python descargar_playlist.py --cli
```
