"""Tests unitaires du socle initial (config, logger, exceptions)."""

import unittest
from pathlib import Path

from config.settings import (
    APP_NAME,
    APP_VERSION,
    BASE_DIR,
    DEFAULT_PING_COUNT,
    DEFAULT_SOCKET_TIMEOUT,
    LOGS_DIR,
)
from core.exceptions import (
    CommandNotFoundError,
    FrameworkError,
    ValidationError,
)
from core.logger import get_logger


class TestCoreSetup(unittest.TestCase):
    """Vérifie la robustesse du socle d'architecture (Étape 1)."""

    def test_settings_constants(self):
        """Vérifie que les paramètres fondamentaux sont définis et cohérents."""
        self.assertEqual(APP_NAME, "Personal Framework CLI")
        self.assertTrue(APP_VERSION.startswith("2."))
        self.assertIsInstance(BASE_DIR, Path)
        self.assertGreater(DEFAULT_PING_COUNT, 0)
        self.assertGreater(DEFAULT_SOCKET_TIMEOUT, 0.0)

    def test_logger_initialization(self):
        """Vérifie que le logger fournit une instance valide et active."""
        logger = get_logger("tests.unit")
        self.assertIsNotNone(logger)
        logger.info("Message de test unitaire - Étape 1")
        # Le dossier de logs doit exister
        self.assertTrue(LOGS_DIR.exists())

    def test_exceptions_hierarchy(self):
        """Vérifie la bonne dérivation et le formatage des exceptions métier."""
        err = ValidationError("Port hors limites", details="port=70000")
        self.assertIsInstance(err, FrameworkError)
        self.assertIn("Port hors limites (port=70000)", str(err))

        cmd_err = CommandNotFoundError("scan")
        self.assertIsInstance(cmd_err, FrameworkError)


if __name__ == "__main__":
    unittest.main()
