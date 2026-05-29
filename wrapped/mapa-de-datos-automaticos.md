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
| Obra mas caliente | Si, si se activa | Sensor de lujuria | Sensor activo + nivel de lujuria |
| Obra que mas me hizo llorar | Si, si se activa | Sensor de llanto | Sensor activo + nivel o veces que llore |
| Mejor humor negro | Si, si se activa | Sensor de humor negro | Sensor activo + nivel de humor negro |
| Tesoro oculto | Si, si se activa | Sensor de tesoro oculto | Sensor activo + nota/opinion positiva |

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
| Llanto inesperado | Probable | Sensor de llanto + comentario | Comentario indica que no esperaba llorar |
| Comedia negra inesperada | Probable | Sensor humor negro + opinion | Opinion indica sorpresa o tesoro oculto |
| Tension / lujuria destacada | Probable | Sensor de lujuria + opinion | tension, quimica, deseo, caliente |

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
| Intensidad de lujuria | No se debe inferir si no lo activas | Activar sensor de lujuria y poner nivel |
| Intensidad de llanto | Puede aparecer en opinion, pero se mide mejor con sensor | Activar sensor de llanto, nivel y veces |
| Calidad de humor negro | No siempre sale del genero | Activar sensor de humor negro y comentario |
| Tesoro oculto real | Necesita que lo marques o que haya baja expectativa + nota alta | Activar sensor de tesoro oculto o explicar por que |

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
- Sensor de lujuria / caliente: activo o no activo
- Nivel de lujuria: 0 a 5
- Sensor de llanto: activo o no activo
- Nivel de llanto: 0 a 5
- Veces que llore
- Sensor de humor negro: activo o no activo
- Nivel de humor negro: 0 a 5
- Sensor de tesoro oculto: activo o no activo

### En reportes mensuales

- Obra que mas mencione
- Obra que recomende
- Tipo que retome
- Tipo que deje abandonado
- Bloqueo del mes
- Salida de bloqueo del mes
- Mayor maraton del mes
- Dia mas intenso del mes
- Obra mas caliente del mes, si aplica
- Obra que mas me hizo llorar del mes, si aplica
- Tesoro oculto de humor negro del mes, si aplica

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
| Obra mas caliente | Sensor de lujuria activo + mayor nivel |
| Momento mas caliente | Sensor de lujuria activo + comentario especifico |
| Obra con mas tension | Sensor de lujuria activo + opinion de tension o quimica |
| Obra que mas me hizo llorar | Sensor de llanto activo + nivel o veces que llore |
| Llanto mas inesperado | Sensor de llanto activo + comentario de sorpresa |
| Llanto mas devastador | Sensor de llanto alto + opinion emocional fuerte |
| Mejor humor negro | Sensor humor negro activo + mayor nivel |
| Tesoro oculto de humor negro | Sensor humor negro activo + sensor tesoro oculto activo |
| Comedia negra mas inesperada | Humor negro alto + opinion de sorpresa |
| Tesoro oculto del año | Sensor tesoro oculto activo + nota alta/opinion positiva |

## Regla de oro

Mientras mas fechas y registros existan, menos tienes que explicarme despues. Si falta informacion, no se inventa: se marca como posible, probable o no determinado.