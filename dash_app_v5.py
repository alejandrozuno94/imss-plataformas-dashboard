# -*- coding: utf-8 -*-
"""
Dashboard IMSS – Plataformas Digitales (v5, con pestañas y evolución)
Requiere: PD_jul.csv, PD_ago.csv, PD_sep.csv en la misma carpeta.

Pestañas:
- Julio / Agosto / Septiembre: mismas gráficas (entidades, vs TDP, pirámides, estructura de género).
- Evolución: Nacional y CDMX
    * Totales: Beneficiados, TDP, Independientes
    * Tasa de formalización: TDP/Beneficiados*100
    * Series por género: Beneficiados H/M, TDP H/M, Independientes H/M
"""

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
import unicodedata

# ================== Paleta y estilo ==================
GUINDA = "#9d2148"
DORADO = "#b28e5c"
VERDE  = "#027a35"

FONT = dict(family="Montserrat", color="#333")
BG = "white"

# ================== Utilidades ==================
def norm_txt(s):
    if not isinstance(s, str):
        return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                if unicodedata.category(c) != 'Mn')
    return s.strip()

def cargar_mes(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    """Lee CSV del mes, agrega columnas derivadas y etiqueta de mes."""
    df = pd.read_csv(path_csv, encoding="utf-8-sig")
    df["Mes"] = etiqueta_mes
    df["entidad_display"] = df["entidad_nacimiento"].astype(str)
    df["entidad_norm"] = df["entidad_display"].apply(norm_txt)

    # Independientes H/M y total
    for col in ["PTPD_Aseg_H", "PTPD_Aseg_M", "PTPD_Puestos_H", "PTPD_Puestos_M",
                "PTPD_Aseg", "PTPD_Puestos"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["independientes_H"] = df["PTPD_Aseg_H"] - df["PTPD_Puestos_H"]
    df["independientes_M"] = df["PTPD_Aseg_M"] - df["PTPD_Puestos_M"]
    df["independientes"]   = df["independientes_H"] + df["independientes_M"]
    return df

def filtro_cdmx(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["entidad_norm"].str.contains(
        "ciudad de mexico|cdmx|distrito federal",
        na=False
    )
    return df[mask].copy()

# ================== Figuras por mes (tab) ==================
def layout_mes(df: pd.DataFrame, mes_label: str) -> html.Div:
    # 1) Total beneficiadas por entidad
    ent = (df.groupby("entidad_display", as_index=False)["PTPD_Aseg"]
             .sum().sort_values("PTPD_Aseg", ascending=True))
    fig1 = px.bar(
        ent, x="PTPD_Aseg", y="entidad_display", orientation="h",
        color_discrete_sequence=[GUINDA],
        title=f"Total de personas beneficiadas por entidad ({mes_label})"
    )
    fig1.update_traces(
        texttemplate="%{x:,.0f}", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Personas beneficiadas: %{x:,.0f}<extra></extra>"
    )
    fig1.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Personas beneficiadas",
                       yaxis_title="", margin=dict(l=80, r=40, t=60, b=30))

    # 2) Beneficiadas vs TDP por entidad
    agg = (df.groupby("entidad_display", as_index=False)[["PTPD_Aseg", "PTPD_Puestos"]]
             .sum().sort_values("PTPD_Aseg", ascending=True))
    fig2 = px.bar(
        agg, y="entidad_display", x=["PTPD_Aseg", "PTPD_Puestos"],
        orientation="h", barmode="group",
        color_discrete_map={"PTPD_Aseg": GUINDA, "PTPD_Puestos": DORADO},
        title=f"Personas beneficiadas vs Personas trabajadoras de plataformas (TDP) ({mes_label})"
    )
    fig2.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>")
    fig2.for_each_trace(lambda t: t.update(
        name="Personas beneficiadas" if "Aseg" in t.name else "Personas trabajadoras de plataformas (TDP)"
    ))
    fig2.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Registros", yaxis_title="",
                       legend_title_text="Indicador", margin=dict(l=80, r=40, t=60, b=30))

    # 3) Pirámide nacional
    age_nat = (df.groupby("Rango_edad_2", as_index=False)[["PTPD_Aseg_H", "PTPD_Aseg_M"]].sum()
                 .sort_values("Rango_edad_2"))
    men_nat_abs = age_nat["PTPD_Aseg_H"].abs()
    age_nat["PTPD_Aseg_H_neg"] = -men_nat_abs

    fig3 = px.bar(age_nat, x="PTPD_Aseg_H_neg", y="Rango_edad_2", orientation="h",
                  color_discrete_sequence=[VERDE],
                  title=f"Pirámide poblacional de personas beneficiadas – Nacional ({mes_label})")
    fig3.add_bar(x=age_nat["PTPD_Aseg_M"], y=age_nat["Rango_edad_2"],
                 orientation="h", marker_color=GUINDA, name="Mujeres",
                 hovertemplate="<b>Mujeres beneficiadas</b>: %{x:,.0f}<br>Edad: %{y}<extra></extra>")
    fig3.add_bar(x=age_nat["PTPD_Aseg_H_neg"], y=age_nat["Rango_edad_2"],
                 orientation="h", marker_color=VERDE, name="Hombres",
                 hovertemplate="<b>Hombres beneficiados</b>: %{customdata:,.0f}<br>Edad: %{y}<extra></extra>",
                 customdata=men_nat_abs)
    fig3.update_layout(barmode="overlay", plot_bgcolor=BG, font=FONT,
                       xaxis_title="Personas", yaxis_title="Edad")

    # 4) Pirámide CDMX
    df_cdmx = filtro_cdmx(df)
    if not df_cdmx.empty:
        age_cdmx = (df_cdmx.groupby("Rango_edad_2", as_index=False)[["PTPD_Aseg_H", "PTPD_Aseg_M"]].sum()
                      .sort_values("Rango_edad_2"))
        men_cdmx_abs = age_cdmx["PTPD_Aseg_H"].abs()
        age_cdmx["PTPD_Aseg_H_neg"] = -men_cdmx_abs

        fig4 = px.bar(age_cdmx, x="PTPD_Aseg_H_neg", y="Rango_edad_2", orientation="h",
                      color_discrete_sequence=[VERDE],
                      title=f"Pirámide poblacional de personas beneficiadas – CDMX ({mes_label})")
        fig4.add_bar(x=age_cdmx["PTPD_Aseg_M"], y=age_cdmx["Rango_edad_2"],
                     orientation="h", marker_color=GUINDA, name="Mujeres",
                     hovertemplate="<b>Mujeres beneficiadas</b>: %{x:,.0f}<br>Edad: %{y}<extra></extra>")
        fig4.add_bar(x=age_cdmx["PTPD_Aseg_H_neg"], y=age_cdmx["Rango_edad_2"],
                     orientation="h", marker_color=VERDE, name="Hombres",
                     hovertemplate="<b>Hombres beneficiados</b>: %{customdata:,.0f}<br>Edad: %{y}<extra></extra>",
                     customdata=men_cdmx_abs)
        fig4.update_layout(barmode="overlay", plot_bgcolor=BG, font=FONT,
                           xaxis_title="Personas", yaxis_title="Edad")
    else:
        fig4 = px.bar(title=f"Pirámide poblacional CDMX ({mes_label}) – sin registros")
        fig4.update_layout(plot_bgcolor=BG, font=FONT)

    # 5) Estructura de género (beneficiadas, TDP e independientes)
    totales = pd.DataFrame({
        "Etiqueta": [
            "Hombres beneficiados", "Mujeres beneficiadas",
            "Hombres TDP", "Mujeres TDP",
            "Hombres independientes", "Mujeres independientes"
        ],
        "Valor": [
            df["PTPD_Aseg_H"].sum(), df["PTPD_Aseg_M"].sum(),
            df["PTPD_Puestos_H"].sum(), df["PTPD_Puestos_M"].sum(),
            df["independientes_H"].sum(), df["independientes_M"].sum()
        ],
        "Color": [VERDE, GUINDA, DORADO, DORADO, VERDE, GUINDA]
    })
    fig5 = px.bar(
        totales, x="Etiqueta", y="Valor", color="Etiqueta",
        color_discrete_sequence=[VERDE, GUINDA, DORADO, DORADO, VERDE, GUINDA],
        title=f"Estructura de género (Beneficiadas, TDP e Independientes) ({mes_label})"
    )
    fig5.update_traces(hovertemplate="<b>%{x}</b>: %{y:,.0f}<extra></extra>")
    fig5.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="", yaxis_title="Personas")

    return html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig1), style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig2), style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "float": "right"})
        ], style={"marginBottom": "18px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig3), style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig4), style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "float": "right"})
        ], style={"marginBottom": "18px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig5), style={"width": "80%", "margin": "auto"})
        ])
    ])

# ================== Evolución (series temporales) ==================
def layout_evolucion(df_jul: pd.DataFrame, df_ago: pd.DataFrame, df_sep: pd.DataFrame) -> html.Div:
    # Unimos meses
    df_all = pd.concat([df_jul, df_ago, df_sep], ignore_index=True)
    # Orden de meses
    orden = ["Julio", "Agosto", "Septiembre"]
    df_all["Mes"] = pd.Categorical(df_all["Mes"], categories=orden, ordered=True)

    # --------- Agregados nacionales ---------
    nat = (df_all.groupby("Mes", as_index=False)[
        ["PTPD_Aseg", "PTPD_Puestos", "independientes",
         "PTPD_Aseg_H", "PTPD_Aseg_M",
         "PTPD_Puestos_H", "PTPD_Puestos_M",
         "independientes_H", "independientes_M"]
    ].sum())
    nat["tasa_formalizacion"] = (nat["PTPD_Puestos"] / nat["PTPD_Aseg"] * 100).round(2)

    # --------- Agregados CDMX ---------
    cdmx = filtro_cdmx(df_all)
    cdmx_agg = (cdmx.groupby("Mes", as_index=False)[
        ["PTPD_Aseg", "PTPD_Puestos", "independientes",
         "PTPD_Aseg_H", "PTPD_Aseg_M",
         "PTPD_Puestos_H", "PTPD_Puestos_M",
         "independientes_H", "independientes_M"]
    ].sum())
    cdmx_agg["tasa_formalizacion"] = (cdmx_agg["PTPD_Puestos"] / cdmx_agg["PTPD_Aseg"] * 100).round(2)

    # ---------- Función de líneas multi-serie ----------
    def line_multi(df, cols, titulo, ytitle):
        df_long = df.melt(id_vars="Mes", value_vars=cols, var_name="Serie", value_name="Valor")
        renombres = {
            "PTPD_Aseg": "Beneficiados",
            "PTPD_Puestos": "TDP",
            "independientes": "Independientes",
            "PTPD_Aseg_H": "Beneficiados H",
            "PTPD_Aseg_M": "Beneficiados M",
            "PTPD_Puestos_H": "TDP H",
            "PTPD_Puestos_M": "TDP M",
            "independientes_H": "Independientes H",
            "independientes_M": "Independientes M",
        }
        df_long["Serie"] = df_long["Serie"].map(renombres).fillna(df_long["Serie"])
        fig = px.line(df_long, x="Mes", y="Valor", color="Serie",
                      color_discrete_sequence=[GUINDA, DORADO, VERDE, "#5c1a2f", "#c0708f", "#806443", "#d7b58a", "#0c4f2b", "#5fb083"],
                      markers=True, title=titulo)
        fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:,.0f}<extra></extra>")
        fig.update_layout(plot_bgcolor=BG, font=FONT, yaxis_title=ytitle, xaxis_title="Mes")
        return fig

    def line_rate(df, colrate, titulo):
        fig = px.line(df, x="Mes", y=colrate, color_discrete_sequence=[GUINDA],
                      markers=True, title=titulo)
        fig.update_traces(hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra></extra>")
        fig.update_layout(plot_bgcolor=BG, font=FONT, yaxis_title="Porcentaje", xaxis_title="Mes")
        return fig

    # ---- Figuras Nacional ----
    fig_nat_totales = line_multi(nat, ["PTPD_Aseg", "PTPD_Puestos", "independientes"],
                                "Nacional: Beneficiados, TDP e Independientes", "Personas")
    fig_nat_tasa    = line_rate(nat, "tasa_formalizacion", "Nacional: Tasa de formalización (TDP/Beneficiados)")
    fig_nat_bene_g  = line_multi(nat, ["PTPD_Aseg_H", "PTPD_Aseg_M"], "Nacional: Beneficiados por género", "Personas")
    fig_nat_tdp_g   = line_multi(nat, ["PTPD_Puestos_H", "PTPD_Puestos_M"], "Nacional: TDP por género", "Personas")
    fig_nat_ind_g   = line_multi(nat, ["independientes_H", "independientes_M"], "Nacional: Independientes por género", "Personas")

    # ---- Figuras CDMX ----
    fig_cdmx_totales = line_multi(cdmx_agg, ["PTPD_Aseg", "PTPD_Puestos", "independientes"],
                                  "CDMX: Beneficiados, TDP e Independientes", "Personas")
    fig_cdmx_tasa    = line_rate(cdmx_agg, "tasa_formalizacion", "CDMX: Tasa de formalización (TDP/Beneficiados)")
    fig_cdmx_bene_g  = line_multi(cdmx_agg, ["PTPD_Aseg_H", "PTPD_Aseg_M"], "CDMX: Beneficiados por género", "Personas")
    fig_cdmx_tdp_g   = line_multi(cdmx_agg, ["PTPD_Puestos_H", "PTPD_Puestos_M"], "CDMX: TDP por género", "Personas")
    fig_cdmx_ind_g   = line_multi(cdmx_agg, ["independientes_H", "independientes_M"], "CDMX: Independientes por género", "Personas")

    return html.Div([
        html.H2("Evolución – Nacional", style={"color": GUINDA, "textAlign": "left"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_totales), style={"width": "48%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_tasa),    style={"width": "48%", "display": "inline-block", "float": "right"}),
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_bene_g), style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig_nat_tdp_g),  style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig_nat_ind_g),  style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
        ], style={"marginBottom": "28px"}),

        html.H2("Evolución – Ciudad de México", style={"color": GUINDA, "textAlign": "left"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_totales), style={"width": "48%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_tasa),    style={"width": "48%", "display": "inline-block", "float": "right"}),
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_bene_g), style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig_cdmx_tdp_g),  style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig_cdmx_ind_g),  style={"width": "32%", "display": "inline-block", "verticalAlign": "top"}),
        ])
    ])

# ================== App y Tabs ==================
app = dash.Dash(__name__, title="IMSS Plataformas Digitales – v5")

# Carga de datos mensuales
df_jul = cargar_mes("PD_jul.csv", "Julio")
df_ago = cargar_mes("PD_ago.csv", "Agosto")
df_sep = cargar_mes("PD_sep.csv", "Septiembre")

app.layout = html.Div(style={
    "fontFamily": "Montserrat",
    "backgroundColor": "#ffffff",
    "padding": "12px"
}, children=[
    html.H1("📊 Dashboard IMSS – Plataformas Digitales", 
            style={"color": GUINDA, "textAlign": "center", "marginBottom": "12px"}),

    dcc.Tabs([
        dcc.Tab(label="Julio", children=[layout_mes(df_jul, "Julio")]),
        dcc.Tab(label="Agosto", children=[layout_mes(df_ago, "Agosto")]),
        dcc.Tab(label="Septiembre", children=[layout_mes(df_sep, "Septiembre")]),
        dcc.Tab(label="Evolución", children=[layout_evolucion(df_jul, df_ago, df_sep)])
    ])
])

if __name__ == "__main__":
    # Para Render: 0.0.0.0 y puerto fijo
    app.run(host="0.0.0.0", port=10000, debug=False)
