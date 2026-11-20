"""Modèle de base abstrait pour tous les résultats de diagnostic réseau.

Ce module garantit que l'ensemble des modules réseau (ping, portscan, dns,
traceroute, discovery) retournent des structures typées, documentées
et sérialisables pour les rapports et l'historique.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class NetworkResult:
    """Structure commune pour tout résultat d'analyse ou de diagnostic réseau.

    Attributes:
        target: Cible analysée (nom d'hôte, IP ou réseau CIDR).
        operation: Nom du diagnostic réseau réalisé (ex: 'ping', 'portscan', 'dns').
        success: True si l'opération a pu s'exécuter jusqu'à son terme.
        resolved_ip: Adresse IP effective résolue pour la cible (si applicable).
        start_timestamp: Horodatage de début (ISO 8601).
        duration_ms: Durée totale de l'opération en millisecondes.
        error_message: Détail textuel de l'anomalie en cas d'échec partiel ou total.
        raw_data: Dictionnaire flexible contenant les données détaillées spécifiques au protocole.
    """

    target: str
    operation: str
    success: bool = False
    resolved_ip: Optional[str] = None
    start_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'objet résultat en dictionnaire sérialisable (JSON / YAML / CSV)."""
        return asdict(self)


@dataclass
class PingResult(NetworkResult):
    """Résultat structuré spécifique au diagnostic de connectivité ICMP (Ping).

    Attributes:
        packets_transmitted: Nombre de paquets envoyés.
        packets_received: Nombre de paquets reçus avec succès.
        packet_loss_percent: Taux de perte en pourcentage (0.0% à 100.0%).
        rtt_min_ms: Temps de boucle minimum mesuré en millisecondes.
        rtt_avg_ms: Temps de boucle moyen en millisecondes.
        rtt_max_ms: Temps de boucle maximum en millisecondes.
        rtt_mdev_ms: Écart-type / gigue (jitter) en millisecondes.
        is_reachable: True si au moins un paquet a reçu une réponse ICMP Echo Reply.
    """

    packets_transmitted: int = 0
    packets_received: int = 0
    packet_loss_percent: float = 100.0
    rtt_min_ms: Optional[float] = None
    rtt_avg_ms: Optional[float] = None
    rtt_max_ms: Optional[float] = None
    rtt_mdev_ms: Optional[float] = None
    is_reachable: bool = False
