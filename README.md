# K-Ripper 🎬🎵

**K-Ripper** es un programa para descargar videos y música desde distintas páginas web, redes sociales y enlaces directos de streaming (`.m3u8` o `.mpd`). Cuenta con una aplicación web moderna accesible desde tu navegador o desde cualquier dispositivo en tu red WiFi (móviles y tablets), además de soporte para consola y ventana de escritorio.

---

## 🚀 ¿Qué puede hacer?

* **Descarga desde varias plataformas:** Funciona con YouTube (videos sueltos y playlists), TikTok, Instagram, Twitter / X, Facebook, Twitch, SoundCloud y reproductores web de películas o series.
* **Formatos simples:**
  * **Video (MP4):** Guarda el video en la mejor calidad disponible con audio integrado.
  * **Audio (MP3):** Extrae solo el sonido (192 kbps).
* **Detecta el enlace solo:** Al pegar el link, el programa identifica de qué página proviene.
* **Renombrar archivos:** Puedes escribir tú mismo el nombre del archivo final antes de bajarlo (útil cuando descargas capítulos o películas y el enlace no trae el título real).
* **Menos bloqueos:** Envía datos de navegación comunes para evitar que las páginas corten la descarga por sospecha de bot.
* **Acceso desde el celular:** Abre la interfaz web desde cualquier teléfono o dispositivo conectado a la misma red WiFi para descargar directo a la computadora.

---

## 📁 Estructura del proyecto

```text
K-Ripper/
├── core/
│   ├── __init__.py
│   ├── downloader.py       # Lógica de descarga (usa yt-dlp por detrás)
│   └── utils.py            # Funciones de ayuda y soporte de FFmpeg
├── web/
│   ├── index.html          # Interfaz web responsiva
│   ├── styles.css          # Estilos y paleta de color personalizada
│   └── app.js              # Manejo de descargas y eventos en tiempo real
├── ui/
│   ├── __init__.py
│   └── app.py              # Ventana visual de escritorio con Tkinter (opcional)
├── server.py               # Servidor FastAPI y streaming de eventos en vivo
├── cli.py                  # Versión para usar desde la terminal
├── main.py                 # Archivo principal para iniciar el programa
├── descargar_playlist.py   # Acceso directo secundario
├── requirements.txt        # Librerías necesarias
└── README.md
```

---

## 📋 Requisitos e Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
2. **FFmpeg:**
   * Descarga FFmpeg y coloca `ffmpeg.exe` dentro de una carpeta llamada `ffmpeg/` en la raíz del proyecto.

---

## ▶️ ¿Cómo usarlo?

* **Modo Web App (Recomendado):**
  ```bash
  python main.py
  ```
  *(Se abrirá automáticamente en tu navegador en `http://localhost:8000`, y podrás abrirlo en tu móvil usando la dirección WiFi que aparece en pantalla).*

* **Modo Terminal:**
  ```bash
  python main.py --cli
  ```

* **Modo Escritorio Clásico:**
  ```bash
  python main.py --gui
  ```
