"""Tests unitaires du module Ping (modules.network.ping)."""

import unittest
from unittest.mock import MagicMock, patch

from core.exceptions import ValidationError
from modules.network.ping import PingCommand, execute_ping, parse_ping_output


class TestPingModule(unittest.TestCase):
    """Vérifie la robustesse de l'analyseur (parser) de sortie ICMP et de la commande Ping."""

    SAMPLE_LINUX_SUCCESS = """PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.038 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.041 ms
64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.045 ms
64 bytes from 127.0.0.1: icmp_seq=4 ttl=64 time=0.039 ms

--- 127.0.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3075ms
rtt min/avg/max/mdev = 0.038/0.041/0.045/0.003 ms
"""

    SAMPLE_LINUX_LOSS = """PING 192.168.1.99 (192.168.1.99) 56(84) bytes of data.
--- 192.168.1.99 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3060ms
"""

    SAMPLE_WINDOWS_SUCCESS = """Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=14ms TTL=117
Reply from 8.8.8.8: bytes=32 time=15ms TTL=117

Ping statistics for 8.8.8.8:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 14ms, Maximum = 15ms, Average = 14ms
"""

    def test_parse_linux_success(self) -> None:
        """Vérifie l'extraction précise des métriques sur une sortie standard Linux."""
        res = parse_ping_output(self.SAMPLE_LINUX_SUCCESS, target="127.0.0.1")
        self.assertTrue(res.is_reachable)
        self.assertTrue(res.success)
        self.assertEqual(res.resolved_ip, "127.0.0.1")
        self.assertEqual(res.packets_transmitted, 4)
        self.assertEqual(res.packets_received, 4)
        self.assertEqual(res.packet_loss_percent, 0.0)
        self.assertEqual(res.rtt_min_ms, 0.038)
        self.assertEqual(res.rtt_avg_ms, 0.041)
        self.assertEqual(res.rtt_max_ms, 0.045)
        self.assertEqual(res.rtt_mdev_ms, 0.003)

    def test_parse_linux_100_percent_loss(self) -> None:
        """Vérifie le comportement en cas de perte intégrale de paquets."""
        res = parse_ping_output(self.SAMPLE_LINUX_LOSS, target="192.168.1.99")
        self.assertFalse(res.is_reachable)
        self.assertFalse(res.success)
        self.assertEqual(res.packets_transmitted, 4)
        self.assertEqual(res.packets_received, 0)
        self.assertEqual(res.packet_loss_percent, 100.0)
        self.assertIsNone(res.rtt_avg_ms)
        self.assertIn("100% de perte", res.error_message or "")

    def test_parse_windows_success(self) -> None:
        """Vérifie l'extraction des statistiques sous format Windows."""
        res = parse_ping_output(self.SAMPLE_WINDOWS_SUCCESS, target="8.8.8.8")
        self.assertTrue(res.is_reachable)
        self.assertEqual(res.packets_transmitted, 4)
        self.assertEqual(res.packets_received, 4)
        self.assertEqual(res.packet_loss_percent, 0.0)
        self.assertEqual(res.rtt_min_ms, 14.0)
        self.assertEqual(res.rtt_avg_ms, 14.0)
        self.assertEqual(res.rtt_max_ms, 15.0)

    @patch("subprocess.run")
    def test_execute_ping_mocked_success(self, mock_run: MagicMock) -> None:
        """Vérifie execute_ping avec simulation de subprocess sans dépendre du réseau."""
        mock_proc = MagicMock()
        mock_proc.stdout = self.SAMPLE_LINUX_SUCCESS
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = execute_ping("127.0.0.1", count=4)
        self.assertTrue(result.success)
        self.assertEqual(result.packets_received, 4)
        self.assertEqual(result.rtt_avg_ms, 0.041)

    @patch("subprocess.run", side_effect=PermissionError("Raw socket non permis"))
    def test_execute_ping_permission_error(self, mock_run: MagicMock) -> None:
        """Vérifie l'interception propre des erreurs de permissions sans crash."""
        result = execute_ping("127.0.0.1")
        self.assertFalse(result.success)
        self.assertIn("Privilèges insuffisants", result.error_message or "")

    def test_ping_command_validation(self) -> None:
        """Vérifie les contrôles de validation de la commande CLI Ping."""
        cmd = PingCommand()
        # Pas d'argument
        res_no_arg = cmd.execute([])
        self.assertFalse(res_no_arg.success)
        self.assertIn("Spécifie une cible", res_no_arg.message)

        # Nombre de paquets hors limites (>30)
        res_high_count = cmd.execute(["8.8.8.8", "50"])
        self.assertFalse(res_high_count.success)
        self.assertIn("entre 1 et 30", res_high_count.message)


if __name__ == "__main__":
    unittest.main()
