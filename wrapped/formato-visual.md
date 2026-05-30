# Formato visual del Wrapped

Este archivo define como deberia verse el Wrapped final para que sea mas parecido a Spotify Wrapped, TV Time, Letterboxd o un resumen visual anual.

## Objetivo

Crear un Wrapped final que tenga:

- Portadas de obras
- Imagenes de personajes
- Imagenes de ships o duos
- Escenas importantes
- Rankings visuales
- Finalistas por premio
- Ganadores sorpresa
- Estadisticas del año
- Tarjetas emocionales y divertidas

## Secciones visuales sugeridas

### 1. Portada del Wrapped

- Año
- Frase del año
- Imagen principal
- Total de obras registradas
- Tipos consumidos

### 2. Resumen general

- Obras terminadas
- Obras empezadas
- Obras abandonadas
- Obras pausadas
- Mes con mas actividad
- Dia mas intenso
- Tipo mas consumido
- Genero mas repetido

### 3. Top 5 del año

Cada obra debe tener:

- Portada
- Titulo
- Tipo
- Nota
- Motivo corto

### 4. Premios con finalistas

Cada premio puede tener:

- 5 finalistas
- Imagen de cada finalista
- Evidencia breve
- Ganador oculto hasta el final

### 5. Premios de personajes

Cada personaje debe mostrar:

- Imagen del personaje
- Obra / version
- Premio
- Evidencia
- Si viene de canon, fanfiction, AU o adaptacion

### 6. Premios de experiencia personal

Ejemplos:

- Maraton mas intenso
- Obra que me saco de un bloqueo
- Obra que me dejo en resaca emocional
- Gusto culposo del año
- Obra que el autor arruino al final

### 7. Rankings visuales

- Ranking general
- Ranking por tipo
- Ranking de personajes
- Ranking de ships
- Ranking de portadas
- Ranking de finales
- Ranking de villanos

### 8. Tarjetas especiales

- Obra mas caliente
- Obra que mas me hizo llorar
- Tesoro oculto de humor negro
- Historia con mas cringe
- Obra demasiado larga que no pude terminar
- Mejor isekai
- Mejor ambientacion historica

### 9. Cierre del Wrapped

- Ganador absoluto del año
- Personaje del año
- Obra que mas me marco
- Frase final
- Pendientes para el proximo año

## Formato de tarjeta sugerido

```md
## [Nombre del premio]

![Imagen](../assets/.../archivo.jpg)

**Ganador:**  
**Obra / version:**  
**Tipo:**  
**Por que gano:**  
**Evidencia:**  
**Certeza:** posible / probable / claro
```

## Regla de imagenes

Cada imagen usada en el Wrapped debe estar registrada en `wrapped/imagenes-wrapped.md`.

## Regla de finalistas

Semanas antes del Wrapped final se puede generar una lista de 5 finalistas por premio usando `plantillas/finalistas-wrapped.md`.

La idea es que puedas subir las imagenes faltantes antes de revelar ganadores.
