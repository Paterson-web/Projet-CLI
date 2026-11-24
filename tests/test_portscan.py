"""Tests unitaires du scanner de ports TCP (modules.network.portscan)."""

import socket
import threading
import unittest

from models.scan_result import PortState
from modules.network.portscan import (
    PortscanCommand,
    execute_portscan,
    lookup_service_name,
    scan_single_port,
)


class TestPortscanModule(unittest.TestCase):
    """Vérifie le comportement du scanner TCP en conditions réelles et locales."""

    @classmethod
    def setUpClass(cls) -> None:
        """Démarre un serveur TCP d'écoute local sur un port éphémère pour les tests."""
        cls.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.server_sock.bind(("127.0.0.1", 0))
        cls.server_sock.listen(5)
        cls.open_port = cls.server_sock.getsockname()[1]

        # Port fermé garanti : on prend open_port + 1 si libre
        cls.closed_port = cls.open_port + 1

        cls._stop_event = threading.Event()

        def _echo_server() -> None:
            while not cls._stop_event.is_set():
                try:
                    cls.server_sock.settimeout(0.2)
                    client, _ = cls.server_sock.accept()
                    client.close()
                except socket.timeout:
                    continue
                except OSError:
                    break

        cls.server_thread = threading.Thread(target=_echo_server, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        """Arrête proprement le serveur d'écoute."""
        cls._stop_event.set()
        cls.server_sock.close()
        cls.server_thread.join(timeout=1.0)

    def test_lookup_service_name(self) -> None:
        """Vérifie l'identification correcte des services standards IANA."""
        self.assertEqual(lookup_service_name(80), "http")
        self.assertEqual(lookup_service_name(22), "ssh")
        self.assertEqual(lookup_service_name(443), "https")
        self.assertEqual(lookup_service_name(65534), "inconnu")

    def test_scan_single_port_open(self) -> None:
        """Vérifie la détection d'un port ouvert en écoute sur 127.0.0.1."""
        item = scan_single_port("127.0.0.1", self.open_port, timeout_sec=1.0)
        self.assertEqual(item.state, PortState.OPEN)
        self.assertEqual(item.port, self.open_port)
        self.assertIsNotNone(item.rtt_ms)

    def test_scan_single_port_closed(self) -> None:
        """Vérifie qu'un port sans écoute renvoie CLOSED (rejet RST immédiat)."""
        item = scan_single_port("127.0.0.1", self.closed_port, timeout_sec=1.0)
        self.assertEqual(item.state, PortState.CLOSED)
        self.assertEqual(item.port, self.closed_port)

    def test_execute_portscan_aggregated(self) -> None:
        """Vérifie l'agrégation ordonnée des résultats dans ScanResult."""
        target_ports = [self.open_port, self.closed_port]
        result = execute_portscan("127.0.0.1", ports=target_ports, max_workers=2)

        self.assertTrue(result.success)
        self.assertEqual(result.ports_scanned_count, 2)
        self.assertEqual(len(result.open_ports), 1)
        self.assertEqual(result.open_ports[0].port, self.open_port)
        self.assertGreaterEqual(result.closed_count, 1)

    def test_execute_portscan_unresolvable_host(self) -> None:
        """Vérifie la gestion d'un nom de domaine introuvable sans crash."""
        result = execute_portscan("domaine-qui-nexiste-pas-du-tout-1234.local", ports=[80])
        self.assertFalse(result.success)
        self.assertIn("Impossible de résoudre", result.error_message or "")

    def test_portscan_command_validation(self) -> None:
        """Vérifie les validations de la commande CLI PortscanCommand."""
        cmd = PortscanCommand()

        # Sans argument
        res_no_arg = cmd.execute([])
        self.assertFalse(res_no_arg.success)
        self.assertIn("Spécifie au moins une cible", res_no_arg.message)

        # Avec plage inversée
        res_bad_range = cmd.execute(["127.0.0.1", "100-50"])
        self.assertFalse(res_bad_range.success)
        self.assertIn("Plage inversée", res_bad_range.message)

        # Exécution normale sur le port de test
        res_ok = cmd.execute(["127.0.0.1", str(self.open_port)])
        self.assertTrue(res_ok.success)
        self.assertIn(f"{self.open_port}/tcp", res_ok.message)


if __name__ == "__main__":
    unittest.main()
