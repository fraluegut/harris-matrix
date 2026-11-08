"""harris-matrix: estratigrafía arqueológica registrable, verificable y dibujable."""

__version__ = "0.1.0"

from .model import Proyecto, Relacion, UE, cargar_proyecto
from .render import renderizar_svg
from .verify import Incidencia, verificar

__all__ = [
    "__version__", "Proyecto", "Relacion", "UE", "Incidencia",
    "cargar_proyecto", "verificar", "renderizar_svg",
]
