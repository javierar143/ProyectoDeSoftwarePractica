"""Resolución de configuración de producción al cargar Flask."""

import os


class ProductionConfigMeta(type):
    """Lee los secretos al cargar Flask, no al importar la configuración."""

    def __getattribute__(cls, name):
        if name in {"GOOGLE_CLIENT_ID", "CORS_ORIGINS"}:
            return os.environ.get(name)
        return super().__getattribute__(name)
