# Simulador de impacto — camioneta rodando por pendiente

Aplicación web (Shiny for Python) que estima el impacto sobre una persona si una camioneta aparcada en una calle con pendiente comienza a rodar sin intervención del motor.

## ¿Qué calcula?

Dadas tres variables — **pendiente**, **distancia** entre la camioneta y la persona, y **masa** de la camioneta — la app calcula:

- Velocidad de impacto (m/s y km/h).
- Energía cinética en el momento del choque (kJ).
- Probabilidad de fatalidad del peatón (curva logística de Rosén & Sander, 2009).
- Probabilidad de lesión grave (AIS 3+).
- Clasificación cualitativa AIS (leve / moderado / grave / crítico).

Además muestra:

- Un **esquema 2D interactivo** de la rampa, la camioneta y la persona (Plotly).
- Una **gráfica de velocidad y energía** acumuladas a lo largo del recorrido.
- Un **banner de advertencia** cuando la fricción de rodadura supera la componente de gravedad y la camioneta no se mueve.

## Modelo físico

Se asume movimiento rectilíneo con fricción de rodadura y sin aire:

- Aceleración neta a lo largo de la pendiente:
  `a = g · (sen θ − μ_r · cos θ)`, con `g = 9.81 m/s²`.
- Condición de arranque: `tan θ > μ_r`. Si no se cumple, la camioneta permanece en reposo.
- Velocidad al recorrer distancia `d`: `v = √(2 · a · d)`.
- Energía cinética: `E = ½ · m · v²`.
- Probabilidad de fatalidad: `P(v) = 1 / (1 + exp(a − b · v_kmh))` (coeficientes configurables en `src/constants.py`).

### Superficies predefinidas (μ_r)

| Superficie       | μ_r    |
|------------------|--------|
| Asfalto seco     | 0.013  |
| Asfalto mojado   | 0.015  |
| Concreto         | 0.014  |
| Grava/compactado | 0.020  |

## Requisitos

- Python >= 3.12
- `uv` para gestión de entorno y dependencias (recomendado).

## Instalación

```bash
cd ai_dev_ubu_py2
uv venv .venv
source .venv/bin/activate
UV_LINK_MODE=copy uv pip install -e .
```

## Uso

```bash
.venv/bin/shiny run src/app.py --port 8000
```

Luego abre `http://localhost:8000` en tu navegador y mueve los sliders para explorar diferentes escenarios.

## Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

## Estructura del proyecto

```
src/
├── app.py          # UI Shiny + server reactivo
├── physics.py      # Funciones puras: aceleración, velocidad, energía, probabilidades
├── plotting.py     # Figuras Plotly (escena + perfil v/E)
└── constants.py    # g, μ_r, umbrales AIS, coeficientes Rosén-Sander
tests/
└── test_physics.py # Tests unitarios
```

## Advertencia

El modelo es una herramienta **didáctica** para explorar cómo la pendiente, la distancia y la masa influyen en la severidad de un atropello hipotético. Los coeficientes de fricción, las curvas de lesión y la escala AIS son aproximaciones; **no deben usarse para análisis forense ni decisiones de ingeniería**.
