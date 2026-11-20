"""Validateurs d'entrées réseau et système.

Ce module centralise la validation rigoureuse des adresses IP (IPv4/IPv6),
des blocs de sous-réseaux CIDR, des numéros et plages de ports TCP/UDP,
ainsi que des noms de domaine selon les RFC en vigueur (RFC 791, RFC 2460, RFC 1123).
"""

import ipaddress
import re
from typing import Union

from core.exceptions import ValidationError

# Expression régulière RFC 1123 pour les noms d'hôtes et FQDN
# - Longueur maximale du label : 63 caractères
# - Ne commence ni ne finit par un tiret
# - Composé uniquement de lettres, chiffres et tirets
_DOMAIN_REGEX = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.?$"
)


def validate_ip(value: str) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
    """Valide qu'une chaîne est une adresse IPv4 ou IPv6 syntaxiquement correcte.

    Args:
        value: Chaîne représentant l'adresse IP (ex: '192.168.1.1' ou '::1').

    Returns:
        Instance de IPv4Address ou IPv6Address.

    Raises:
        ValidationError: Si l'adresse est invalide ou malformée.
    """
    clean_val = str(value).strip()
    if not clean_val:
        raise ValidationError("L'adresse IP ne peut pas être vide.")

    try:
        return ipaddress.ip_address(clean_val)
    except ValueError as err:
        raise ValidationError(
            f"L'adresse '{clean_val}' n'est pas une adresse IP valide.",
            details=str(err),
        )


def validate_network(value: str) -> Union[ipaddress.IPv4Network, ipaddress.IPv6Network]:
    """Valide qu'une chaîne représente un sous-réseau avec préfixe CIDR (ex: '192.168.1.0/24').

    Args:
        value: Bloc CIDR à valider.

    Returns:
        Instance de IPv4Network ou IPv6Network.

    Raises:
        ValidationError: Si la syntaxe CIDR ou le masque est incorrect.
    """
    clean_val = str(value).strip()
    if not clean_val:
        raise ValidationError("Le préfixe réseau ne peut pas être vide.")

    try:
        # strict=False permet d'accepter une adresse d'hôte avec son masque (ex: 192.168.1.50/24)
        return ipaddress.ip_network(clean_val, strict=False)
    except ValueError as err:
        raise ValidationError(
            f"Le bloc réseau CIDR '{clean_val}' est invalide.",
            details=str(err),
        )


def validate_port(value: Union[int, str]) -> int:
    """Valide qu'un numéro de port se situe dans la plage standard TCP/UDP (1 à 65535).

    Le port 0 est réservé dans les piles sockets et ne doit pas être utilisé
    pour un scan ou un diagnostic conventionnel.

    Args:
        value: Entier ou chaîne convertible en entier représentant le port.

    Returns:
        Numéro de port sous forme d'entier validé.

    Raises:
        ValidationError: Si le port n'est pas un entier ou se situe hors limites.
    """
    try:
        port = int(str(value).strip())
    except (ValueError, TypeError):
        raise ValidationError(
            f"Le port '{value}' n'est pas un nombre entier valide.",
            details="Conversion impossible en entier",
        )

    if not (1 <= port <= 65535):
        raise ValidationError(
            f"Le port {port} est hors limites. La plage autorisée est de 1 à 65535.",
            details=f"port={port}",
        )

    return port


def validate_port_range(value: str, max_allowed: int = 1000) -> list[int]:
    """Analyse et valide une liste ou plage de ports (ex: '80', '80,443', '20-25').

    Args:
        value: Chaîne décrivant un ou plusieurs ports.
        max_allowed: Nombre maximal de ports autorisés pour un scan unitaire.

    Returns:
        Liste triée et dédoublonnée des ports valides.

    Raises:
        ValidationError: Si la syntaxe est erronée ou si le nombre dépasse la limite.
    """
    clean_val = str(value).strip()
    if not clean_val:
        raise ValidationError("La spécification de ports ne peut pas être vide.")

    ports_set: set[int] = set()
    segments = [s.strip() for s in clean_val.split(",") if s.strip()]

    if not segments:
        raise ValidationError("Format de ports invalide.")

    for segment in segments:
        if "-" in segment:
            # Plage de type debut-fin
            parts = segment.split("-")
            if len(parts) != 2:
                raise ValidationError(f"Plage de ports invalide : '{segment}'. Format attendu : debut-fin")
            start = validate_port(parts[0])
            end = validate_port(parts[1])
            if start > end:
                raise ValidationError(
                    f"Plage inversée : {start} est supérieur à {end}.",
                    details=f"{start}>{end}",
                )
            ports_set.update(range(start, end + 1))
        else:
            ports_set.add(validate_port(segment))

    if len(ports_set) > max_allowed:
        raise ValidationError(
            f"Le nombre de ports demandés ({len(ports_set)}) dépasse la limite maximale autorisée ({max_allowed}).",
            details=f"count={len(ports_set)}, max={max_allowed}",
        )

    return sorted(ports_set)


def validate_domain(value: str) -> str:
    """Valide qu'une chaîne est un nom d'hôte ou domaine pleinement qualifié (FQDN).

    Args:
        value: Nom de domaine ou hostname (ex: 'example.com', 'google.fr').

    Returns:
        Nom de domaine validé en minuscules sans point final.

    Raises:
        ValidationError: Si la syntaxe RFC 1123 est violée.
    """
    clean_val = str(value).strip().rstrip(".").lower()
    if not clean_val:
        raise ValidationError("Le nom de domaine ne peut pas être vide.")

    if len(clean_val) > 253:
        raise ValidationError("Le nom de domaine dépasse la taille maximale de 253 caractères.")

    if not _DOMAIN_REGEX.match(clean_val):
        raise ValidationError(
            f"Le nom d'hôte ou domaine '{clean_val}' n'est pas conforme aux spécifications RFC 1123.",
            details="Caractères non autorisés ou syntaxe de label invalide",
        )

    return clean_val


def validate_target(value: str) -> tuple[str, str]:
    """Identifie et valide la cible d'un diagnostic réseau (IPv4, IPv6 ou Domaine).

    Empêche formellement l'injection de drapeaux de commande (ex: arguments commençant par '-').

    Args:
        value: Cible saisie par l'utilisateur.

    Returns:
        Tuple (cible_nettoyée, type_cible) où type_cible vaut 'ipv4', 'ipv6' ou 'domain'.

    Raises:
        ValidationError: Si la cible est invalide ou suspecte.
    """
    clean_val = str(value).strip()
    if not clean_val:
        raise ValidationError("La cible réseau ne peut pas être vide.")

    # Sécurité défensive : interdire les chaînes commençant par '-' (drapeaux CLI injectés)
    if clean_val.startswith("-"):
        raise ValidationError(
            f"Cible invalide : '{clean_val}'. Une cible réseau ne peut pas débuter par un tiret.",
            details="Argument injection guard",
        )

    # 1. Tentative d'interprétation comme adresse IP directe
    try:
        ip_obj = ipaddress.ip_address(clean_val)
        ip_type = "ipv4" if ip_obj.version == 4 else "ipv6"
        return str(ip_obj), ip_type
    except ValueError:
        pass

    # 2. Tentative d'interprétation comme nom d'hôte / FQDN
    domain = validate_domain(clean_val)
    return domain, "domain"
