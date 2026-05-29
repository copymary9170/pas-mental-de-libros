# Mapa de datos automaticos

Este archivo resume que cosas puedo medir automaticamente, de donde salen los datos y que conviene agregar para que el Wrapped sea mas inteligente.

## Lo que ya se puede medir si las entradas estan llenas

| Dato / premio | Se puede medir | De donde sale | Que necesita |
|---|---|---|---|
| Obras terminadas | Si | `Estado personal`, `listas/terminados.md` | Estado o lista actualizada |
| Obras empezadas | Si | `Fecha de inicio`, `listas/viendo-leyendo.md` | Fecha de inicio |
| Obras abandonadas | Si | `Estado personal`, `listas/abandonados.md` | Estado o lista actualizada |
| Obras pendientes | Si | `listas/pendientes.md` | Lista actualizada |
| Tipo mas repetido | Si | Campo `Tipo` | Tipo consistente: libro, serie, anime, pelicula, manga, manhwa, etc. |
| Genero mas repetido | Si | Campo `Genero` | Generos escritos de forma consistente |
| Mes con mas actividad | Si | `Registro diario de avance`, fechas de inicio/finalizacion | Fechas registradas |
| Obra mejor calificada | Si | `Nota final` | Nota final numerica |
| Favoritos por tipo | Si | `Tipo` + `Nota final` + opinion | Tipo y nota final |
| Estreno reciente | Si | `Fecha de estreno / publicacion` + `Fecha de inicio` | Ambas fechas |
| Llegue tarde al hype | Parcial | Fecha estreno + fecha inicio + opinion | Fechas y opinion sobre hype/fama |
| Maraton mas intenso | Si | `Registro diario de avance` | Cantidad de capitulos/episodios por dia |
| Dia mas intenso | Si | `Registro diario de avance` | Fecha y avance diario |
| Obra terminada mas rapido | Si | Fecha inicio + fecha finalizacion + cantidad total | Fechas y total de capitulos/paginas |
| Pendiente mas antiguo empezado | Si | `Fecha agregada a pendientes` + `Fecha de inicio` | Ambas fechas |
| Pendiente mas antiguo terminado | Si | `Fecha agregada a pendientes` + `Fecha de finalizacion` | Ambas fechas |
| Bloqueo por tipo | Si | Registros por fecha + campo `Tipo` | Actividad por fecha y tipo |
| Salida de bloqueo | Si | Primer registro despues de pausa larga | Fechas y tipo |
| Entrada en bloqueo | Probable | Obra terminada/abandonada antes de pausa larga | Fechas posteriores sin actividad |
| Retomada despues de pausa | Si | Pausa larga entre registros de la misma obra | Registro diario |
| Abandono rapido | Si | Estado abandonado + poco progreso | Estado y progreso |

## Lo que se puede medir con opinion escrita

| Dato / premio | Se puede medir | De donde sale | Que ayuda a detectarlo |
|---|---|---|---|
| Obra que me destruyo emocionalmente | Probable | Opinion general, momentos, lo peor | Palabras como llore, vacio, devastada, no lo supere |
| Obra que me dio paz mental | Probable | Opinion general | Palabras como calma, paz, comfort, tranquila, bonita |
| Obra que me rompio la paz mental | Probable | Opinion general | ansiedad, caos, sufrimiento, trauma, obsesion |
| Obra que se sintio como terapia | Probable | Opinion general | me ayudo, la necesitaba, me acompaño |
| Mayor obsesion | Probable | Opinion + señales | obsesion, teorias, fanarts, edits, fanfiction |
| Obra que recomende mas | Parcial | Opinion + campo `La recomende` | Si lo mencionas varias veces o marcas recomendacion |
| Obra que mencione demasiado | Parcial | Reportes, opiniones, repeticion en archivos | Varias menciones en distintos archivos |
| Personaje que se robo el año | Probable | Personajes favoritos + opinion | Muchas menciones o puesto alto |
| Ship que mas me obsesiono | Probable | Personajes, opinion, fanfiction | Menciones repetidas del ship |

## Lo que no puedo medir bien todavia sin nuevos datos

| Premio / dato | Problema | Que se puede agregar |
|---|---|---|
| Cuanto tiempo real pase viendo o leyendo | Falta duracion real | Llenar `Tiempo aproximado` en registro diario |
| Si la vi acompañada o sola | No sale de fechas | Campo `La vi con alguien` o comentario diario |
| Si la recomende varias veces | No hay contador | Campo `Veces recomendada` o notas en reportes |
| Si hable mucho de ella fuera del repo | No puedo saberlo | Campo `La mencione mucho` o comentario |
| Si busque fanarts/edits/fanfiction | No se puede saber sin que lo anotes | Campo `Me hizo buscar` |
| Si llego en un mal/buen momento personal | No se infiere solo con fechas | Campo `Momento personal` u opinion |
| Nivel exacto de obsesion | No se mide solo con nota | Campo `Nivel de obsesion` o menciones repetidas |
| Mejor opening/ending/banda sonora | Falta campo especifico | Agregar opinion musical o ranking por obra |
| Mejor portada/poster/panel | Falta campo visual especifico | Agregar campo de arte/visual favorito |
| Mejor actor/actriz/seiyuu | Falta dato de elenco/voz | Agregar campo opcional si aplica |

## Datos nuevos que conviene agregar

Estos campos no son obligatorios, pero harian el sistema mas automatico.

### En cada entrada

- Fecha agregada a pendientes
- Fecha de estreno / publicacion
- Tipo normalizado: libro, serie, anime, pelicula, manga, manhwa, comic, fanfiction, documental
- Registro diario de avance
- Tiempo aproximado
- Estado del dia: normal, enganche, cansancio, pausa, abandono, emocion fuerte
- Veces recomendada
- La vi con alguien
- Me hizo buscar: teorias, fanarts, edits, fanfiction, entrevistas
- Momento personal: buen momento, mal momento, momento perfecto, etapa importante

### En reportes mensuales

- Obra que mas mencione
- Obra que recomende
- Tipo que retome
- Tipo que deje abandonado
- Bloqueo del mes
- Salida de bloqueo del mes
- Mayor maraton del mes
- Dia mas intenso del mes

## Nuevos premios automaticos que se pueden agregar

| Premio | Como se puede calcular |
|---|---|
| Tipo resucitado del año | Tipo que tuvo pausa larga y luego varios registros |
| Tipo abandonado del año | Tipo con mas pausas largas o abandono |
| Obra puente | Obra que hizo que despues consumiera varias del mismo tipo/genero |
| Obra detonante de obsesion | Obra despues de la cual aparecen busquedas, fanfiction, fanarts o reportes repetidos |
| Mes de regreso | Mes donde retome mas tipos despues de pausas |
| Mes de bloqueo | Mes con menos actividad o despues de una obra fuerte |
| Racha mas larga viendo/leyendo | Dias consecutivos con registros |
| Racha rota mas dolorosa | Racha larga que se corto despues de una obra o pausa |
| Genero refugio | Genero al que vuelvo despues de pausas o bloqueos |
| Genero de riesgo | Genero que suele terminar en abandono o pausa |
| Obra efecto domino | Obra que me llevo a ver/leer otras parecidas |
| Obra rompe rutina | Obra de un tipo/genero que casi no consumo pero disfrute |
| Retorno mas inesperado | Tipo u obra que llevaba mucho tiempo sin tocar y volvio fuerte |

## Regla de oro

Mientras mas fechas y registros existan, menos tienes que explicarme despues. Si falta informacion, no se inventa: se marca como posible, probable o no determinado.
