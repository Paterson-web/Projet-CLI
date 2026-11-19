"""Contrat fondamental pour toutes les commandes de Personal Framework CLI.

Ce module définit la classe abstraite CommandBase que chaque commande
(intégrée ou réseau) doit implémenter, ainsi que la structure de retour
CommandResult garantissant des retours d'exécution uniformes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CommandResult:
    """Structure standardisée du résultat d'exécution d'une commande.

    Attributes:
        success: Indique si la commande s'est exécutée sans erreur fatale.
        message: Message synthétique compréhensible pour l'utilisateur.
        data: Données brutes ou structurées produites par la commande (optionnel).
        error: Détail technique de l'erreur en cas d'échec (optionnel).
        should_exit: Signal indiquant au shell s'il doit mettre fin à la session.
    """

    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None
    should_exit: bool = False

    @classmethod
    def ok(cls, message: str = "", data: Any = None) -> "CommandResult":
        """Fabrique un résultat de succès."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, error: Optional[str] = None) -> "CommandResult":
        """Fabrique un résultat d'échec."""
        return cls(success=False, message=message, error=error)

    @classmethod
    def exit(cls, message: str = "") -> "CommandResult":
        """Fabrique un résultat demandant la fin de la session interactive."""
        return cls(success=True, message=message, should_exit=True)


class CommandBase(ABC):
    """Classe de base abstraite pour l'ensemble des commandes du framework."""

    def __init__(
        self,
        name: str,
        description: str,
        usage: str,
        aliases: Optional[list[str]] = None,
    ) -> None:
        """Initialise une nouvelle commande.

        Args:
            name: Nom d'invocation principal de la commande (ex: 'ping').
            description: Explication courte de l'action réalisée.
            usage: Syntaxe d'utilisation (ex: 'ping <cible>').
            aliases: Liste d'alias alternatifs (ex: ['p'] pour ping).
        """
        self.name: str = name.strip().lower()
        self.description: str = description.strip()
        self.usage: str = usage.strip()
        self.aliases: list[str] = [a.strip().lower() for a in (aliases or [])]

    @abstractmethod
    def execute(self, args: list[str]) -> CommandResult:
        """Exécute la commande avec les arguments fournis.

        Args:
            args: Liste des arguments passés en ligne de commande.

        Returns:
            Une instance de CommandResult indiquant le statut et le contenu.
        """
        raise NotImplementedError("Chaque commande doit implémenter la méthode execute().")

    def format_help(self) -> str:
        """Génère la documentation d'aide de la commande."""
        alias_str = f" (alias: {', '.join(self.aliases)})" if self.aliases else ""
        return (
            f"Commande : {self.name}{alias_str}\n"
            f"Description : {self.description}\n"
            f"Utilisation : {self.usage}"
        )
