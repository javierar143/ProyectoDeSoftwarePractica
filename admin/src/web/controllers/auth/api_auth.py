"""Controladores REST relacionados con autenticación."""

from flask import Blueprint


api_auth = Blueprint(
    "api_auth",
    __name__,
    url_prefix="/api/auth",
)