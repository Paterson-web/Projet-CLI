"""Tests unitaires complets des validateurs de saisie réseau (utils.validators)."""

import unittest

from core.exceptions import ValidationError
from utils.validators import (
    validate_domain,
    validate_ip,
    validate_network,
    validate_port,
    validate_port_range,
    validate_target,
)


class TestValidators(unittest.TestCase):
    """Vérifie la robustesse de chaque validateur face à des entrées conformes et malicieuses."""

    # --- Tests validate_ip ---
    def test_validate_ip_valid(self) -> None:
        """Vérifie l'acceptation d'adresses IPv4 et IPv6 valides."""
        v4 = validate_ip("192.168.1.1")
        self.assertEqual(str(v4), "192.168.1.1")
        self.assertEqual(v4.version, 4)

        v6 = validate_ip("2001:db8::1")
        self.assertEqual(str(v6), "2001:db8::1")
        self.assertEqual(v6.version, 6)

    def test_validate_ip_invalid(self) -> None:
        """Vérifie le rejet des adresses IP syntaxiquement incorrectes."""
        invalid_ips = ["256.0.0.1", "192.168.1", "not_an_ip", "1.2.3.4.5", ""]
        for bad in invalid_ips:
            with self.assertRaises(ValidationError, msg=f"Doit rejeter : {bad}"):
                validate_ip(bad)

    # --- Tests validate_network ---
    def test_validate_network_valid(self) -> None:
        """Vérifie la validation de blocs CIDR IPv4 et IPv6."""
        net = validate_network("192.168.1.0/24")
        self.assertEqual(str(net), "192.168.1.0/24")

        # Accepte une adresse d'hôte avec masque sans lever d'erreur
        host_net = validate_network("10.0.0.45/8")
        self.assertEqual(str(host_net), "10.0.0.0/8")

    def test_validate_network_invalid(self) -> None:
        """Vérifie le rejet de blocs réseaux CIDR invalides."""
        for bad in ["192.168.1.0/33", "10.0.0.0/abc", "non_cidr", ""]:
            with self.assertRaises(ValidationError):
                validate_network(bad)

    # --- Tests validate_port ---
    def test_validate_port_valid(self) -> None:
        """Vérifie les bornes valides de ports TCP/UDP (1 et 65535) et valeurs courantes."""
        self.assertEqual(validate_port(1), 1)
        self.assertEqual(validate_port(80), 80)
        self.assertEqual(validate_port("443"), 443)
        self.assertEqual(validate_port(65535), 65535)

    def test_validate_port_invalid(self) -> None:
        """Vérifie le rejet du port 0, des nombres négatifs et des ports > 65535."""
        invalid_ports = [0, -1, 65536, 70000, "abc", ""]
        for bad in invalid_ports:
            with self.assertRaises(ValidationError, msg=f"Doit rejeter : {bad}"):
                validate_port(bad)

    # --- Tests validate_port_range ---
    def test_validate_port_range_valid(self) -> None:
        """Vérifie l'analyse de ports simples, listes séparées par virgules et plages avec tiret."""
        # Port unique
        self.assertEqual(validate_port_range("80"), [80])
        # Liste
        self.assertEqual(validate_port_range("80, 443, 8080"), [80, 443, 8080])
        # Plage
        self.assertEqual(validate_port_range("20-23"), [20, 21, 22, 23])
        # Mixte avec dédoublonnement et tri automatique
        self.assertEqual(validate_port_range("80, 21-23, 80, 22"), [21, 22, 23, 80])

    def test_validate_port_range_inverted_or_invalid(self) -> None:
        """Vérifie le rejet des plages inversées (ex: 80-20) et des formats corrompus."""
        with self.assertRaises(ValidationError):
            validate_port_range("80-20")
        with self.assertRaises(ValidationError):
            validate_port_range("20-25-30")

    def test_validate_port_range_cap_limit(self) -> None:
        """Vérifie que la limite de sécurité max_allowed est respectée pour éviter les surcharges."""
        with self.assertRaises(ValidationError):
            validate_port_range("1-100", max_allowed=50)

    # --- Tests validate_domain ---
    def test_validate_domain_valid(self) -> None:
        """Vérifie l'acceptation de noms d'hôtes et domaines conformes à la RFC 1123."""
        self.assertEqual(validate_domain("google.com"), "google.com")
        self.assertEqual(validate_domain("sub-domain.example.co.uk"), "sub-domain.example.co.uk")
        self.assertEqual(validate_domain("localhost"), "localhost")

    def test_validate_domain_invalid(self) -> None:
        """Vérifie le rejet de noms de domaine illégaux."""
        invalid_domains = [
            "-badstart.com",
            "badend-.com",
            "domain..com",
            "has space.com",
            "",
            "a" * 255 + ".com",
        ]
        for bad in invalid_domains:
            with self.assertRaises(ValidationError, msg=f"Doit rejeter : {bad}"):
                validate_domain(bad)

    # --- Tests validate_target (Sécurité & Injection) ---
    def test_validate_target_detection(self) -> None:
        """Vérifie la détection automatique du type de cible (IPv4, IPv6, domaine)."""
        target, target_type = validate_target("8.8.8.8")
        self.assertEqual(target, "8.8.8.8")
        self.assertEqual(target_type, "ipv4")

        target_v6, type_v6 = validate_target("::1")
        self.assertEqual(target_v6, "::1")
        self.assertEqual(type_v6, "ipv6")

        target_dom, type_dom = validate_target("scanme.nmap.org")
        self.assertEqual(target_dom, "scanme.nmap.org")
        self.assertEqual(type_dom, "domain")

    def test_validate_target_injection_guard(self) -> None:
        """Vérifie le blocage immédiat des chaînes débutant par un tiret (injection de flags CLI)."""
        with self.assertRaises(ValidationError):
            validate_target("-c 1 8.8.8.8")
        with self.assertRaises(ValidationError):
            validate_target("--help")


if __name__ == "__main__":
    unittest.main()
