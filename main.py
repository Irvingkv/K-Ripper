"""
K-Ripper - Punto de Entrada Principal
Por defecto inicia la aplicación Web moderna en http://localhost:8000.
Opciones:
  python main.py          -> Inicia la Web App moderna (Abre navegador automáticamente)
  python main.py --gui    -> Inicia la interfaz de escritorio clásica Tkinter
  python main.py --cli    -> Inicia el modo interactivo por consola/terminal
"""
import sys

def main():
    args = sys.argv[1:]
    
    if any(a in args for a in ['--cli', '-c']):
        from cli import cli_main
        cli_main()
    elif any(a in args for a in ['--gui', '-g']):
        import tkinter as tk
        from ui import DownloaderGUI
        try:
            root = tk.Tk()
            app = DownloaderGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"No se pudo iniciar Tkinter ({e}).")
            from cli import cli_main
            cli_main()
    else:
        # Modo por defecto: Web App moderna (FastAPI + Navegador)
        from server import start_server
        open_browser = '--no-browser' not in args
        start_server(open_browser=open_browser)

if __name__ == "__main__":
    main()
