"""Shell interactif de Personal Framework CLI (Vue terminal).

Ce module implémente l'interface terminal via le module standard cmd.
Il n'héberge aucune logique réseau : il délègue l'intégralité du traitement
au CommandManager et met en forme les résultats pour l'utilisateur.
"""

import cmd
import shlex

from config.settings import (
    BANNER,
    COLOR_BOLD,
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
)
from core.command_manager import CommandManager


class PatersonShell(cmd.Cmd):
    """Interface interactive en ligne de commande pour Personal Framework."""

    prompt = f"{COLOR_RED}paterson{COLOR_RESET}({COLOR_CYAN}framework{COLOR_RESET}) > "
    intro = BANNER + f"\nTapez {COLOR_BOLD}help{COLOR_RESET} pour afficher la liste des commandes disponibles.\n"

    def __init__(self, command_manager: CommandManager) -> None:
        """Initialise le shell avec son gestionnaire de commandes associé.

        Args:
            command_manager: Instance du gestionnaire de commandes.
        """
        super().__init__()
        self.command_manager = command_manager

    def default(self, line: str) -> bool:
        """Point d'entrée pour toute commande saisie dans le shell.

        Découpe la ligne de commande, l'envoie au CommandManager et
        affiche le résultat en fonction de son statut.
        """
        raw = line.strip()
        if not raw:
            return False

        try:
            tokens = shlex.split(raw)
        except ValueError as err:
            print(f"{COLOR_RED}[!] Erreur de syntaxe dans la commande :{COLOR_RESET} {err}")
            return False

        command_name = tokens[0]
        args = tokens[1:]

        result = self.command_manager.execute(command_name, args)

        if result.message:
            if result.success:
                print(f"{COLOR_GREEN}{result.message}{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}[!] {result.message}{COLOR_RESET}")

        return result.should_exit

    def emptyline(self) -> bool:
        """Empêche la répétition automatique de la commande précédente sur appui Entrée."""
        return False

    def do_EOF(self, arg: str) -> bool:
        """Gère la fin de flux (Ctrl+D ou redirection d'entrée)."""
        print()
        return True

    def do_help(self, arg: str) -> None:
        """Affiche l'aide globale ou l'aide détaillée d'une commande spécifique."""
        target = arg.strip().lower()
        if target:
            cmd_obj = self.command_manager.get(target)
            if cmd_obj:
                print(f"\n{COLOR_CYAN}{cmd_obj.format_help()}{COLOR_RESET}\n")
            else:
                print(f"{COLOR_RED}[!] Aucune commande ou alias nommé '{target}'.{COLOR_RESET}")
            return

        commands = self.command_manager.list_commands()
        print(f"\n{COLOR_CYAN}{COLOR_BOLD}COMMANDES DISPONIBLES :{COLOR_RESET}")
        print("-" * 65)

        for cmd_obj in commands:
            aliases_str = f" ({', '.join(cmd_obj.aliases)})" if cmd_obj.aliases else ""
            header = f"{cmd_obj.name}{aliases_str}"
            print(f"  {COLOR_BOLD}{header:<22}{COLOR_RESET} : {cmd_obj.description}")

        print("-" * 65)
        print(f"Astuce : tapez {COLOR_BOLD}help <commande>{COLOR_RESET} pour la syntaxe détaillée.\n")

    def run(self) -> None:
        """Démarre la boucle interactive avec interception propre de Ctrl+C."""
        while True:
            try:
                self.cmdloop()
                break
            except KeyboardInterrupt:
                print(f"\n{COLOR_YELLOW}[*] Action annulée (Ctrl+C). Tapez 'exit' pour quitter.{COLOR_RESET}")
