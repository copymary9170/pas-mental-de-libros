from .obra import Obra


def obra_from_dict(data: dict) -> Obra:
    return Obra(
        titulo=data.get("titulo", ""),
        autor=data.get("autor", ""),
        estado=data.get("estado", "leyendo"),
        link_original=data.get("link_original", ""),
        capitulos_vistos=data.get("capitulos_vistos", 0),
    )


def obra_to_dict(obra: Obra) -> dict:
    return {
        "titulo": obra.titulo,
        "autor": obra.autor,
        "estado": obra.estado,
        "link_original": obra.link_original,
        "capitulos_vistos": obra.capitulos_vistos,
    }
