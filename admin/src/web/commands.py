"""Comandos de consola CLI para mantenimiento, esquemas y carga de semillas."""

from flask import Flask

from src.core import database
from src.core.seeds.sectores import SECTORES_INICIALES
from src.core.services.sectores import sector as sector_service
from src.core.seeds.permisos import load_permisos
from src.core.seeds.asignaciones_jefes import (
    load_asignaciones_jefes_sector,
)


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

    @app.cli.command("seed-permisos")
    def seed_permisos():
        """Completa los permisos y sus asociaciones faltantes por rol."""
        load_permisos()
        print("Permisos y asociaciones por rol actualizados correctamente.")

    @app.cli.command("seed-asignaciones-jefes")
    def seed_asignaciones_jefes():
        """Completa los sectores faltantes de los Jefes de Servicio."""
        resultado = load_asignaciones_jefes_sector()

        print(
            "Asignaciones completadas: "
            f"{resultado['asignados']}"
        )
        print(
            "Usuarios sin sector de origen: "
            f"{resultado['sin_sector_origen']}"
        )
        print(
            "Usuarios que requieren revisión: "
            f"{resultado['requieren_revision']}"
        )