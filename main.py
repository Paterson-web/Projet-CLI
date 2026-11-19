#!/usr/bin/env python3
"""Point d'entrée unique de Personal Framework CLI v2.0.0.

Ce script initialise la journalisation, instancie le gestionnaire de commandes,
enregistre les modules actifs et démarre l'interface utilisateur interactive.
"""

import sys

from config.logging_config import setup_logging
from core.builtin_commands import ClearCommand, ExitCommand, InfoCommand
from core.command_manager import CommandManager
from core.legacy_bridges import PingLegacyCommand, PortscanLegacyCommand
from core.logger import get_logger
from core.shell import PatersonShell


def bootstrap_command_manager() -> CommandManager:
    """Construit et configure le gestionnaire de commandes avec les modules initiaux."""
    manager = CommandManager()

    # Enregistrement des commandes intégrées de base
    manager.register(InfoCommand())
    manager.register(ExitCommand())
    manager.register(ClearCommand())

    # Enregistrement des commandes réseau transitoires (v1.1.0 bridge)
    manager.register(PingLegacyCommand())
    manager.register(PortscanLegacyCommand())

    return manager


def main() -> None:
    """Fonction principale d'amorçage du framework."""
    # 1. Initialisation des logs
    setup_logging(level="INFO")
    logger = get_logger("main")
    logger.info("Démarrage de Personal Framework CLI")

    # 2. Construction du moteur
    command_manager = bootstrap_command_manager()

    # 3. Lancement du Shell
    shell = PatersonShell(command_manager=command_manager)
    try:
        shell.run()
    except Exception as err:
        logger.critical(f"Erreur fatale au niveau de l'application : {err}", exc_info=True)
        print(f"\n[FATAL] Le framework s'est arrêté de manière inattendue : {err}", file=sys.stderr)
        sys.exit(1)
    finally:
        logger.info("Arrêt normal de Personal Framework CLI")


if __name__ == "__main__":
    main()
