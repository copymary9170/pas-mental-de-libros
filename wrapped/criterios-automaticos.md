# Criterios automaticos para Wrapped

Este archivo explica como puedo determinar premios del Wrapped usando tus entradas, opiniones y acciones registradas.

La idea es que no tengas que dar toda la informacion de nuevo. Si tus fichas tienen fechas, opinion, nota, estado y registros de capitulos o episodios, puedo inferir muchos premios sin que los llenes manualmente.

## Fuentes que se revisan

- `entradas/`: fichas completas de obras
- `listas/`: pendientes, viendo/leyendo, terminados y abandonados
- `ranking/`: favoritos y ranking general
- `capitulos/`: registros por episodio, capitulo o dia
- `wrapped/`: reportes anteriores

## Datos base que permiten calcular premios

| Dato | Para que sirve |
|---|---|
| Fecha de estreno / publicacion | Comparar que tan cerca la viste o leiste del estreno |
| Fecha de inicio | Saber cuando la empezaste |
| Fecha de finalizacion | Saber cuanto tardaste en terminarla |
| Registro diario de capitulos / episodios | Detectar maratones, pausas, ritmo y dias de mas actividad |
| Estado personal | Saber si esta pendiente, en progreso, pausada, terminada o abandonada |
| Tipo de obra | Detectar bloqueos por categoria: series, libros, manhwas, peliculas, anime, manga, comics, fanfiction, documentales |
| Nota final | Comparar favoritos, decepciones y recomendaciones |
| Opinion general | Detectar emociones, obsesiones, decepcion, sorpresa o apego |
| Lo mejor / lo peor | Detectar premios especificos sin preguntarte otra vez |
| Personajes favoritos | Detectar protagonistas, secundarios, ships o villanos destacados |

## Premios que puedo inferir por fechas

| Premio | Como se determina |
|---|---|
| La vi apenas se estreno | La fecha de inicio esta muy cerca de la fecha de estreno / publicacion |
| La vi con poco tiempo de estrenarse | La fecha de inicio esta cerca de la fecha de estreno / publicacion, aunque no sea inmediata |
| Llegue tarde pero valio la pena | Hay mucha distancia entre estreno e inicio, pero la nota es alta o la opinion es positiva |
| Llegue tarde y entendi el hype | Hay mucha distancia entre estreno e inicio y la opinion menciona que entiende la fama, el hype o la recomendacion |
| Llegue tarde y no entendi el hype | Hay mucha distancia entre estreno e inicio, con nota regular/baja u opinion negativa |
| La termine en tiempo record | Hay poca distancia entre fecha de inicio y fecha de finalizacion para la cantidad de capitulos, paginas o episodios |
| Obra que debi terminar antes | Paso mucho tiempo entre inicio y finalizacion, pero termino con buena nota u opinion positiva |
| Obra que vi en el momento perfecto | La opinion menciona que llego en un buen momento, que la necesitaba o que encajo con una etapa personal |
| Obra que vi en el peor momento posible | La opinion menciona que no era el momento, que dolio mas de lo normal o que fue demasiado para ese momento |
| Pendiente mas antiguo que por fin empece | Obra agregada a pendientes hace mucho tiempo y luego movida a en progreso |
| Pendiente mas antiguo que por fin termine | Obra agregada a pendientes hace mucho tiempo y luego movida a terminada |

## Premios que puedo inferir por registros diarios

Para detectar estos premios, se revisa la tabla de **registro diario** de cada entrada o los archivos de `capitulos/`.

| Premio | Como se determina |
|---|---|
| Maraton mas intenso | Mayor cantidad de capitulos / episodios vistos o leidos en un mismo dia |
| Maraton mas largo | Varios dias seguidos con muchos capitulos / episodios de la misma obra |
| Maraton mas espontaneo | Muchos capitulos / episodios vistos el mismo dia de inicio |
| Maraton que no pude soltar | Muchos capitulos / episodios en pocos dias, mas opinion de adiccion o enganche |
| Maraton que me dejo destruido | Muchos capitulos / episodios en poco tiempo, mas opinion emocional fuerte |
| Obra perfecta para maratonear | Ritmo rapido, varios capitulos por dia y opinion positiva |
| Obra perfecta para ver de a poco | Ritmo lento/espaciado y opinion positiva sobre disfrutarla lentamente |
| Obra que vi lentamente y disfrute mas asi | Pocos capitulos por dia, pausas largas, pero opinion positiva |
| Obra que debi ver mas despacio | Registro rapido y opinion indica saturacion, confusion o que hubiera sido mejor pausarla |
| Dia mas intenso del año | Dia con mas capitulos / episodios / paginas registrados entre todas las obras |
| Mes con mas actividad | Mes con mas registros de avance o mas obras terminadas |
| Obra que me saco de un bloqueo por tipo | Primer registro de un tipo de obra despues de mucho tiempo sin consumir ese tipo |
| Tipo de obra que revivi este año | Categoria que paso de tener mucha inactividad a varios registros nuevos |

## Premios que puedo inferir por cambios de estado

| Premio | Como se determina |
|---|---|
| Obra que retome despues de mucho tiempo | Paso de pausada o pendiente a en progreso despues de mucho tiempo |
| Retomada mas satisfactoria | Obra retomada que termino con buena nota u opinion positiva |
| Retomada mas dificil | Obra retomada con pausas repetidas o comentarios de dificultad |
| Obra que deje en pausa y me costo volver | Pausa larga entre dos registros de avance |
| Obra que abandone rapido | Estado abandonado con poco progreso registrado |
| Abandono mas doloroso | Estado abandonado, pero opinion indica que dolio dejarla o que queria que gustara |
| Abandono mas justificado | Estado abandonado y opinion explica claramente por que no valia seguir |
| Obra que casi abandono pero salvo el final | Opinion inicial o registros negativos, pero final positivo |
| Obra que casi abandono pero despues ame | Registros iniciales negativos y opinion final muy positiva |

## Premios que puedo inferir por bloqueos de consumo

Un bloqueo no tiene que depender solo de que escribas "me saco de un bloqueo". Tambien se puede calcular viendo cuanto tiempo paso sin consumir un tipo de obra y cuando volviste a tocar ese tipo.

Ejemplos de tipos: libros, series, anime, peliculas, manga, manhwa, comics, fanfiction, documentales.

| Premio | Como se determina |
|---|---|
| Obra que me saco de un bloqueo de series | Primera serie iniciada o registrada despues de mucho tiempo sin ver series |
| Obra que me saco de un bloqueo de libros | Primer libro iniciado o registrado despues de mucho tiempo sin leer libros |
| Obra que me saco de un bloqueo de peliculas | Primera pelicula registrada despues de mucho tiempo sin ver peliculas |
| Obra que me saco de un bloqueo de manga / manhwa | Primer manga o manhwa registrado despues de mucho tiempo sin leer ese tipo |
| Obra que me saco de un bloqueo general | Primera obra registrada despues de mucho tiempo sin actividad en ningun tipo |
| Tipo que mas abandone este año | Tipo con mas tiempo de inactividad o mas obras pausadas/abandonadas |
| Tipo que mas retome este año | Tipo que tuvo inactividad larga y luego varios avances nuevos |

Criterio sugerido para detectar bloqueo por tipo:

| Resultado | Tiempo sin registros de ese tipo |
|---|---|
| Pausa normal | 15 a 29 dias |
| Bloqueo leve | 30 a 59 dias |
| Bloqueo fuerte | 60 a 119 dias |
| Bloqueo largo | 120 dias o mas |

Para calcularlo se revisan las fechas de `Fecha de inicio`, `Fecha de finalizacion` y el `Registro diario de avance`. Si una obra aparece despues de una pausa larga en su tipo, puede ganar el premio de salida de bloqueo.

## Premios que puedo inferir por opiniones

| Premio | Palabras o señales posibles |
|---|---|
| Obra que mas me destruyo emocionalmente | destruyo, llore, devastada, dolor, vacio, no lo supere |
| Obra que me dio paz mental | tranquila, bonita, calma, comfort, paz, descanso |
| Obra que me rompio la paz mental | ansiedad, caos, sufrimiento, trauma, obsesion |
| Obra que se sintio como terapia | me ayudo, necesitaba esto, me acompaño, me hizo bien |
| Obra que me saco de un bloqueo | puede salir por opinion o por actividad despues de mucha inactividad |
| Obra que me metio en un bloqueo | no pude ver nada despues, resaca, bloqueo lector, o mucha inactividad despues de terminarla |
| Mayor obsesion del año | obsesion, no paro de pensar, busque teorias, fanarts, edits, fanfiction |
| Obra que me hizo buscar teorias | opinion o señales mencionan teorias, explicaciones o analisis |
| Obra que me hizo buscar fanarts / edits | opinion o señales mencionan fanarts, edits, imagenes o videos |
| Obra que me hizo buscar fanfiction | opinion o señales mencionan fanfiction, AO3, Wattpad u otra busqueda similar |
| Obra que recomende mas este año | opinion o registros mencionan que la recomendaste varias veces |
| Recomendacion que valio la pena | marcada como recomendacion y opinion positiva |
| Recomendacion que no era para mi | marcada como recomendacion y opinion negativa o neutral |

## Como se calcula estreno reciente

Se compara:

- `Fecha de estreno / publicacion`
- `Fecha de inicio`

Criterio sugerido:

| Resultado | Diferencia entre estreno e inicio |
|---|---|
| Apenas se estreno | 0 a 7 dias |
| Poco tiempo de estrenarse | 8 a 45 dias |
| Estreno reciente tardio | 46 a 90 dias |
| Llegue tarde | Mas de 90 dias |

Si la obra tiene muchos episodios o capitulos publicados durante meses, se puede usar la fecha de estreno de la temporada, tomo, arco o capitulo que corresponda.

## Como se calcula un maraton

Se revisa el registro diario:

| Señal | Interpretacion |
|---|---|
| Muchos capitulos el mismo dia | Posible maraton |
| Muchos capitulos el dia de inicio | Maraton espontaneo |
| Muchos capitulos durante varios dias seguidos | Maraton largo |
| Obra terminada en muy pocos dias | Termino en tiempo record |
| Opinion con cansancio o saturacion | Maraton pesado |
| Opinion con emocion fuerte | Maraton emocional |

Ejemplo de registro util:

| Fecha | Capitulos / episodios vistos | Paginas leidas | Tiempo aproximado | Comentario |
|---|---:|---:|---|---|
| 2026-01-05 | 6 | 0 | 3 horas | No podia parar |
| 2026-01-06 | 5 | 0 | 2 horas | Me destruyo |

## Como se calcula salida o entrada en bloqueo

Se revisa el espacio entre registros de actividad.

### Salida de bloqueo

Una obra puede sacar de un bloqueo si:

1. Pertenece a un tipo que tenia mucho tiempo sin registros.
2. Es la primera actividad nueva despues de esa pausa.
3. Despues de esa obra hubo continuidad, opinion positiva o avance real.

### Entrada en bloqueo

Una obra puede meter en bloqueo si:

1. Despues de terminarla o abandonarla pasa mucho tiempo sin registros.
2. La opinion menciona resaca, cansancio, saturacion o que costo seguir con otras cosas.
3. El bloqueo puede ser general o por tipo.

Ejemplo:

| Tipo | Ultimo registro antes | Nuevo registro | Dias sin actividad | Resultado |
|---|---|---|---:|---|
| Series | 2026-02-01 | 2026-05-20 | 108 | Bloqueo fuerte de series |
| Peliculas | 2026-01-10 | 2026-01-25 | 15 | Pausa normal |
| Manhwa | 2025-12-01 | 2026-06-15 | 196 | Bloqueo largo de manhwa |

## Niveles de certeza

Si falta informacion, no se inventa. Se puede marcar como:

- No determinado: no hay datos suficientes
- Posible ganador: hay una señal, pero faltan datos
- Ganador probable: hay varias señales, pero no esta completamente confirmado
- Ganador claro: fechas, registros y opinion coinciden

## Como quiero que se usen estos criterios

Cuando pida mi Wrapped, quiero que se revise lo que ya escribi y se llenen los premios con base en mis entradas, listas, opiniones, fechas y registros diarios.

Si hay dudas, se deja como probable en vez de inventar.