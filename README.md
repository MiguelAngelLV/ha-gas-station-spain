# Componente Gas Station Spain

## ¿Qué es Gasolineras de España?

«Gasolineras de España» Es un componente para [Home Assistant](https://home-assistant.io/) que permite obtener el precio del combustible de las distintas
gasolineras de España para visualizarlo en tu instalación de Home Assistant.

## Instalación

Puedes instalar el componente usando HACS:

### Directa usando _My Home Assistant_

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=miguelangellv&repository=ha-gas-station-spain&category=integration)

### Manual

Deberás añadir el repositorio personalizado en HACS:

```
HACS -> Integraciones -> Tres puntitos -> Repositorios Personalizados
```

Copias la URL del repositorio (https://github.com/MiguelAngelLV/ha-gas-station-spain), como categoría seleccionas _Integración_ y pulsas en _Añadir_.

Una vez añadido el repositorio, lo instalas.

## Configuración

Una vez instalado, ve a _Dispositivos y Servicios -> Añadir Integración_ y busca _Gasolineras España_.

El asistente te irá solicitando los datos de la gasolinera y el tipo de combustible.

![Provincia](images/wizard1.png)

![Gasolinera](images/wizard2.png)

Una vez configurado, tendrás la integración con la entidad que muestre el precio.

![Chart](images/chart.png)

Puedes añadir varias configuraciones para controlar varios precios (distintas gasolineras y distintos combustibles).

## Videotutorial

[![Gasolineras de España](http://img.youtube.com/vi/wu5H5-QZyyA/0.jpg)](http://www.youtube.com/watch?v=wu5H5-QZyyA)

## Origen de los Datos

Los datos provienen de la [fuente oficial del Gobierno de España](https://geoportalgasolineras.es/geoportal-instalaciones/Inicio).

Este componente se limita a acceder a la API pública para mostrar la información proporcionada.
