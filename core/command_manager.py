"""Gestionnaire central de commandes (CommandManager).

Ce module implémente le registre de commandes (Command Registry) et assure
la recherche, le routage des arguments, la journalisation des exécutions
et la capture centralisée des exceptions.
"""

from typing import Optional

from core.command_base import CommandBase, CommandResult
from core.exceptions import CommandError, CommandNotFoundError, ValidationError
from core.logger import get_logger

logger = get_logger("core.command_manager")


class CommandManager:
    """Orchestre l'enregistrement, la découverte et l'exécution des commandes."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandBase] = {}
        self._aliases: dict[str, str] = {}

    def register(self, command: CommandBase) -> None:
        """Enregistre une nouvelle commande et ses alias dans le gestionnaire.

        Args:
            command: Instance d'une sous-classe de CommandBase.

        Raises:
            ValueError: Si le nom de la commande est déjà enregistré.
        """
        name = command.name.lower()
        if name in self._commands:
            raise ValueError(f"La commande '{name}' est déjà enregistrée.")

        self._commands[name] = command
        logger.debug(f"Commande enregistrée : {name}")

        for alias in command.aliases:
            alias_lower = alias.lower()
            if alias_lower in self._commands or alias_lower in self._aliases:
                logger.warning(
                    f"L'alias '{alias_lower}' pour la commande '{name}' est déjà utilisé et sera ignoré."
                )
                continue
            self._aliases[alias_lower] = name

    def unregister(self, name: str) -> bool:
        """Désenregistre une commande par son nom.

        Args:
            name: Nom de la commande à retirer.

        Returns:
            True si la commande existait et a été retirée, False sinon.
        """
        name = name.lower()
        if name not in self._commands:
            return False

        command = self._commands.pop(name)
        # Nettoyage des alias associés
        aliases_to_remove = [k for k, v in self._aliases.items() if v == name]
        for a in aliases_to_remove:
            self._aliases.pop(a, None)

        logger.debug(f"Commande retirée : {name}")
        return True

    def get(self, name_or_alias: str) -> Optional[CommandBase]:
        """Recherche une commande par son nom exact ou l'un de ses alias.

        Args:
            name_or_alias: Nom ou alias de la commande recherchée.

        Returns:
            L'instance de CommandBase correspondante, ou None si introuvable.
        """
        key = name_or_alias.strip().lower()
        if key in self._commands:
            return self._commands[key]

        real_name = self._aliases.get(key)
        if real_name:
            return self._commands.get(real_name)

        return None

    def execute(self, command_name: str, args: list[str]) -> CommandResult:
        """Distribue l'exécution à la commande correspondante.

        Capture de façon centralisée les erreurs métier et journalise l'événement.

        Args:
            command_name: Nom ou alias de la commande demandée.
            args: Arguments passés à la commande.

        Returns:
            Un objet CommandResult contenant le résultat ou l'erreur formatée.
        """
        command = self.get(command_name)
        if not command:
            logger.warning(f"Tentative d'exécution d'une commande inconnue : '{command_name}'")
            return CommandResult.fail(
                f"Commande inconnue : '{command_name}'. Tapez 'help' pour afficher la liste des commandes disponibles."
            )

        try:
            logger.info(f"Exécution de la commande '{command.name}' avec {len(args)} argument(s)")
            result = command.execute(args)
            return result
        except ValidationError as err:
            logger.warning(f"Erreur de validation dans '{command.name}': {err}")
            return CommandResult.fail(f"Erreur de saisie : {err.message}", error=err.details)
        except CommandError as err:
            logger.error(f"Erreur de commande dans '{command.name}': {err}")
            return CommandResult.fail(f"Erreur d'exécution : {err.message}", error=err.details)
        except Exception as err:
            logger.exception(f"Erreur imprévue lors de l'exécution de '{command.name}': {err}")
            return CommandResult.fail(
                f"Une erreur interne inattendue est survenue : {err}", error=str(err)
            )

    def list_commands(self) -> list[CommandBase]:
        """Retourne la liste triée de toutes les commandes enregistrées."""
        return sorted(self._commands.values(), key=lambda cmd: cmd.name)
