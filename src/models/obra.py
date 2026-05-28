from dataclasses import dataclass


@dataclass
class Obra:
    titulo: str
    autor: str = ""
    estado: str = "leyendo"
    link_original: str = ""
    capitulos_vistos: int = 0
