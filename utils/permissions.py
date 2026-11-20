"""Gestion et vérification des privilèges système (root / administrateur).

Ce module contrôle les autorisations locales sans imposer de privilèges élevés
lorsque les bibliothèques standards ou sockets normaux suffisent.
"""

import os
import sys


def is_root_or_admin() -> bool:
    """Vérifie si le processus s'exécute avec des privilèges superutilisateur (root / admin).

    Returns:
        True si le processus possède les droits administrateur, False sinon.
    """
    if sys.platform != "win32":
        try:
            return os.geteuid() == 0  # type: ignore[attr-defined]
        except AttributeError:
            return False

    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
    except Exception:
        return False


def explain_permission_requirement(operation: str) -> str:
    """Fournit une explication claire et constructive lorsqu'une opération nécessite des privilèges.

    Args:
        operation: Nom de l'opération tentée (ex: 'raw_socket', 'promiscuous_mode').

    Returns:
        Message explicatif avec la commande recommandée.
    """
    if sys.platform != "win32":
        return (
            f"L'opération '{operation}' requiert les privilèges superutilisateur (root) ou la capacité CAP_NET_RAW.\n"
            f"Pour l'exécuter sous Linux : relancez le framework avec 'sudo paterson'."
        )
    return (
        f"L'opération '{operation}' requiert des privilèges élevés sous Windows.\n"
        "Veuillez exécuter votre terminal en tant qu'Administrateur."
    )
