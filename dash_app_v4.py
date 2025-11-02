# -*- coding: utf-8 -*-
"""
Dashboard IMSS – Plataformas Digitales (v4.1)
- Hovers: etiquetas limpias (“Personas beneficiadas”, “Personas trabajadoras de plataformas (TDP)”)
- Leyenda verde para hombres en pirámides
- Título final: “Estructura de género (Beneficiadas, TDP e Independientes)”
- Paleta institucional (guinda, dorado, verde) y tipografía Montserrat
"""

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
import unicodedata

# ===== Paleta =====
GUINDA = "#9d2148"
DORADO = "#b28e5c"
VERDE  = "#027a35"

# ===== Datos =====
df = pd.read_csv("PD_sep.csv", encoding="utf-8-sig")
df["entidad_display"] = df["entidad_nacimiento"].astype(str)

def norm_txt(s):
    if not isinstance(s, str): return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return s.strip()

df["entidad_norm"] = df["entidad_display"].apply(norm_txt)

# Trabajadores independientes
df["independientes_H"] = (pd.to_numeric(df["PTPD_Aseg_H"], errors="coerce").fillna(0)
                          - pd.to_numeric(df["PTPD_Puestos_H"], errors="coerce").fillna(0))
df["independientes_M"] = (pd.to_numeric(df["PTPD_Aseg_M"], errors="coerce").fillna(0)
                          - pd.to_numeric(df["PTPD_Puestos_M"], errors="coerce").fillna(0))

# ================================================================
# 1) Personas beneficiadas por entidad
ent = (df.groupby("entidad_display", as_index=False)["PTPD_Aseg"]
       .sum()
       .sort_values("PTPD_Aseg", ascending=True))

fig1 = px.bar(
    ent, x="PTPD_Aseg", y="entidad_display", orientation="h",
    color_discrete_sequence=[GUINDA],
    title="Total de personas beneficiadas por entidad"
)
fig1.update_traces(
    texttemplate="%{x:,.0f}", textposition="outside",
    hovertemplate="<b>%{y}</b><br>Personas beneficiadas: %{x:,.0f}<extra></extra>"
)
fig1.update_layout(
    plot_bgcolor="white",
    font=dict(family="Montserrat", color="#333"),
    xaxis_title="Personas beneficiadas",
    yaxis_title="",
    margin=dict(l=80, r=40, t=60, b=30)
)

# ================================================================
# 2) Beneficiadas vs TDP por entidad
agg = (df.groupby("entidad_display", as_index=False)[["PTPD_Aseg","PTPD_Puestos"]]
       .sum()
       .sort_values("PTPD_Aseg", ascending=True))

fig2 = px.bar(
    agg, y="entidad_display", x=["PTPD_Aseg","PTPD_Puestos"],
    orientation="h", barmode="group",
    color_discrete_map={"PTPD_Aseg": GUINDA, "PTPD_Puestos": DORADO},
    title="Personas beneficiadas vs Personas trabajadoras de plataformas (TDP)"
)
fig2.update_traces(
    hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>"
)
# Renombrar leyenda
fig2.for_each_trace(lambda t: t.update(name="Personas beneficiadas" if "Aseg" in t.name else "Personas trabajadoras de plataformas (TDP)"))
fig2.update_layout(
    plot_bgcolor="white",
    font=dict(family="Montserrat", color="#333"),
    xaxis_title="Registros",
    yaxis_title="",
    legend_title_text="Indicador",
    margin=dict(l=80, r=40, t=60, b=30)
)

# ================================================================
# 3) Pirámide nacional
age_nat = (df.groupby("Rango_edad_2", as_index=False)
             [["PTPD_Aseg_H","PTPD_Aseg_M"]].sum())
age_nat = age_nat.sort_values("Rango_edad_2")
men_nat_abs = age_nat["PTPD_Aseg_H"].abs()
age_nat["PTPD_Aseg_H_neg"] = -men_nat_abs

fig3 = px.bar(
    age_nat, x="PTPD_Aseg_H_neg", y="Rango_edad_2", orientation="h",
    color_discrete_sequence=[VERDE], title="Pirámide poblacional nacional"
)
fig3.add_bar(
    x=age_nat["PTPD_Aseg_M"], y=age_nat["Rango_edad_2"],
    orientation="h", marker_color=GUINDA, name="Mujeres",
    hovertemplate="<b>Mujeres beneficiadas</b>: %{x:,.0f}<br>Edad: %{y}<extra></extra>"
)
fig3.add_bar(
    x=age_nat["PTPD_Aseg_H_neg"], y=age_nat["Rango_edad_2"],
    orientation="h", marker_color=VERDE, name="Hombres",
    hovertemplate="<b>Hombres beneficiados</b>: %{customdata:,.0f}<br>Edad: %{y}<extra></extra>",
    customdata=men_nat_abs
)
fig3.update_layout(
    barmode="overlay",
    plot_bgcolor="white",
    font=dict(family="Montserrat", color="#333"),
    xaxis_title="Personas",
    yaxis_title="Edad"
)

# ================================================================
# 4) Pirámide CDMX
mask_cdmx = df["entidad_norm"].str.contains("ciudad de mexico|cdmx|distrito federal", na=False)
df_cdmx = df[mask_cdmx].copy()

if not df_cdmx.empty:
    age_cdmx = (df_cdmx.groupby("Rango_edad_2", as_index=False)
                [["PTPD_Aseg_H","PTPD_Aseg_M"]].sum())
    age_cdmx = age_cdmx.sort_values("Rango_edad_2")
    men_cdmx_abs = age_cdmx["PTPD_Aseg_H"].abs()
    age_cdmx["PTPD_Aseg_H_neg"] = -men_cdmx_abs

    fig4 = px.bar(
        age_cdmx, x="PTPD_Aseg_H_neg", y="Rango_edad_2", orientation="h",
        color_discrete_sequence=[VERDE], title="Pirámide poblacional CDMX"
    )
    fig4.add_bar(
        x=age_cdmx["PTPD_Aseg_M"], y=age_cdmx["Rango_edad_2"],
        orientation="h", marker_color=GUINDA, name="Mujeres",
        hovertemplate="<b>Mujeres beneficiadas</b>: %{x:,.0f}<br>Edad: %{y}<extra></extra>"
    )
    fig4.add_bar(
        x=age_cdmx["PTPD_Aseg_H_neg"], y=age_cdmx["Rango_edad_2"],
        orientation="h", marker_color=VERDE, name="Hombres",
        hovertemplate="<b>Hombres beneficiados</b>: %{customdata:,.0f}<br>Edad: %{y}<extra></extra>",
        customdata=men_cdmx_abs
    )
    fig4.update_layout(
        barmode="overlay",
        plot_bgcolor="white",
        font=dict(family="Montserrat", color="#333"),
        xaxis_title="Personas",
        yaxis_title="Edad"
    )
else:
    fig4 = px.bar(title="Pirámide poblacional CDMX (sin registros)")
    fig4.update_layout(plot_bgcolor="white", font=dict(family="Montserrat", color="#333"))

# ================================================================
# 5) Estructura de género: Beneficiadas, TDP e Independientes
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
    title="Estructura de género (Beneficiadas, TDP e Independientes)"
)
fig5.update_traces(
    hovertemplate="<b>%{x}</b>: %{y:,.0f}<extra></extra>"
)
fig5.update_layout(
    plot_bgcolor="white",
    font=dict(family="Montserrat", color="#333"),
    xaxis_title="",
    yaxis_title="Personas"
)

# ================================================================
# Layout general
app = dash.Dash(__name__, title="IMSS Plataformas Digitales – v4.1")

app.layout = html.Div(style={
    "fontFamily": "Montserrat",
    "backgroundColor": "#ffffff",
    "padding": "10px"
}, children=[
    html.H1("📊 Dashboard IMSS – Plataformas Digitales", 
            style={"color": GUINDA, "textAlign": "center", "marginBottom": "10px"}),

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

if __name__ == "__main__":
    app.run(debug=True)
