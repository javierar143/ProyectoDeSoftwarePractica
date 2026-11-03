"""Comandos de consola CLI para mantenimiento, esquemas y carga de semillas."""

from flask import Flask

from src.core import database
from src.core.seeds.sectores import SECTORES_INICIALES
from src.core.services.sectores import sector as sector_service


def register_commands(app: Flask) -> None:
    """Registra los comandos de terminal en la instancia de Flask."""

    @app.cli.command("reset-db")
    def reset_db():
        """Restablece la base de datos borrando y recreando tablas con sus semillas."""
        database.reset_db()
        print("Base de datos reseteada y cargada con datos iniciales correctamente.")

    @app.cli.command("seed-db")
    def seed_db():
        """Carga todas las semillas del sistema sin reiniciar las tablas."""
        database.seed_all()
        print("Semillas base cargadas correctamente.")

    @app.cli.command("seed-sectores")
    def seed_sectores():
        """Carga exclusivamente los sectores iniciales que aún no existan."""
        creados = sector_service.seed(SECTORES_INICIALES)
        print(f"Sectores creados: {creados}")