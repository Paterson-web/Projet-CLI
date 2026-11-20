"""Utilitaires d'adaptation et de détection multiplateforme (OS).

Ce module centralise la gestion des particularités entre Linux (Ubuntu cible),
Windows et macOS, notamment pour la construction des commandes système.
"""

import platform
import sys
from typing import Final

_CURRENT_OS: Final[str] = sys.platform


def is_linux() -> bool:
    """Indique si l'environnement d'exécution est Linux."""
    return _CURRENT_OS.startswith("linux")


def is_windows() -> bool:
    """Indique si l'environnement d'exécution est Windows."""
    return _CURRENT_OS.startswith("win32") or _CURRENT_OS.startswith("cygwin")


def is_macos() -> bool:
    """Indique si l'environnement d'exécution est macOS (Darwin)."""
    return _CURRENT_OS.startswith("darwin")


def get_platform_name() -> str:
    """Retourne un libellé textuel propre du système d'exploitation."""
    if is_linux():
        return "Linux"
    if is_windows():
        return "Windows"
    if is_macos():
        return "macOS"
    return platform.system()


def build_ping_command(
    target: str,
    count: int = 4,
    timeout_sec: float = 3.0,
) -> list[str]:
    """Construit la liste d'arguments sécurisée pour l'utilitaire système ping selon l'OS.

    Args:
        target: Adresse IP ou nom d'hôte validé.
        count: Nombre de paquets ICMP à émettre.
        timeout_sec: Délai d'attente maximum par sonde (en secondes).

    Returns:
        Liste de chaînes prête à être transmise à subprocess.run sans shell=True.
    """
    if is_windows():
        # Sous Windows : -n pour le nombre, -w pour le timeout en millisecondes
        timeout_ms = max(1000, int(timeout_sec * 1000))
        return ["ping", "-n", str(count), "-w", str(timeout_ms), target]

    if is_macos():
        # Sous macOS : -c pour le nombre, -W pour le timeout en millisecondes
        timeout_ms = max(1000, int(timeout_sec * 1000))
        return ["ping", "-c", str(count), "-W", str(timeout_ms), target]

    # Sous Linux (Ubuntu) : -c pour le nombre, -W pour le timeout en secondes
    timeout_s = max(1, int(timeout_sec))
    return ["ping", "-c", str(count), "-W", str(timeout_s), target]
