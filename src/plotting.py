"""Plotly figures for the truck-impact Shiny app."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from physics import kinetic_energy

# Visual constants — tweak here to restyle the scene without touching logic.
_TRUCK_COLOR = "#1565c0"
_PERSON_COLOR = "#c62828"
_GROUND_COLOR = "#424242"

# Vehicle image served as a static Shiny asset from www/vehiculo.png.
# Falls back to None if the file is absent so the app still runs.
_VEHICULO_SRC: str | None = None
_img_path = Path(__file__).parent / "www" / "vehiculo.png"
if _img_path.exists():
    _VEHICULO_SRC = "/vehiculo.png"


def scene_figure(
    slope_deg: float,
    distance_m: float,
    will_roll: bool,
) -> go.Figure:
    """Return a 2D side-view sketch of the truck on the slope with the person
    standing downhill. Scales axes to the requested distance so the diagram
    stays readable for any slider value.
    """
    theta = math.radians(slope_deg)

    # Road runs from the truck (x=0, top) down to the person (x=distance_m,
    # bottom) along the slope — we use slope-aligned axes for clarity.
    x_road = np.array([0.0, distance_m])
    y_road = np.array([distance_m * math.sin(theta), 0.0])

    fig = go.Figure()

    # Ground / slope line.
    fig.add_trace(
        go.Scatter(
            x=x_road,
            y=y_road,
            mode="lines",
            line={"color": _GROUND_COLOR, "width": 6},
            name="Calle",
            hoverinfo="skip",
        )
    )

    # Horizontal reference at the person's foot to help visualise the drop.
    fig.add_trace(
        go.Scatter(
            x=[0.0, distance_m * 1.05],
            y=[0.0, 0.0],
            mode="lines",
            line={"color": "#bdbdbd", "width": 1, "dash": "dot"},
            name="Horizontal",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Truck at top of slope.
    truck_w = max(distance_m * 0.14, 3.5)
    truck_h = truck_w * 0.44      # aspect ratio of the side-view image (~2.3:1)
    road_top_y = distance_m * math.sin(theta)

    if _VEHICULO_SRC:
        fig.add_layout_image(
            source=_VEHICULO_SRC,
            xref="x", yref="y",
            x=-truck_w / 2,
            y=road_top_y + truck_h,
            sizex=truck_w,
            sizey=truck_h,
            xanchor="left",
            yanchor="top",
            sizing="stretch",
            opacity=0.90,
            layer="above",
        )
        # Invisible hover marker so users still see the tooltip.
        fig.add_trace(
            go.Scatter(
                x=[0.0],
                y=[road_top_y + truck_h / 2],
                mode="markers",
                marker={"size": 1, "opacity": 0},
                name="Camioneta",
                hovertemplate="Camioneta en reposo<extra></extra>",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=[0.0],
                y=[road_top_y],
                mode="markers+text",
                marker={"symbol": "square", "size": 32, "color": _TRUCK_COLOR},
                text=["🚚"],
                textposition="middle center",
                textfont={"size": 22},
                name="Camioneta",
                hovertemplate="Camioneta en reposo<extra></extra>",
            )
        )

    # Person at the bottom.
    fig.add_trace(
        go.Scatter(
            x=[distance_m],
            y=[0.0],
            mode="markers+text",
            marker={"symbol": "circle", "size": 18, "color": _PERSON_COLOR},
            text=["🧍"],
            textposition="top center",
            textfont={"size": 20},
            name="Persona",
            hovertemplate="Persona parada<extra></extra>",
        )
    )

    # Annotation: slope angle at the top.
    fig.add_annotation(
        x=distance_m * 0.15,
        y=distance_m * math.sin(theta) * 0.7,
        text=f"Pendiente: {slope_deg:.1f}°",
        showarrow=False,
        font={"size": 13, "color": _GROUND_COLOR},
    )

    # Annotation: distance along the slope.
    fig.add_annotation(
        x=distance_m * 0.5,
        y=distance_m * math.sin(theta) * 0.5,
        text=f"Distancia: {distance_m:.0f} m",
        showarrow=False,
        yshift=-20,
        font={"size": 13, "color": _GROUND_COLOR},
    )

    if not will_roll:
        fig.add_annotation(
            x=distance_m * 0.5,
            y=distance_m * math.sin(theta) * 0.5 + distance_m * 0.05,
            text="⚠️ La camioneta NO arranca — fricción vence a la gravedad",
            showarrow=False,
            font={"size": 14, "color": "#c62828"},
            bgcolor="rgba(255,235,238,0.9)",
            bordercolor="#c62828",
            borderwidth=1,
        )

    truck_h_for_range = max(distance_m * 0.14, 3.5) * 0.44
    fig.update_layout(
        title="Esquema de la escena",
        xaxis={
            "title": "Distancia horizontal (m)",
            "range": [-distance_m * 0.10, distance_m * 1.1],
        },
        yaxis={
            "title": "Altura (m)",
            "scaleanchor": "x",
            "scaleratio": 1,
            "range": [
                -distance_m * 0.05,
                distance_m * math.sin(theta) + truck_h_for_range * 1.3,
            ],
        },
        showlegend=False,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
        plot_bgcolor="white",
    )
    return fig


def velocity_energy_figure(
    acceleration: float,
    distance_m: float,
    mass_kg: float,
    will_roll: bool,
) -> go.Figure:
    """Return a dual-axis plot of velocity and kinetic energy along the path.

    The x axis is the distance rolled so far (0 → distance_m). This helps the
    user see how both magnitudes grow between the truck and the pedestrian.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if not will_roll or distance_m <= 0 or acceleration <= 0:
        # Flat zero lines, but keep the layout so the UI doesn't jump.
        xs = np.array([0.0, max(distance_m, 1.0)])
        zeros = np.zeros_like(xs)
        fig.add_trace(
            go.Scatter(x=xs, y=zeros, mode="lines", name="v (km/h)",
                       line={"color": "#1565c0", "width": 3}),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=xs, y=zeros, mode="lines", name="E (kJ)",
                       line={"color": "#ef6c00", "width": 3, "dash": "dash"}),
            secondary_y=True,
        )
    else:
        # Sample 100 points along the slope for smooth curves.
        xs = np.linspace(0.0, distance_m, 100)
        v_mps = np.sqrt(2.0 * acceleration * xs)
        v_kmh = v_mps * 3.6
        # Vectorised kinetic energy: avoid calling the scalar helper 100 times.
        e_kj = 0.5 * mass_kg * v_mps**2 / 1000.0

        fig.add_trace(
            go.Scatter(
                x=xs, y=v_kmh, mode="lines", name="Velocidad (km/h)",
                line={"color": "#1565c0", "width": 3},
                hovertemplate="x=%{x:.1f} m<br>v=%{y:.1f} km/h<extra></extra>",
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=xs, y=e_kj, mode="lines", name="Energía (kJ)",
                line={"color": "#ef6c00", "width": 3, "dash": "dash"},
                hovertemplate="x=%{x:.1f} m<br>E=%{y:.1f} kJ<extra></extra>",
            ),
            secondary_y=True,
        )

        # Mark the impact point.
        fig.add_trace(
            go.Scatter(
                x=[distance_m],
                y=[v_kmh[-1]],
                mode="markers",
                marker={"symbol": "x", "size": 12, "color": "#1565c0"},
                name="Impacto",
                hovertemplate="Impacto: %{y:.1f} km/h<extra></extra>",
            ),
            secondary_y=False,
        )

    fig.update_layout(
        title="Velocidad y energía cinética vs. distancia rodada",
        xaxis={"title": "Distancia rodada (m)"},
        legend={"orientation": "h", "y": -0.2},
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
        plot_bgcolor="white",
    )
    fig.update_yaxes(title_text="Velocidad (km/h)", secondary_y=False)
    fig.update_yaxes(title_text="Energía cinética (kJ)", secondary_y=True)
    return fig


# Exposed so tests can confirm that the scalar helper matches the vectorised
# curve used in velocity_energy_figure without reimplementing it.
def _impact_kinetic_energy_kj(mass_kg: float, v_mps: float) -> float:
    return kinetic_energy(mass_kg, v_mps) / 1000.0
