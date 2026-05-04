"""Physical and model constants for the truck-impact simulator."""

from __future__ import annotations

# Gravitational acceleration (m/s^2)
G: float = 9.81

# Rolling-friction coefficient (dimensionless) per surface type.
# Values are typical ranges for passenger-vehicle tires on each surface.
SURFACE_MU_R: dict[str, float] = {
    "asfalto_seco": 0.013,
    "asfalto_mojado": 0.015,
    "concreto": 0.014,
    "grava": 0.020,
}

# Human-readable labels for the surface dropdown (kept separate so UI stays
# declarative and easy to translate).
SURFACE_LABELS: dict[str, str] = {
    "asfalto_seco": "Asfalto seco",
    "asfalto_mojado": "Asfalto mojado",
    "concreto": "Concreto",
    "grava": "Grava / compactado",
}

# Qualitative AIS (Abbreviated Injury Scale) thresholds, keyed by the upper
# bound of impact speed (km/h). Values are conservative pedestrian-impact
# heuristics, not clinical predictions.
AIS_THRESHOLDS: list[tuple[float, str, str]] = [
    # (upper_bound_kmh, label, severity_color)
    (20.0, "AIS 1 — Leve", "#2e7d32"),
    (40.0, "AIS 2 — Moderado", "#f9a825"),
    (60.0, "AIS 3–4 — Grave", "#ef6c00"),
    (float("inf"), "AIS 5–6 — Crítico / mortal probable", "#c62828"),
]

# Rosén & Sander (2009) simplified logistic for pedestrian fatality vs.
# vehicle impact speed (km/h):  P(v) = 1 / (1 + exp(a - b*v))
ROSEN_SANDER_COEFS: dict[str, float] = {
    "a_fatal": 6.9,
    "b_fatal": 0.09,
    # Complementary curve for AIS3+ (serious injury); lower threshold.
    "a_serious": 4.5,
    "b_serious": 0.09,
}

# Detailed AIS descriptions for the educational panel (ordered by severity).
AIS_DESCRIPTIONS: list[dict] = [
    {
        "level": "AIS 1 — Leve",
        "range": "≤ 20 km/h",
        "color": "#2e7d32",
        "bg": "#e8f5e9",
        "clinical": (
            "Lesiones menores que no ponen en riesgo la vida y generalmente "
            "no requieren hospitalización prolongada."
        ),
        "examples": (
            "Contusiones superficiales, laceraciones menores, esguinces leves, "
            "fracturas de huesos pequeños (dedos, nariz), quemaduras superficiales."
        ),
        "prognosis": (
            "Recuperación completa esperada en días a pocas semanas. "
            "Sin secuelas permanentes esperadas."
        ),
        "context": (
            "A ≤ 20 km/h la energía cinética equivale a una caída desde menos de 0.6 m de altura. "
            "La lesión más común en peatones es contusión en extremidades inferiores. "
            "Equivale a la velocidad de un peatón trotando."
        ),
    },
    {
        "level": "AIS 2 — Moderado",
        "range": "20–40 km/h",
        "color": "#f57f17",
        "bg": "#fffde7",
        "clinical": (
            "Lesiones significativas, habitualmente no fatales por sí solas, "
            "pero que requieren atención médica y posiblemente hospitalización."
        ),
        "examples": (
            "Fractura de costillas (1-2), fractura de tibia/peroné sin desplazamiento, "
            "luxaciones, laceraciones profundas, conmoción cerebral leve (Glasgow 13-15)."
        ),
        "prognosis": (
            "Recuperación en semanas a meses. Posibilidad de secuelas menores. "
            "Riesgo de complicaciones si no se trata oportunamente."
        ),
        "context": (
            "Equivalente a la velocidad de un ciclista urbano o la zona residencial (30 km/h). "
            "La energía cinética del vehículo es suficiente para fracturar huesos largos de extremidades "
            "y proyectar al peatón varios metros."
        ),
    },
    {
        "level": "AIS 3–4 — Grave",
        "range": "40–60 km/h",
        "color": "#e65100",
        "bg": "#fff3e0",
        "clinical": (
            "Lesiones graves que amenazan la vida. Requieren atención de emergencia, "
            "cuidados intensivos y posiblemente cirugía de urgencia."
        ),
        "examples": (
            "Fractura abierta de fémur, traumatismo torácico con neumotórax, "
            "hemorragia interna abdominal, traumatismo craneoencefálico moderado (Glasgow 9-12), "
            "fractura de pelvis."
        ),
        "prognosis": (
            "Hospitalización prolongada (semanas a meses). Alta probabilidad de secuelas permanentes "
            "(limitación funcional, dolor crónico). Mortalidad significativa sin atención oportuna."
        ),
        "context": (
            "Velocidades de tráfico urbano estándar (50 km/h). El cuerpo absorbe energías del orden "
            "de decenas de kJ. Las lesiones múltiples simultáneas son la norma, no la excepción. "
            "La mortalidad hospitalaria para AIS 3 es ~5%, para AIS 4 es ~15-20%."
        ),
    },
    {
        "level": "AIS 5–6 — Crítico / Mortal probable",
        "range": "> 60 km/h",
        "color": "#b71c1c",
        "bg": "#ffebee",
        "clinical": (
            "Lesiones críticas con alta probabilidad de muerte. "
            "AIS 6 se define formalmente como lesión incompatible con la vida."
        ),
        "examples": (
            "Traumatismo craneoencefálico severo (Glasgow ≤ 8), lesión de médula espinal con tetraplejia, "
            "rotura aórtica, lesiones múltiples de órganos vitales, aplastamiento torácico severo."
        ),
        "prognosis": (
            "Mortalidad &gt; 50% incluso con atención en centro de trauma nivel I. "
            "Los supervivientes presentan secuelas graves y permanentes. "
            "AIS 6 implica supervivencia prácticamente imposible."
        ),
        "context": (
            "Velocidades de vía rápida o carretera. La energía cinética supera la capacidad estructural "
            "del esqueleto y órganos vitales. Según el modelo de Rosén &amp; Sander, "
            "la probabilidad de fatalidad supera el 90% a ~80 km/h. "
            "En estudios forenses europeos, &gt;70% de los peatones fallecen a impactos &gt; 65 km/h."
        ),
    },
]

# Bibliographic references in APA 7th edition format.
APA_REFERENCES: list[str] = [
    (
        "Rosén, E., &amp; Sander, U. (2009). Pedestrian fatality risk as a function of car impact speed. "
        "<em>Accident Analysis &amp; Prevention, 41</em>(3), 536–542. "
        "https://doi.org/10.1016/j.aap.2009.02.003"
    ),
    (
        "Association for the Advancement of Automotive Medicine. (2008). "
        "<em>The Abbreviated Injury Scale 2005 — Update 2008</em>. AAAM."
    ),
    (
        "Beer, F. P., Johnston, E. R., &amp; Cornwell, P. J. (2013). "
        "<em>Vector mechanics for engineers: Dynamics</em> (11.ª ed.). McGraw-Hill Education."
    ),
    (
        "World Health Organization. (2023). "
        "<em>Global status report on road safety 2023</em>. WHO. "
        "https://www.who.int/publications/i/item/9789240086517"
    ),
    (
        "Fugger, T. F., Randles, B. C., Wobrock, J. L., &amp; Smith, J. (2002). "
        "Pedestrian throw kinematics in forward projection collisions. "
        "<em>SAE Technical Paper 2002-01-0019</em>. "
        "https://doi.org/10.4271/2002-01-0019"
    ),
    (
        "Otte, D. (1999). Severity and mechanism of head impacts in car-to-pedestrian accidents. "
        "<em>International Journal of Crashworthiness, 4</em>(4), 373–380. "
        "https://doi.org/10.1533/cras.1999.0111"
    ),
]
