"""Shiny app: truck rolling down a slope, impact estimation on a pedestrian."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path regardless of how the app is invoked (local,
# `shiny run src/app.py`, or deployed as `src.app`).
_src = Path(__file__).parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from shiny import App, reactive, render, ui

import report
from constants import AIS_DESCRIPTIONS, APA_REFERENCES, SURFACE_LABELS
from physics import SimulationResult, simulate
from plotting import scene_figure, velocity_energy_figure


def _plotly_html(fig) -> ui.HTML:
    return ui.HTML(
        fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
            config={"displaylogo": False, "responsive": True},
        )
    )


_SURFACE_CHOICES = dict(SURFACE_LABELS.items())

_DEFAULT_SLOPE_DEG = 5.0
_DEFAULT_DISTANCE_M = 30
_DEFAULT_MASS_KG = 2400

# ── UI helpers ────────────────────────────────────────────────────────────────

def _value_tile(title: str, value: str, subtitle: str, bg: str, fg: str) -> ui.Tag:
    base = "padding:1rem; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.10);"
    return ui.div(
        ui.p(title, style=f"margin:0; font-size:0.82rem; font-weight:600; color:{fg}; opacity:.75;"),
        ui.h3(value, style=f"margin:0.25rem 0; color:{fg}; font-size:1.5rem;"),
        ui.p(subtitle, style=f"margin:0; font-size:0.78rem; color:{fg}; opacity:.80;"),
        style=f"{base} background:{bg};",
    )


def _ais_panel(desc: dict) -> ui.Tag:
    return ui.div(
        ui.div(
            ui.tags.span(
                desc["level"],
                style=(
                    f"background:{desc['color']}; color:#fff; padding:3px 10px; "
                    "border-radius:12px; font-weight:700; font-size:0.85rem;"
                ),
            ),
            ui.tags.span(
                f" · Velocidades {desc['range']}",
                style="font-size:0.85rem; color:#555; margin-left:8px;",
            ),
            style="margin-bottom:0.6rem;",
        ),
        ui.tags.table(
            ui.tags.tr(
                ui.tags.td(ui.tags.b("Descripción clínica"), style="width:11rem; vertical-align:top; padding:3px 8px 3px 0;"),
                ui.tags.td(ui.HTML(desc["clinical"]), style="padding:3px 0;"),
            ),
            ui.tags.tr(
                ui.tags.td(ui.tags.b("Ejemplos de lesiones"), style="vertical-align:top; padding:3px 8px 3px 0;"),
                ui.tags.td(ui.HTML(desc["examples"]), style="padding:3px 0;"),
            ),
            ui.tags.tr(
                ui.tags.td(ui.tags.b("Pronóstico"), style="vertical-align:top; padding:3px 8px 3px 0;"),
                ui.tags.td(ui.HTML(desc["prognosis"]), style="padding:3px 0;"),
            ),
            ui.tags.tr(
                ui.tags.td(ui.tags.b("Contexto práctico"), style="vertical-align:top; padding:3px 8px 3px 0;"),
                ui.tags.td(ui.HTML(desc["context"]), style="padding:3px 0;"),
            ),
            style="width:100%; border-collapse:collapse; font-size:0.88rem; line-height:1.5;",
        ),
        style=(
            f"padding:1rem 1.2rem; border-left:4px solid {desc['color']}; "
            f"background:{desc['bg']}; border-radius:0 8px 8px 0; margin-bottom:0.8rem;"
        ),
    )


# ── Layout ────────────────────────────────────────────────────────────────────

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h5("Parámetros de entrada", style="margin-bottom:0.8rem; color:#1565c0;"),
        ui.input_slider("slope_deg", "Pendiente (°)", min=0.0, max=25.0,
                        value=_DEFAULT_SLOPE_DEG, step=0.5),
        ui.input_slider("distance_m", "Distancia a la persona (m)", min=1, max=200,
                        value=_DEFAULT_DISTANCE_M, step=1),
        ui.input_numeric("mass_kg", "Masa de la camioneta (kg)",
                         value=_DEFAULT_MASS_KG, min=500, max=6000, step=50),
        ui.input_select("surface", "Superficie de rodadura",
                        choices=_SURFACE_CHOICES, selected="asfalto_seco"),
        ui.hr(),
        ui.input_action_button(
            "run_btn", "▶  Calcular impacto",
            class_="btn-primary w-100",
            style="font-weight:700; font-size:1rem;",
        ),
        ui.p(
            "Ajusta los parámetros y presiona Calcular para actualizar los resultados.",
            style="font-size:0.78rem; color:#777; margin-top:0.5rem; text-align:center;",
        ),
        ui.hr(),
        ui.p("Descargar memoria de cálculo:",
             style="font-size:0.82rem; font-weight:600; margin-bottom:0.4rem;"),
        ui.download_button(
            "download_pdf", "📄  PDF",
            class_="btn-outline-danger w-100",
            style="margin-bottom:0.4rem;",
        ),
        ui.download_button(
            "download_docx", "📝  Word (.docx)",
            class_="btn-outline-primary w-100",
        ),
        ui.hr(),
        ui.help_text(
            ui.markdown(
                "**Modelo físico**\n\n"
                "- `a = g·(sen θ − μ_r·cos θ)`\n"
                "- `v = √(2·a·d)`\n"
                "- `E = ½·m·v²`\n"
                "- P(fatal): Rosén & Sander, 2009"
            )
        ),
        title="Simulador de impacto",
        width=310,
    ),

    # Status banner
    ui.output_ui("status_banner"),

    # Scene + profile side by side
    ui.layout_columns(
        ui.card(
            ui.card_header("Esquema de la escena"),
            ui.output_ui("scene_plot"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Perfil de velocidad y energía"),
            ui.output_ui("profile_plot"),
            full_screen=True,
        ),
        col_widths=[6, 6],
    ),

    # Impact results
    ui.card(
        ui.card_header("Resultados en el impacto"),
        ui.output_ui("impact_results"),
        full_screen=True,
    ),

    # AIS explanation
    ui.card(
        ui.card_header("Niveles de lesión AIS — Explicación detallada"),
        ui.output_ui("ais_panel"),
        full_screen=True,
    ),

    # References
    ui.card(
        ui.card_header("Referencias bibliográficas (APA 7.ª ed.)"),
        ui.output_ui("references_panel"),
    ),

    title="Simulador de impacto — camioneta en pendiente",
    fillable=False,
)


# ── Server ────────────────────────────────────────────────────────────────────

def server(input, output, session):  # noqa: A002

    @reactive.calc
    def sim() -> SimulationResult:
        # Re-run only when the button is pressed; read sliders in isolation.
        input.run_btn()
        with reactive.isolate():
            return simulate(
                slope_deg=float(input.slope_deg()),
                distance_m=float(input.distance_m()),
                mass_kg=float(input.mass_kg()),
                surface_key=str(input.surface()),
            )

    # ── Status banner ────────────────────────────────────────────────────────

    @output
    @render.ui
    def status_banner():
        if sim().will_roll:
            return ui.div()
        return ui.div(
            ui.markdown(
                "⚠️ **La camioneta no arranca en estas condiciones.** "
                "La fricción de rodadura supera la componente gravitacional. "
                "Sube la pendiente o cambia la superficie para ver un impacto."
            ),
            style=(
                "padding:0.8rem 1rem; border:1px solid #c62828; "
                "background:#ffebee; border-radius:8px; "
                "margin-bottom:1rem; color:#b71c1c;"
            ),
        )

    # ── Plots ────────────────────────────────────────────────────────────────

    @output
    @render.ui
    def scene_plot():
        result = sim()
        with reactive.isolate():
            slope_deg = float(input.slope_deg())
            distance_m = float(input.distance_m())
        fig = scene_figure(
            slope_deg=slope_deg,
            distance_m=distance_m,
            will_roll=result.will_roll,
        )
        return _plotly_html(fig)

    @output
    @render.ui
    def profile_plot():
        result = sim()
        with reactive.isolate():
            distance_m = float(input.distance_m())
            mass_kg = float(input.mass_kg())
        fig = velocity_energy_figure(
            acceleration=result.acceleration,
            distance_m=distance_m,
            mass_kg=mass_kg,
            will_roll=result.will_roll,
        )
        return _plotly_html(fig)

    # ── Impact results ───────────────────────────────────────────────────────

    @output
    @render.ui
    def impact_results():
        result = sim()
        if not result.will_roll:
            return ui.p(
                "Sin impacto — la camioneta permanece en reposo.",
                style="font-size:1rem; color:#555;",
            )
        v_kmh = result.v_impact_kmh
        v_mps = result.v_impact_mps
        e_kj = result.kinetic_energy_j / 1000.0
        p_fatal_pct = result.fatality_probability * 100.0
        p_serious_pct = result.serious_injury_probability * 100.0

        return ui.layout_columns(
            _value_tile("Velocidad de impacto", f"{v_kmh:.1f} km/h",
                        f"{v_mps:.2f} m/s", "#e3f2fd", "#0d47a1"),
            _value_tile("Energía cinética", f"{e_kj:.1f} kJ",
                        f"{result.kinetic_energy_j:,.0f} J", "#fff3e0", "#e65100"),
            _value_tile("Prob. fatalidad peatón", f"{p_fatal_pct:.1f}%",
                        f"Lesión grave (AIS3+): {p_serious_pct:.1f}%", "#fce4ec", "#880e4f"),
            _value_tile("Nivel AIS", result.ais_label,
                        "Escala Abbreviated Injury Scale", "#ede7f6", result.ais_color),
            col_widths=[3, 3, 3, 3],
        )

    # ── AIS explanation ──────────────────────────────────────────────────────

    @output
    @render.ui
    def ais_panel():
        result = sim()
        panels = []
        for desc in AIS_DESCRIPTIONS:
            ais_key = desc["level"].split("—")[0].strip()
            is_active = result.will_roll and result.ais_label.startswith(ais_key)
            panel = ui.div(
                _ais_panel(desc),
                style=(
                    "outline: 3px solid " + desc["color"] + "; "
                    "border-radius:8px; margin-bottom:0.5rem;"
                ) if is_active else "margin-bottom:0.5rem;",
            )
            if is_active:
                panels.insert(0, ui.div(
                    ui.tags.span(
                        "▲ Nivel activo según los resultados del cálculo",
                        style=(
                            f"font-weight:700; color:{desc['color']}; "
                            "font-size:0.82rem; display:block; margin-bottom:0.4rem;"
                        ),
                    ),
                    panel,
                ))
            else:
                panels.append(panel)
        return ui.div(
            ui.p(
                "La escala AIS (Abbreviated Injury Scale) es el estándar internacional "
                "para clasificar la gravedad de lesiones traumáticas. Fue desarrollada por "
                "la Association for the Advancement of Automotive Medicine (AAAM) y se usa "
                "en medicina forense, epidemiología vial y diseño de sistemas de seguridad.",
                style="font-size:0.9rem; color:#444; margin-bottom:1rem;",
            ),
            *panels,
        )

    # ── References ───────────────────────────────────────────────────────────

    @output
    @render.ui
    def references_panel():
        items = [
            ui.tags.li(
                ui.HTML(ref),
                style="margin-bottom:0.5rem; font-size:0.88rem; line-height:1.6;",
            )
            for ref in APA_REFERENCES
        ]
        return ui.tags.ol(*items, style="padding-left:1.5rem; margin:0;")

    # ── Downloads ────────────────────────────────────────────────────────────

    @render.download(filename="memoria_calculo.pdf", media_type="application/pdf")
    def download_pdf():
        with reactive.isolate():
            slope_deg = float(input.slope_deg())
            distance_m = float(input.distance_m())
            mass_kg = float(input.mass_kg())
            surface_key = str(input.surface())
        result = simulate(slope_deg, distance_m, mass_kg, surface_key)
        yield report.generate_pdf(result, slope_deg, distance_m, mass_kg, surface_key)

    @render.download(filename="memoria_calculo.docx",
                     media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    def download_docx():
        with reactive.isolate():
            slope_deg = float(input.slope_deg())
            distance_m = float(input.distance_m())
            mass_kg = float(input.mass_kg())
            surface_key = str(input.surface())
        result = simulate(slope_deg, distance_m, mass_kg, surface_key)
        yield report.generate_docx(result, slope_deg, distance_m, mass_kg, surface_key)


# ── Static assets ─────────────────────────────────────────────────────────────
_www = Path(__file__).parent / "www"

app = App(app_ui, server, static_assets=_www)
