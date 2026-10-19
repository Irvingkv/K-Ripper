"""
Modo de línea de comandos (CLI) para K-Ripper.
"""
import sys
from core import verificar_ffmpeg, descargar_multimedia

def cli_main():
    """Ejecuta la interfaz de línea de comandos."""
    print("=" * 60)
    print("  K-RIPPER - DESCARGADOR MULTIMEDIA (PELÍCULAS, SERIES, REDES)")
    print("=" * 60)
    
    ffmpeg_dir = verificar_ffmpeg()
    print("✅ FFmpeg detectado correctamente.\n")

    print("📌 Formato de salida:")
    print("   1. Video (MP4) [Por defecto]")
    print("   2. Audio (MP3)")
    opcion_formato = input("Elige una opción (1 o 2) [1]: ").strip()
    formato = 'audio' if opcion_formato == '2' else 'video'
    print(f"✅ Formato seleccionado: {formato.upper()}\n")
    
    url = input("Pega el enlace (URL web, video o .m3u8): ").strip()
    if not url:
        print("❌ Error: No se proporcionó ningún enlace.")
        sys.exit(1)
        
    custom_name = input("Nombre personalizado (opcional, presiona Enter para omitir): ").strip()
    descargar_multimedia(url, ffmpeg_dir, formato=formato, custom_name=custom_name)

if __name__ == "__main__":
    cli_main()
