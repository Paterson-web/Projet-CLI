"""Passerelles de transition pour les commandes initiales v1.1.0 (ping, portscan).

Ces commandes permettent de conserver le comportement d'origine de v1.1.0
au sein de la nouvelle architecture en attendant les étapes de refactorisation
dédiées (Étape 4 pour Ping et Étape 5 pour Portscan).
"""

import socket
import subprocess
import sys

from core.command_base import CommandBase, CommandResult


class PingLegacyCommand(CommandBase):
    """Commande de transition pour la connectivité ICMP (v1.1.0)."""

    def __init__(self) -> None:
        super().__init__(
            name="ping",
            description="Teste la connectivité ICMP vers un hôte distant (mode transitoire v1.1.0).",
            usage="ping <cible>",
            aliases=["p"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult.fail("Spécifie une cible valide (ex: ping 8.8.8.8)")

        target = args[0]
        param = "-c" if sys.platform != "win32" else "-n"
        command = ["ping", param, "4", target]

        try:
            print(f"[*] Envoi de paquets ICMP vers {target}...")
            res = subprocess.run(command, capture_output=False, timeout=10)
            if res.returncode == 0:
                return CommandResult.ok(message=f"Ping vers {target} terminé avec succès.")
            return CommandResult.fail(
                message=f"La cible {target} n'a pas répondu à l'ensemble des paquets ICMP."
            )
        except subprocess.TimeoutExpired:
            return CommandResult.fail(message=f"Délai d'attente dépassé lors du ping vers {target}.")
        except Exception as err:
            return CommandResult.fail(message=f"Erreur d'exécution du ping : {err}", error=str(err))


class PortscanLegacyCommand(CommandBase):
    """Commande de transition pour le scan de port TCP (v1.1.0)."""

    def __init__(self) -> None:
        super().__init__(
            name="portscan",
            description="Vérifie l'accessibilité d'un port TCP unique (mode transitoire v1.1.0).",
            usage="portscan <cible> <port>",
            aliases=["scan"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult.fail("Utilisation : portscan <cible> <port> (ex: portscan 127.0.0.1 80)")

        target = args[0]
        try:
            port = int(args[1])
            if not (1 <= port <= 65535):
                return CommandResult.fail("Le numéro de port doit être compris entre 1 et 65535.")
        except ValueError:
            return CommandResult.fail("Le port doit être un nombre entier valide.")

        print(f"[*] Scan du port {port} sur {target} (timeout 2.0s)...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)

        try:
            result = sock.connect_ex((target, port))
            if result == 0:
                return CommandResult.ok(
                    message=f"[+][SUCCESS] Le port {port} est OUVERT sur {target}.",
                    data={"target": target, "port": port, "state": "open"},
                )
            return CommandResult.ok(
                message=f"[-][CLOSED] Le port {port} est fermé ou filtré sur {target}.",
                data={"target": target, "port": port, "state": "closed_or_filtered"},
            )
        except socket.gaierror:
            return CommandResult.fail(message=f"Impossible de résoudre l'adresse de l'hôte '{target}'.")
        except Exception as err:
            return CommandResult.fail(message=f"Erreur réseau : {err}", error=str(err))
        finally:
            sock.close()
