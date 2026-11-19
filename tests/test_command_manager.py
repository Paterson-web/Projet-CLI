"""Tests unitaires du gestionnaire de commandes (CommandManager)."""

import unittest

from core.command_base import CommandBase, CommandResult
from core.command_manager import CommandManager
from core.exceptions import ValidationError


class DummyEchoCommand(CommandBase):
    """Commande de test fictive pour tester l'exécution et les arguments."""

    def __init__(self) -> None:
        super().__init__(
            name="echo",
            description="Renvoie les arguments fournis.",
            usage="echo <texte>",
            aliases=["print"],
        )

    def execute(self, args: list[str]) -> CommandResult:
        if not args:
            raise ValidationError("Aucun argument fourni", details="args=[]")
        return CommandResult.ok(message=" ".join(args), data=args)


class TestCommandManager(unittest.TestCase):
    """Suite de tests validant le comportement du CommandManager."""

    def setUp(self) -> None:
        self.manager = CommandManager()
        self.cmd = DummyEchoCommand()
        self.manager.register(self.cmd)

    def test_registration_and_lookup(self) -> None:
        """Vérifie l'enregistrement et la recherche par nom et alias."""
        # Recherche par nom exact
        self.assertEqual(self.manager.get("echo"), self.cmd)
        # Recherche insensible à la casse
        self.assertEqual(self.manager.get("ECHO"), self.cmd)
        # Recherche par alias
        self.assertEqual(self.manager.get("print"), self.cmd)
        # Commande inexistante
        self.assertIsNone(self.manager.get("unknown"))

    def test_duplicate_registration_fails(self) -> None:
        """Vérifie qu'on ne peut pas enregistrer deux commandes avec le même nom."""
        with self.assertRaises(ValueError):
            self.manager.register(self.cmd)

    def test_successful_execution(self) -> None:
        """Vérifie l'exécution normale d'une commande enregistrée."""
        result = self.manager.execute("echo", ["hello", "world"])
        self.assertTrue(result.success)
        self.assertEqual(result.message, "hello world")
        self.assertEqual(result.data, ["hello", "world"])

    def test_alias_execution(self) -> None:
        """Vérifie l'exécution d'une commande via son alias."""
        result = self.manager.execute("print", ["test_alias"])
        self.assertTrue(result.success)
        self.assertEqual(result.message, "test_alias")

    def test_unknown_command_execution(self) -> None:
        """Vérifie la capture propre d'une commande non enregistrée."""
        result = self.manager.execute("not_exists", [])
        self.assertFalse(result.success)
        self.assertIn("Commande inconnue", result.message)

    def test_validation_error_capture(self) -> None:
        """Vérifie que les ValidationError sont interceptées et formatées en échec lisible."""
        result = self.manager.execute("echo", [])
        self.assertFalse(result.success)
        self.assertIn("Erreur de saisie", result.message)

    def test_unregister_command(self) -> None:
        """Vérifie le retrait d'une commande et le nettoyage de ses alias."""
        self.assertTrue(self.manager.unregister("echo"))
        self.assertIsNone(self.manager.get("echo"))
        self.assertIsNone(self.manager.get("print"))
        self.assertFalse(self.manager.unregister("echo"))


if __name__ == "__main__":
    unittest.main()
