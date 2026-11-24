"""Modèles de données pour le diagnostic et l'analyse des ports TCP (Portscan).

Ce module définit les structures typées représentant les états d'un port,
les informations de service associées et le résultat global d'un scan.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional

from models.network_result import NetworkResult


class PortState(str, Enum):
    """État observé d'un port TCP selon la RFC 793 et les réponses socket."""

    OPEN = "open"  # Connexion TCP établie avec succès (SYN-ACK reçu)
    CLOSED = "closed"  # Connexion rejetée explicitement (RST reçu / ECONNREFUSED)
    FILTERED = "filtered"  # Sonde sans réponse (DROP par pare-feu ou timeout)
    ERROR = "error"  # Anomalie de communication ou de résolution


@dataclass
class PortScanItem:
    """Résultat unitaire d'observation d'un port TCP.

    Attributes:
        port: Numéro de port TCP (1 à 65535).
        state: État observé (OPEN, CLOSED, FILTERED, ERROR).
        service_name: Nom du service standard IANA associé (ex: 'ssh', 'http').
        service_certainty: Niveau de certitude ('observed', 'presumed_by_port').
        rtt_ms: Temps d'aller-retour de la connexion en millisecondes.
        banner: Bannière d'accueil passive éventuelle (ex: 'OpenSSH_8.9').
        error_details: Détail technique si state == ERROR.
    """

    port: int
    state: PortState
    service_name: Optional[str] = None
    service_certainty: str = "presumed_by_port"
    rtt_ms: Optional[float] = None
    banner: Optional[str] = None
    error_details: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'élément en dictionnaire sérialisable."""
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass
class ScanResult(NetworkResult):
    """Résultat agrégé d'une opération de scan de ports TCP sur une cible.

    Attributes:
        ports_scanned_count: Nombre total de ports testés.
        items: Liste détaillée des observations par port.
        open_ports: Liste filtrée des ports ouverts.
        closed_count: Nombre total de ports fermés.
        filtered_count: Nombre total de ports filtrés (ou sans réponse).
    """

    ports_scanned_count: int = 0
    items: list[PortScanItem] = field(default_factory=list)
    open_ports: list[PortScanItem] = field(default_factory=list)
    closed_count: int = 0
    filtered_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convertit le résultat complet en dictionnaire sérialisable."""
        data = super().to_dict()
        data["items"] = [item.to_dict() for item in self.items]
        data["open_ports"] = [item.to_dict() for item in self.open_ports]
        return data
