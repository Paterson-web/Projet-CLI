"""Configuration centralisée du système de journalisation (logging).

Ce module initialise les handlers de log (fichier et console optionnelle)
avec rotation ou écriture contrôlée dans le dossier logs/.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config.settings import (
    DEFAULT_LOG_LEVEL,
    LOG_DATE_FORMAT,
    LOG_FILE_NAME,
    LOG_FORMAT,
    LOGS_DIR,
)

_is_configured = False


def setup_logging(
    level: str = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    console_output: bool = False,
) -> None:
    """Configure la journalisation racine pour l'ensemble du framework.

    Args:
        level: Niveau de log textuel ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_file: Chemin personnalisé du fichier de log. Si None, utilise logs/framework.log.
        console_output: Si True, diffuse également les logs sur la sortie standard.
    """
    global _is_configured
    if _is_configured:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Nettoyage d'éventuels handlers déjà attachés
    root_logger.handlers.clear()

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Handler fichier tournant (max 5 Mo par fichier, conservation de 3 sauvegardes)
    destination = log_file or (LOGS_DIR / LOG_FILE_NAME)
    file_handler = RotatingFileHandler(
        filename=destination,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Seulement avertissements et erreurs sur console
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _is_configured = True
