"""
WallasAPI ASCII Banner
Muestra un banner vistoso al iniciar el servidor o el script batch.
"""
import sys


def show_banner():
    """Imprime el banner de WallasAPI con colores ANSI."""
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    YELLOW = "\033[33m"
    WHITE = "\033[37m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    all_lines = [
        '',
        r' _    _  ___   _      _       ___   _____       ___  ______ _____ ',
        r'| |  | |/ _ \ | |    | |     / _ \ /  ___|     / _ \ | ___ \_   _|',
        r'| |  | / /_\ \| |    | |    / /_\ \ `--.     / /_\ \| |_/ / | |  ',
        r'| |/\| |  _  || |    | |    |  _  | `--. \    |  _  ||  __/  | |  ',
        r'\  /\  / | | || |____| |____| | | |/\__/ /    | | | || |    _| |_ ',
        r' \/  \/\_| |_/\_____/\_____/\_| |_/\____/     \_| |_/\_|    \___/ ',
        r'                                                                  ',
        r'                                                                  ',
        '',
        DIM + WHITE + '          p o w e r e d  b y  w u b j a k' + RESET,
        '',
        DIM + '  El Enrutador Inteligente Multi-Proveedor de IA' + RESET,
        '',
    ]

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

    for line in all_lines:
        print(line)


if __name__ == "__main__":
    show_banner()
