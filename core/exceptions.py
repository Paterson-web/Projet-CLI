"""Hiérarchie centralisée des exceptions de Personal Framework CLI.

Toutes les exceptions du framework héritent de FrameworkError,
permettant une capture globale et une distinction nette entre
erreurs de validation utilisateur, erreurs d'exécution réseau,
et problèmes de configuration système.
"""


class FrameworkError(Exception):
    """Exception racine pour toutes les erreurs spécifiques au framework."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class ConfigurationError(FrameworkError):
    """Levée lorsqu'une incohérence ou un manque survient dans la configuration."""
    pass


class ValidationError(FrameworkError):
    """Levée lorsqu'une entrée utilisateur (IP, port, domaine, etc.) est invalide."""
    pass


class NetworkExecutionError(FrameworkError):
    """Exception de base pour les échecs lors des opérations réseau."""
    pass


class HostUnreachableError(NetworkExecutionError):
    """Levée lorsqu'une cible réseau ne répond pas ou est introuvable."""
    pass


class OperationTimeoutError(NetworkExecutionError):
    """Levée lorsqu'une opération réseau dépasse le délai d'attente alloué."""
    pass


class CommandError(FrameworkError):
    """Levée lors d'un échec de distribution ou d'exécution d'une commande CLI."""
    pass


class CommandNotFoundError(CommandError):
    """Levée lorsqu'une commande sollicitée n'est pas enregistrée dans le CommandManager."""
    pass


class InsufficientPrivilegeError(FrameworkError):
    """Levée lorsqu'une opération nécessite des privilèges non disponibles (ex: root/sudo pour raw socket)."""
    pass
