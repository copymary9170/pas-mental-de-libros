# Pas Mental de Libros

App en Streamlit para llevar seguimiento de libros, fanfiction, novelas, mangas, manhwas, manhuas y otras lecturas.

## Funciones

- Agregar obras con portada, título, autor, tipo, etiquetas y clasificación.
- Guardar sinopsis general.
- Guardar links originales y links de respaldo.
- Subir archivos o páginas como respaldo manual.
- Registrar capítulos leídos, notas y sinopsis por capítulo.
- Marcar estado personal de lectura:
  - Pendiente
  - Leyendo
  - Terminado
  - Pausado
  - Abandonado
- Marcar estado de publicación:
  - En emisión
  - Terminada
  - Hiatus con aviso
  - Hiatus sin aviso
  - Cancelada
  - Abandonada por autor
- Filtros por título, autor, tipo, estado, etiquetas y ranking.
- Ranking mensual y anual.
- Estadísticas de lecturas terminadas, pausadas, abandonadas y en hiatus.

## Instalación

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

```text
pas-mental-de-libros/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
├── uploads/
│   ├── portadas/
│   └── respaldos/
└── src/
    ├── database.py
    ├── utils.py
    └── styles.py
```

## Nota importante

La primera versión guarda todo de forma local usando SQLite y carpetas locales.
Para usarlo en varios dispositivos, más adelante se puede conectar con Supabase, Google Drive o almacenamiento en la nube.
