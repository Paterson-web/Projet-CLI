"""Commandes intégrées du framework (info, exit, clear)."""

import os
import platform
import sys

from config.settings import APP_AUTHOR, APP_NAME, APP_VERSION
from core.command_base import CommandBase, CommandResult


class InfoCommand(CommandBase):
    """Affiche les métadonnées et l'état du framework."""

    def __init__(self) -> None:
        super().__init__(
            name="info",
            description="Affiche les informations globales et l'état d'exécution du framework.",
            usage="info",
            aliases=["about", "version"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        info_lines = [
            f"Framework      : {APP_NAME} v{APP_VERSION}",
            f"Auteur         : {APP_AUTHOR}",
            f"Python         : {platform.python_version()} ({sys.executable})",
            f"Système hôte   : {platform.system()} {platform.release()} ({platform.machine()})",
            "Architecture   : Modulaire v2.0 (Séparation Vue / Contrôleur / Services)",
        ]
        message = "\n".join(info_lines)
        return CommandResult.ok(message=message, data={"name": APP_NAME, "version": APP_VERSION})


class ExitCommand(CommandBase):
    """Met fin à la session interactive du shell."""

    def __init__(self) -> None:
        super().__init__(
            name="exit",
            description="Quitte le shell interactif du framework.",
            usage="exit",
            aliases=["quit", "q"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult.exit(message="Fermeture de la session. À bientôt !")


class ClearCommand(CommandBase):
    """Efface l'écran du terminal."""

    def __init__(self) -> None:
        super().__init__(
            name="clear",
            description="Nettoie l'affichage du terminal.",
            usage="clear",
            aliases=["cls"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        os.system("cls" if sys.platform == "win32" else "clear")
        return CommandResult.ok(message="")
