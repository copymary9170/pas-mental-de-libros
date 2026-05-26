from pathlib import Path

COMPILADOS_DIR = Path("data/compilados")


def asegurar_compilados_dir():
    COMPILADOS_DIR.mkdir(parents=True, exist_ok=True)


def limpiar_nombre_archivo(nombre):
    permitido = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
    limpio = "".join(c for c in str(nombre or "obra") if c in permitido).strip()
    return limpio.replace(" ", "_") or "obra"


def generar_compilado_texto(obra, capitulos):
    titulo = obra.get("titulo", "Obra sin titulo") if obra else "Obra sin titulo"
    autor = obra.get("autor", "") if obra else ""
    partes = []
    partes.append(f"# {titulo}\n")
    if autor:
        partes.append(f"Autor / creador: {autor}\n")
    partes.append("\n---\n")
    capitulos_ordenados = sorted(capitulos or [], key=lambda c: (int(c.get("temporada") or 1), int(c.get("numero") or 0)))
    for cap in capitulos_ordenados:
        temporada = int(cap.get("temporada") or 1)
        numero = int(cap.get("numero") or 0)
        titulo_cap = cap.get("titulo") or f"Capitulo {numero}"
        texto = cap.get("texto_completo") or ""
        resumen = cap.get("sinopsis") or ""
        notas = cap.get("notas") or cap.get("comentario") or ""
        partes.append(f"\n\n## Temporada {temporada} - Capitulo {numero}: {titulo_cap}\n\n")
        if resumen:
            partes.append(f"Resumen: {resumen}\n\n")
        if texto:
            partes.append(texto.strip() + "\n")
        else:
            partes.append("[Sin texto completo guardado para este capitulo.]\n")
        if notas:
            partes.append(f"\nNotas / comentarios: {notas}\n")
        partes.append("\n---\n")
    return "".join(partes).strip() + "\n"


def guardar_compilado(obra, capitulos):
    asegurar_compilados_dir()
    obra_id = obra.get("id", "obra") if obra else "obra"
    titulo = limpiar_nombre_archivo(obra.get("titulo", "obra") if obra else "obra")
    path = COMPILADOS_DIR / f"{obra_id}_{titulo}_compilado.md"
    texto = generar_compilado_texto(obra, capitulos)
    path.write_text(texto, encoding="utf-8")
    return str(path), texto
