"""Module d'analyse et de scan des ports TCP (Portscan v2.0).

Ce module implémente un scanner TCP multi-threadé avec contrôle strict
de la concurrence, gestion des timeouts, support IPv4/IPv6, distinction fine
entre ports fermés et filtrés, et résolution prudente des services IANA.
"""

import concurrent.futures
import errno
import socket
import time
from typing import Optional

from config.settings import DEFAULT_SCAN_PORTS, DEFAULT_SOCKET_TIMEOUT, MAX_SCAN_CONCURRENCY
from core.command_base import CommandBase, CommandResult
from core.logger import get_logger
from models.scan_result import PortScanItem, PortState, ScanResult
from utils.formatter import format_badge, format_latency, format_table
from utils.validators import validate_port_range, validate_target

logger = get_logger("modules.network.portscan")

# Dictionnaire de secours pour les ports les plus fréquents (au cas où getservbyport échoue)
_WELL_KNOWN_SERVICES: dict[int, str] = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "domain (dns)",
    80: "http",
    110: "pop3",
    111: "rpcbind",
    135: "msrpc",
    139: "netbios-ssn",
    143: "imap",
    443: "https",
    445: "microsoft-ds (smb)",
    993: "imaps",
    995: "pop3s",
    1433: "ms-sql-s",
    1521: "oracle",
    3306: "mysql",
    3389: "ms-wbt-server (rdp)",
    5432: "postgresql",
    5900: "vnc",
    6379: "redis",
    8000: "http-alt",
    8080: "http-proxy",
    8443: "https-alt",
    9000: "cslistener",
    27017: "mongodb",
}


def lookup_service_name(port: int) -> str:
    """Identifie le nom de service usuel associé au port selon l'IANA.

    Args:
        port: Numéro de port TCP (1-65535).

    Returns:
        Nom textuel du service standard présumé (ou 'inconnu').
    """
    try:
        return socket.getservbyport(port, "tcp")
    except (OSError, socket.error):
        return _WELL_KNOWN_SERVICES.get(port, "inconnu")


def scan_single_port(
    target_ip: str,
    port: int,
    family: int = socket.AF_INET,
    timeout_sec: float = DEFAULT_SOCKET_TIMEOUT,
) -> PortScanItem:
    """Tente une connexion TCP standard (3-way handshake) sur un port unique.

    Distingue rigoureusement :
    - OPEN (code 0)
    - CLOSED (connexion refusée, RST renvoyé par la machine)
    - FILTERED (dépassement de délai, pare-feu qui jette la sonde)

    Args:
        target_ip: Adresse IP directe (v4 ou v6) de l'hôte.
        port: Numéro de port à tester.
        family: Famille de socket (AF_INET ou AF_INET6).
        timeout_sec: Délai d'attente maximum pour la connexion.

    Returns:
        Instance de PortScanItem avec l'état et les métriques observées.
    """
    service_name = lookup_service_name(port)
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(timeout_sec)

    start_time = time.perf_counter()
    try:
        code = sock.connect_ex((target_ip, port))
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if code == 0:
            # Port OUVERT : tentative prudente de capture passive de bannière
            banner: Optional[str] = None
            try:
                sock.settimeout(0.3)
                raw_banner = sock.recv(256)
                if raw_banner:
                    banner = raw_banner.decode("utf-8", errors="replace").strip()
            except Exception:
                banner = None

            return PortScanItem(
                port=port,
                state=PortState.OPEN,
                service_name=service_name,
                rtt_ms=duration_ms,
                banner=banner,
            )

        # Codes d'erreurs TCP standards (rejet explicite vs timeout)
        closed_codes = {errno.ECONNREFUSED}
        if hasattr(errno, "WSAECONNREFUSED"):
            closed_codes.add(getattr(errno, "WSAECONNREFUSED"))

        if code in closed_codes:
            return PortScanItem(
                port=port,
                state=PortState.CLOSED,
                service_name=service_name,
                rtt_ms=duration_ms,
            )

        # Autres codes (timeout, hôte inaccessible, filtrage silencieux)
        return PortScanItem(
            port=port,
            state=PortState.FILTERED,
            service_name=service_name,
            error_details=f"errno={code}",
        )

    except (socket.timeout, TimeoutError):
        return PortScanItem(
            port=port,
            state=PortState.FILTERED,
            service_name=service_name,
            error_details="Timeout de connexion dépassé",
        )
    except Exception as err:
        return PortScanItem(
            port=port,
            state=PortState.ERROR,
            service_name=service_name,
            error_details=str(err),
        )
    finally:
        sock.close()


def execute_portscan(
    target: str,
    ports: list[int],
    max_workers: int = 20,
    timeout_sec: float = DEFAULT_SOCKET_TIMEOUT,
) -> ScanResult:
    """Orchestre un scan de ports concurrent et contrôlé sur une cible autorisée.

    Args:
        target: Nom d'hôte ou adresse IP cible.
        ports: Liste des numéros de ports à analyser.
        max_workers: Nombre maximal de threads simultanés (plafond de concurrence).
        timeout_sec: Délai d'attente par socket en secondes.

    Returns:
        Instance structurée de ScanResult.
    """
    clean_target, target_type = validate_target(target)
    start_total = time.perf_counter()

    # 1. Résolution de l'adresse IP et détection de la famille (v4/v6)
    try:
        addrinfo = socket.getaddrinfo(
            clean_target,
            None,
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )
        if not addrinfo:
            raise socket.gaierror("Aucune adresse IP trouvée pour cette cible.")
        # Utiliser la première adresse résolue
        family, _, _, _, sockaddr = addrinfo[0]
        resolved_ip = sockaddr[0]
    except socket.gaierror as err:
        logger.error(f"Échec de résolution DNS pour {clean_target} : {err}")
        return ScanResult(
            target=clean_target,
            operation="portscan",
            success=False,
            error_message=f"Impossible de résoudre le nom d'hôte '{clean_target}' : {err}",
        )

    # 2. Préparation du pool de concurrence
    concurrency = min(len(ports), max_workers, MAX_SCAN_CONCURRENCY)
    concurrency = max(1, concurrency)

    logger.info(
        f"Lancement portscan vers {clean_target} ({resolved_ip}) : "
        f"{len(ports)} ports avec {concurrency} threads"
    )

    items: list[PortScanItem] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_port = {
            executor.submit(
                scan_single_port,
                target_ip=resolved_ip,
                port=p,
                family=family,
                timeout_sec=timeout_sec,
            ): p
            for p in ports
        }

        for future in concurrent.futures.as_completed(future_to_port):
            try:
                item = future.result()
                items.append(item)
            except Exception as err:
                port = future_to_port[future]
                items.append(
                    PortScanItem(
                        port=port,
                        state=PortState.ERROR,
                        error_details=f"Thread error: {err}",
                    )
                )

    # Tri ordonné des résultats par numéro de port
    items.sort(key=lambda x: x.port)

    # Agrégation des statistiques
    open_ports = [it for it in items if it.state == PortState.OPEN]
    closed_count = sum(1 for it in items if it.state == PortState.CLOSED)
    filtered_count = sum(1 for it in items if it.state == PortState.FILTERED)
    duration_ms = (time.perf_counter() - start_total) * 1000.0

    logger.info(
        f"Scan terminé en {duration_ms:.1f}ms : {len(open_ports)} ouverts, "
        f"{closed_count} fermés, {filtered_count} filtrés."
    )

    return ScanResult(
        target=clean_target,
        operation="portscan",
        success=True,
        resolved_ip=resolved_ip,
        duration_ms=duration_ms,
        ports_scanned_count=len(ports),
        items=items,
        open_ports=open_ports,
        closed_count=closed_count,
        filtered_count=filtered_count,
        raw_data={"concurrency": concurrency, "target_type": target_type},
    )


class PortscanCommand(CommandBase):
    """Commande interactive pour le scan de ports TCP v2.0."""

    def __init__(self) -> None:
        super().__init__(
            name="portscan",
            description="Vérifie l'accessibilité de ports TCP et identifie les services associés.",
            usage="portscan <cible> [ports (ex: 80 | 80,443 | 20-25 | defaut: ports usuels)]",
            aliases=["scan", "ps"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult.fail(
                "Spécifie au moins une cible réseau.\n"
                "Exemples :\n"
                "  portscan 127.0.0.1           (teste les 18 ports usuels)\n"
                "  portscan 127.0.0.1 80,443    (teste deux ports précis)\n"
                "  portscan 127.0.0.1 20-25     (teste une plage)"
            )

        target = args[0]
        # Si aucun port n'est spécifié, on utilise la liste par défaut sécurisée
        if len(args) >= 2:
            try:
                ports = validate_port_range(args[1], max_allowed=1000)
            except Exception as err:
                return CommandResult.fail(str(err))
        else:
            ports = list(DEFAULT_SCAN_PORTS)

        print(
            f"[*] Démarrage du scan TCP sur {target} ({len(ports)} port(s) ciblé(s))..."
        )

        result = execute_portscan(target=target, ports=ports, max_workers=25)

        if not result.success:
            return CommandResult.fail(
                result.error_message or "Échec de l'exécution du scan."
            )

        # Construction du tableau de restitution
        headers = ["PORT", "ÉTAT", "SERVICE (IANA)", "LATENCE (RTT)", "BANNIÈRE"]
        rows: list[list[str]] = []

        # Afficher en priorité les ports ouverts
        for item in result.items:
            # Pour éviter d'inonder le terminal, on n'affiche que les ports ouverts et filtrés
            if item.state in (PortState.OPEN, PortState.FILTERED):
                rows.append([
                    f"{item.port}/tcp",
                    format_badge(item.state.value),
                    item.service_name or "-",
                    format_latency(item.rtt_ms),
                    item.banner or "-",
                ])

        lines: list[str] = []
        ip_info = f" ({result.resolved_ip})" if result.resolved_ip else ""
        lines.append(f"Résultats pour {result.target}{ip_info} :")

        if rows:
            lines.append(format_table(headers=headers, rows=rows))
        else:
            lines.append("  Aucun port ouvert ou filtré détecté.")

        lines.append(
            f"\nSynthèse : {len(result.open_ports)} ouvert(s), "
            f"{result.closed_count} fermé(s), {result.filtered_count} filtré(s) "
            f"(analysés en {format_latency(result.duration_ms)})"
        )

        return CommandResult.ok(message="\n".join(lines), data=result.to_dict())
