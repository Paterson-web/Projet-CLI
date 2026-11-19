"""Paramètres et configuration centrale de Personal Framework CLI.

Ce module centralise l'ensemble des constantes, chemins de stockage,
délais d'expiration réseau et limites opérationnelles pour éviter
la dispersion de valeurs magiques dans les modules applicatifs.
"""

from pathlib import Path
from typing import Final

# Métadonnées de l'application
APP_NAME: Final[str] = "Personal Framework CLI"
APP_VERSION: Final[str] = "2.0.0-dev"
APP_AUTHOR: Final[str] = "Paterson"

# Chemins absolus du système de fichiers
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
HISTORY_DIR: Final[Path] = DATA_DIR / "history"
REPORTS_DIR: Final[Path] = BASE_DIR / "reports"
LOGS_DIR: Final[Path] = BASE_DIR / "logs"

# S'assurer que les répertoires minimaux de persistance existent
for directory in (DATA_DIR, HISTORY_DIR, REPORTS_DIR, LOGS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Paramètres réseau par défaut
DEFAULT_PING_COUNT: Final[int] = 4
DEFAULT_PING_TIMEOUT: Final[float] = 5.0  # en secondes
DEFAULT_SOCKET_TIMEOUT: Final[float] = 2.0  # en secondes
DEFAULT_DNS_TIMEOUT: Final[float] = 3.0  # en secondes
MAX_SCAN_CONCURRENCY: Final[int] = 50  # limite de concurrence pour les scans
DEFAULT_SCAN_PORTS: Final[tuple[int, ...]] = (
    21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 993, 995, 3306, 3389, 5432, 8080, 8443
)

# Paramètres de journalisation
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
LOG_FILE_NAME: Final[str] = "framework.log"
LOG_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Palette de couleurs ANSI standard pour l'interface
COLOR_RESET: Final[str] = "\033[0m"
COLOR_BOLD: Final[str] = "\033[1m"
COLOR_CYAN: Final[str] = "\033[96m"
COLOR_GREEN: Final[str] = "\033[92m"
COLOR_YELLOW: Final[str] = "\033[93m"
COLOR_RED: Final[str] = "\033[91m"
COLOR_DIM: Final[str] = "\033[2m"

# Bannière d'accueil v2.0
BANNER: Final[str] = f"""{COLOR_CYAN}{COLOR_BOLD}
  ____       _                           
 |  _ \\ __ _| |_ ___ _ __ ___  ___  _ __  
 | |_) / _` | __/ _ \\ '__/ __|/ _ \\| '_ \\ 
 |  __/ (_| | ||  __/ |  \\__ \\ (_) | | | |
 |_|   \\__,_|\\__\\___|_|  |___/\\___/|_| |_|
{COLOR_RESET}{COLOR_YELLOW}:: {APP_NAME} :: v{APP_VERSION}{COLOR_RESET}
"""
