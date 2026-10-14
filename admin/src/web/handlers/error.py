from flask import render_template
from dataclasses import dataclass

@dataclass
class HTTPError:
    code: int
    message: str
    description: str

def not_found(e):
    error = HTTPError(
        code=404,
        message="Página no encontrada",
        description="Lo sentimos, la pagina que estás buscando no existe."
    )
    return render_template('error.html', error=error), 404

def unauthorized(e):
    error = HTTPError(
        code=401,
        message="Acceso no autorizado",
        description="No estas autorizado para ver este contenido. Por favor, inicia sesion"
    )
    return render_template('error.html', error=error), 401

def internal_server_error(e):
    error = HTTPError(
        code=500,
        message="Internal Server Error",
        description="Ocurrio un error en el servidor, intentelo mas tarde"
    )
    return render_template('error.html', error=error), 500