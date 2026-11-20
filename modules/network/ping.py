"""Module de diagnostic de connectivité ICMP (Ping).

Ce module prend en charge l'exécution multiplateforme de ping, la capture
des métriques RTT (min, avg, max, mdev) et l'analyse statistique des pertes de paquets.
Il est totalement découplé de la présentation terminal.
"""

import re
import subprocess
import time
from typing import Optional

from core.command_base import CommandBase, CommandResult
from core.logger import get_logger
from models.network_result import PingResult
from utils.formatter import format_badge, format_latency
from utils.platform_utils import build_ping_command, is_windows
from utils.validators import validate_target

logger = get_logger("modules.network.ping")

# Expressions régulières pour analyser les sorties de ping (Linux & Windows)
_RE_LINUX_IP = re.compile(r"PING\s+\S+\s+\(([0-9a-fA-F\.\:]+)\)")
_RE_LINUX_PACKETS = re.compile(
    r"(\d+)\s+packets transmitted,\s+(\d+)\s+(?:packets\s+)?received,\s+([0-9\.]+)%\s+packet loss"
)
_RE_LINUX_RTT = re.compile(
    r"rtt\s+min/avg/max/mdev\s*=\s*([0-9\.]+)/([0-9\.]+)/([0-9\.]+)/([0-9\.]+)\s+ms"
)

_RE_WIN_IP = re.compile(r"Pinging\s+\S+\s+\[([0-9a-fA-F\.\:]+)\]")
_RE_WIN_PACKETS = re.compile(
    r"Packets:\s+Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)\s*\(([0-9\.]+)%\s*loss\)"
)
_RE_WIN_RTT = re.compile(
    r"Minimum\s*=\s*(\d+)\s*ms,\s*Maximum\s*=\s*(\d+)\s*ms,\s*Average\s*=\s*(\d+)\s*ms"
)


def parse_ping_output(raw_output: str, target: str) -> PingResult:
    """Analyse la sortie texte brute de la commande ping pour extraire les métriques.

    Args:
        raw_output: Chaîne contenant stdout et stderr de ping.
        target: Nom d'hôte ou IP cible initiale.

    Returns:
        Instance de PingResult complétée avec les métriques extraites.
    """
    result = PingResult(
        target=target,
        operation="ping",
        raw_data={"output": raw_output},
    )

    if not raw_output:
        result.error_message = "Aucune réponse reçue (sortie vide)."
        return result

    # 1. Extraction de l'IP résolue
    match_ip = _RE_LINUX_IP.search(raw_output) or _RE_WIN_IP.search(raw_output)
    if match_ip:
        result.resolved_ip = match_ip.group(1)

    # 2. Extraction des paquets et pertes
    match_pkts = _RE_LINUX_PACKETS.search(raw_output)
    if match_pkts:
        result.packets_transmitted = int(match_pkts.group(1))
        result.packets_received = int(match_pkts.group(2))
        result.packet_loss_percent = float(match_pkts.group(3))
    else:
        match_win_pkts = _RE_WIN_PACKETS.search(raw_output)
        if match_win_pkts:
            result.packets_transmitted = int(match_win_pkts.group(1))
            result.packets_received = int(match_win_pkts.group(2))
            result.packet_loss_percent = float(match_win_pkts.group(4))

    # 3. Extraction des métriques de latence (RTT)
    match_rtt = _RE_LINUX_RTT.search(raw_output)
    if match_rtt:
        result.rtt_min_ms = float(match_rtt.group(1))
        result.rtt_avg_ms = float(match_rtt.group(2))
        result.rtt_max_ms = float(match_rtt.group(3))
        result.rtt_mdev_ms = float(match_rtt.group(4))
    else:
        match_win_rtt = _RE_WIN_RTT.search(raw_output)
        if match_win_rtt:
            result.rtt_min_ms = float(match_win_rtt.group(1))
            result.rtt_max_ms = float(match_win_rtt.group(2))
            result.rtt_avg_ms = float(match_win_rtt.group(3))

    # Détermination de l'état
    result.is_reachable = result.packets_received > 0
    result.success = result.is_reachable

    if not result.is_reachable:
        result.error_message = (
            f"100% de perte : l'hôte {target} ne répond pas aux requêtes ICMP Echo."
        )

    return result


def execute_ping(
    target: str,
    count: int = 4,
    timeout_sec: float = 3.0,
) -> PingResult:
    """Exécute un diagnostic ICMP complet vers la cible spécifiée.

    Args:
        target: Adresse IP ou nom de domaine à tester.
        count: Nombre de paquets ICMP (défaut: 4).
        timeout_sec: Délai d'attente maximum par sonde en secondes.

    Returns:
        PingResult structuré et validé.
    """
    clean_target, _ = validate_target(target)
    command = build_ping_command(clean_target, count=count, timeout_sec=timeout_sec)

    # Durée maximale globale allouée au processus ping
    total_timeout = max(5.0, (count * timeout_sec) + 3.0)

    start_time = time.perf_counter()
    logger.info(f"Démarrage diagnostic Ping vers {clean_target} ({count} paquets)")

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=total_timeout,
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        output = (process.stdout or "") + (process.stderr or "")
        result = parse_ping_output(output, target=clean_target)
        result.duration_ms = duration_ms

        logger.info(
            f"Ping {clean_target} terminé : reçu={result.packets_received}/{result.packets_transmitted}, "
            f"perte={result.packet_loss_percent}%, rtt_avg={result.rtt_avg_ms}ms"
        )
        return result

    except subprocess.TimeoutExpired:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.warning(f"Timeout global dépassé ({total_timeout}s) lors du ping vers {clean_target}")
        return PingResult(
            target=clean_target,
            operation="ping",
            success=False,
            duration_ms=duration_ms,
            packets_transmitted=count,
            packets_received=0,
            packet_loss_percent=100.0,
            error_message=f"Délai d'attente global dépassé ({total_timeout:.1f}s) sans réponse.",
        )

    except PermissionError as err:
        logger.error(f"Permission refusée pour exécuter ping : {err}")
        return PingResult(
            target=clean_target,
            operation="ping",
            success=False,
            error_message="Privilèges insuffisants pour exécuter l'utilitaire ping (accès raw socket requis).",
        )

    except Exception as err:
        logger.exception(f"Erreur imprévue lors du ping vers {clean_target}: {err}")
        return PingResult(
            target=clean_target,
            operation="ping",
            success=False,
            error_message=f"Erreur d'exécution de la sonde ICMP : {err}",
        )


class PingCommand(CommandBase):
    """Commande interactive pour le diagnostic ICMP Ping v2.0."""

    def __init__(self) -> None:
        super().__init__(
            name="ping",
            description="Teste la connectivité ICMP et calcule les statistiques de latence RTT.",
            usage="ping <cible> [nombre_paquets]",
            aliases=["p"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult.fail("Spécifie une cible valide. Exemple : ping 8.8.8.8")

        target = args[0]
        count = 4

        if len(args) >= 2:
            try:
                count = int(args[1])
                if not (1 <= count <= 30):
                    return CommandResult.fail("Le nombre de paquets doit être compris entre 1 et 30.")
            except ValueError:
                return CommandResult.fail("Le nombre de paquets doit être un entier valide.")

        print(f"[*] Envoi de {count} sondes ICMP vers {target}...")
        result = execute_ping(target=target, count=count)

        if not result.is_reachable:
            err_msg = result.error_message or "L'hôte cible ne répond pas aux paquets ICMP."
            return CommandResult.fail(message=err_msg, error=result.error_message)

        # Construction du compte-rendu formaté
        ip_display = f" ({result.resolved_ip})" if result.resolved_ip else ""
        lines = [
            f"Statut ICMP vers {result.target}{ip_display} : {format_badge('reachable')}",
            f"Paquets    : {result.packets_transmitted} envoyés, {result.packets_received} reçus, {result.packet_loss_percent:.1f}% perte",
        ]

        if result.rtt_avg_ms is not None:
            rtt_details = (
                f"RTT (ms)   : min={format_latency(result.rtt_min_ms)} | "
                f"avg={format_latency(result.rtt_avg_ms)} | "
                f"max={format_latency(result.rtt_max_ms)}"
            )
            if result.rtt_mdev_ms is not None:
                rtt_details += f" | gigue(mdev)={format_latency(result.rtt_mdev_ms)}"
            lines.append(rtt_details)

        lines.append(f"Durée test : {format_latency(result.duration_ms)}")

        return CommandResult.ok(message="\n".join(lines), data=result.to_dict())
