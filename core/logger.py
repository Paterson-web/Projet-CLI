"""Fournisseur d'instances de journalisation pour Personal Framework CLI."""

import logging
from config.logging_config import setup_logging


def get_logger(name: str) -> logging.Logger:
    """Fournit un logger configuré pour le composant spécifié.

    Initialise automatiquement le logging global si cela n'a pas encore été fait.

    Args:
        name: Nom qualifié du module ou de la commande (ex: 'modules.network.ping').

    Returns:
        Instance de logging.Logger prête à l'emploi.
    """
    setup_logging()
    return logging.getLogger(name)
