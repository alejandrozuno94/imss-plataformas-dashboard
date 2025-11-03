# -*- coding: utf-8 -*-
"""
Dashboard IMSS – Plataformas Digitales (v5 con pestañas + totales + % por género + evolución)
Requiere:
- CSV: PD_jul.csv, PD_ago.csv, PD_sep.csv en la raíz.
- Imágenes en carpeta ./assets: repa.png, H-M.png
"""

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
import unicodedata

# ================== Paletas ==================
GUINDA = "#9d2148"
DORADO = "#b28e5c"
VERDE  = "#027a35"

# Bloque porcentajes/razones (tu paleta)
BLUE_DARK  = "#2F5761"
BLUE_LIGHT = "#628184"
BROWN_LIGHT = "#C17A5A"     # “marrón claro”
BEIGE      = "#FEF0C1"
WHITE      = "#FFFFFF"

FONT = dict(family="Montserrat", color="#333")
BG = "white"

# ================== Utilidades ==================
def norm_txt(s):
    if not isinstance(s, str): return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                if unicodedata.category(c) != 'Mn')
    return s.strip()

def fmt_num(x):
    try:
        return f"{int(round(x, 0)):,}".replace(",", " ")
    except Exception:
        return "0"

def pct(a, b):
    # porcentaje seguro (0 si b==0)
    return (float(a) / float(b) * 100.0) if float(b) != 0 else 0.0

def cargar_mes(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, encoding="utf-8-sig")
    df["Mes"] = etiqueta_mes
    df["entidad_display"] = df["entidad_nacimiento"].astype(str)
    df["entidad_norm"] = df["entidad_display"].apply(norm_txt)

    # Forzar numéricos y NaN->0
    for col in ["PTPD_Aseg_H","PTPD_Aseg_M","PTPD_Puestos_H","PTPD_Puestos_M",
                "PTPD_Aseg","PTPD_Puestos"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Independientes (H/M/Total)
    df["independientes_H"] = df["PTPD_Aseg_H"] - df["PTPD_Puestos_H"]
    df["independientes_M"] = df["PTPD_Aseg_M"] - df["PTPD_Puestos_M"]
    df["independientes"]   = df["independientes_H"] + df["independientes_M"]
    return df

def filtro_cdmx(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["entidad_norm"].str.contains("ciudad de mexico|cdmx|distrito federal", na=False)
    return df[mask].copy()

# ================== Bloques “Porcentajes y Razones” ==================
def bloque_totales(df: pd.DataFrame, df_cdmx: pd.DataFrame, app: dash.Dash, titulo: str) -> html.Div:
    # Nacional
    ben_n  = df["PTPD_Aseg"].sum()
    tdp_n  = df["PTPD_Puestos"].sum()
    ind_n  = df["independientes"].sum()

    # CDMX
    ben_c  = df_cdmx["PTPD_Aseg"].sum() if not df_cdmx.empty else 0
    tdp_c  = df_cdmx["PTPD_Puestos"].sum() if not df_cdmx.empty else 0
    ind_c  = df_cdmx["independientes"].sum() if not df_cdmx.empty else 0

    card_style = {
        "backgroundColor": BEIGE, "borderRadius": "18px",
        "padding": "16px 18px", "boxShadow": "0 6px 16px rgba(0,0,0,.08)"
    }
    label_style = {"fontSize": "18px", "color": BLUE_LIGHT, "margin": "4px 0"}
    value_style = {"fontSize": "30px", "fontWeight": "700", "color": BLUE_DARK}

    icon_repa = app.get_asset_url("repa.png")

    def columna(scope, ben, tdp, ind):
        return html.Div([
            html.H3(scope, style={"color": GUINDA, "marginTop": 0, "marginBottom": "8px"}),
            html.Div([html.Span("Beneficiados", style=label_style),
                      html.Div(fmt_num(ben), style=value_style)]),
            html.Div([html.Span("Trab. de plataformas (TDP)", style=label_style),
                      html.Div(fmt_num(tdp), style=value_style)]),
            html.Div([html.Span("Trab. independientes", style=label_style),
                      html.Div(fmt_num(ind), style=value_style)]),
        ], style={"width": "44%", "display": "inline-block", "verticalAlign": "top"})

    return html.Div([
        html.H2(titulo, style={"color": GUINDA}),
        html.Div([
            columna("Nacional", ben_n, tdp_n, ind_n),
            html.Div([html.Img(src=icon_repa, style={"height": "120px", "display": "block", "margin": "0 auto"})],
                     style={"width": "12%", "display": "inline-block", "textAlign": "center"}),
            columna("CDMX", ben_c, tdp_c, ind_c),
        ], style=card_style)
    ], style={"marginTop": "8px", "marginBottom": "16px"})

def bloque_genero(df: pd.DataFrame, df_cdmx: pd.DataFrame, app: dash.Dash, titulo: str) -> html.Div:
    # Nacional: %H y %M por categoría
    def perc_cat(h, m):
        tot = h + m
        return pct(h, tot), pct(m, tot)

    bh, bm = df["PTPD_Aseg_H"].sum(), df["PTPD_Aseg_M"].sum()
    th, tm = df["PTPD_Puestos_H"].sum(), df["PTPD_Puestos_M"].sum()
    ih, im = df["independientes_H"].sum(), df["independientes_M"].sum()

    bH, bM = perc_cat(bh, bm)
    tH, tM = perc_cat(th, tm)
    iH, iM = perc_cat(ih, im)

    # CDMX
    if not df_cdmx.empty:
        bhc, bmc = df_cdmx["PTPD_Aseg_H"].sum(), df_cdmx["PTPD_Aseg_M"].sum()
        thc, tmc = df_cdmx["PTPD_Puestos_H"].sum(), df_cdmx["PTPD_Puestos_M"].sum()
        ihc, imc = df_cdmx["independientes_H"].sum(), df_cdmx["independientes_M"].sum()
        bHc, bMc = perc_cat(bhc, bmc)
        tHc, tMc = perc_cat(thc, tmc)
        iHc, iMc = perc_cat(ihc, imc)
    else:
        bHc = bMc = tHc = tMc = iHc = iMc = 0.0

    card_style = {
        "backgroundColor": BLUE_DARK, "borderRadius": "18px",
        "padding": "18px 20px", "boxShadow": "0 6px 16px rgba(0,0,0,.08)", "color": WHITE
    }
    big = {"fontSize": "30px", "fontWeight": "800"}
    tag_h = {"color": WHITE, "backgroundColor": BLUE_LIGHT, "padding": "2px 8px",
             "borderRadius": "999px", "fontSize": "14px", "marginRight": "8px"}
    tag_m = {"color": WHITE, "backgroundColor": BROWN_LIGHT, "padding": "2px 8px",
             "borderRadius": "999px", "fontSize": "14px", "marginLeft": "8px"}

    icon_hm = app.get_asset_url("H-M.png")

    def panel(scope, Hvals, Mvals):
        (bH_, tH_, iH_) = Hvals
        (bM_, tM_, iM_) = Mvals
        return html.Div([
            html.H3(scope, style={"color": DORADO, "marginTop": 0}),
            html.Div([
                # Columna Hombres
                html.Div([
                    html.Div([html.Span("Hombres", style=tag_h)], style={"marginBottom": "6px"}),
                    html.Div([html.Div("Beneficiados", style={"fontSize": "16px"}),
                              html.Div(f"{bH_:.1f}%", style=big)]),
                    html.Div([html.Div("TDP", style={"fontSize": "16px", "marginTop": "8px"}),
                              html.Div(f'{tH_:.1f}%', style=big)]),
                    html.Div([html.Div("Independientes", style={"fontSize": "16px", "marginTop": "8px"}),
                              html.Div(f'{iH_:.1f}%', style=big)]),
                ], style={"width": "40%", "display": "inline-block", "verticalAlign": "top"}),

                # Icono
                html.Div([html.Img(src=icon_hm, style={"height": "120px", "display": "block", "margin": "0 auto"})],
                         style={"width": "20%", "display": "inline-block", "textAlign": "center"}),

                # Columna Mujeres
                html.Div([
                    html.Div([html.Span("Mujeres", style=tag_m)], style={"textAlign": "right", "marginBottom": "6px"}),
                    html.Div([html.Div("Beneficiadas", style={"fontSize": "16px", "textAlign": "right"}),
                              html.Div(f"{bM_:.1f}%", style={**big, "textAlign": "right"})]),
                    html.Div([html.Div("TDP", style={"fontSize": "16px", "textAlign": "right", "marginTop": "8px"}),
                              html.Div(f'{tM_:.1f}%', style={**big, "textAlign": "right"})]),
                    html.Div([html.Div("Independientes", style={"fontSize": "16px", "textAlign": "right", "marginTop": "8px"}),
                              html.Div(f'{iM_:.1f}%', style={**big, "textAlign": "right"})]),
                ], style={"width": "40%", "display": "inline-block", "verticalAlign": "top"})
            ])
        ], style=card_style)

    return html.Div([
        html.H2(titulo, style={"color": GUINDA, "marginTop": "12px"}),
        html.Div([
            html.Div(panel("Nacional",
                           (bH, tH, iH),
                           (bM, tM, iM)),
                    style={"width": "49%", "display": "inline-block", "verticalAlign": "top", "marginRight": "2%"}),
            html.Div(panel("CDMX",
                           (bHc, tHc, iHc),
                           (bMc, tMc, iMc)),
                    style={"width": "49%", "display": "inline-block", "verticalAlign": "top"})
        ])
    ], style={"marginBottom": "18px"})

# ================== Gráficas por mes ==================
def layout_mes(df: pd.DataFrame, mes_label: str, app: dash.Dash) -> html.Div:
    # 1) Personas beneficiadas por entidad
    ent = (df.groupby("entidad_display", as_index=False)["PTPD_Aseg"]
           .sum().sort_values("PTPD_Aseg", ascending=True))
    fig1 = px.bar(ent, x="PTPD_Aseg", y="entidad_display", orientation="h",
                  color_discrete_sequence=[GUINDA],
                  title=f"Total de personas beneficiadas por entidad ({mes_label})")
    fig1.update_traces(texttemplate="%{x:,.0f}", textposition="outside",
                       hovertemplate="<b>%{y}</b><br>Personas beneficiadas: %{x:,.0f}<extra></extra>")
    fig1.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Personas beneficiadas",
                       yaxis_title="", margin=dict(l=80, r=40, t=60, b=30))

    # 2) Beneficiadas vs TDP por entidad
    agg = (df.groupby("entidad_display", as_index=False)[["PTPD_Aseg","PTPD_Puestos"]]
           .sum().sort_values("PTPD_Aseg", ascending=True))
    fig2 = px.bar(agg, y="entidad_display", x=["PTPD_Aseg","PTPD_Puestos"],
                  orientation="h", barmode="group",
                  color_discrete_map={"PTPD_Aseg": GUINDA, "PTPD_Puestos": DORADO},
                  title=f"Personas beneficiadas vs Personas trabajadoras de plataformas (TDP) ({mes_label})")
    fig2.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>")
    fig2.for_each_trace(lambda t: t.update(
        name="Personas beneficiadas" if "Aseg" in t.name else "Personas trabajadoras de plataformas (TDP)"
    ))
    fig2.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Registros", yaxis_title="",
                       legend_title_text="Indicador", margin=dict(l=80, r=40, t=60, b=30))

    # 3) Pirámide nacional
    age_nat = (df.groupby("Rango_edad_2", as_index=False)[["PTPD_Aseg_H","PTPD_Aseg_M"]]
               .sum().sort_values("Rango_edad_2"))
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
        age_cdmx = (df_cdmx.groupby("Rango_edad_2", as_index=False)[["PTPD_Aseg_H","PTPD_Aseg_M"]]
                    .sum().sort_values("Rango_edad_2"))
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

    # === BLOQUES NUEVOS ===
    totales_div = bloque_totales(df, df_cdmx, app, "Totales (números absolutos)")
    genero_div  = bloque_genero(df, df_cdmx, app, "Estructura de género (% por categoría)")

    # Layout del tab
    return html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig1), style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig2), style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "float": "right"})
        ], style={"marginBottom": "18px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig3), style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig4), style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "float": "right"})
        ], style={"marginBottom": "18px"}),

        # BLOQUE 1: TOTALES
        totales_div,
        # BLOQUE 2: % POR GÉNERO
        genero_div
    ])

# ================== Evolución (series) ==================
def layout_evolucion(df_jul: pd.DataFrame, df_ago: pd.DataFrame, df_sep: pd.DataFrame) -> html.Div:
    df_all = pd.concat([df_jul, df_ago, df_sep], ignore_index=True)
    orden = ["Julio", "Agosto", "Septiembre"]
    df_all["Mes"] = pd.Categorical(df_all["Mes"], categories=orden, ordered=True)

    nat = (df_all.groupby("Mes", as_index=False)[
        ["PTPD_Aseg","PTPD_Puestos","independientes",
         "PTPD_Aseg_H","PTPD_Aseg_M",
         "PTPD_Puestos_H","PTPD_Puestos_M",
         "independientes_H","independientes_M"]
    ].sum())
    nat["tasa_formalizacion"] = (nat["PTPD_Puestos"] / nat["PTPD_Aseg"] * 100).round(2)

    cdmx = filtro_cdmx(df_all)
    cdmx_agg = (cdmx.groupby("Mes", as_index=False)[
        ["PTPD_Aseg","PTPD_Puestos","independientes",
         "PTPD_Aseg_H","PTPD_Aseg_M",
         "PTPD_Puestos_H","PTPD_Puestos_M",
         "independientes_H","independientes_M"]
    ].sum())
    cdmx_agg["tasa_formalizacion"] = (cdmx_agg["PTPD_Puestos"] / cdmx_agg["PTPD_Aseg"] * 100).round(2)

    def line_multi(df, cols, titulo, ytitle):
        df_long = df.melt(id_vars="Mes", value_vars=cols, var_name="Serie", value_name="Valor")
        ren = {"PTPD_Aseg":"Beneficiados","PTPD_Puestos":"TDP","independientes":"Independientes",
               "PTPD_Aseg_H":"Beneficiados H","PTPD_Aseg_M":"Beneficiados M",
               "PTPD_Puestos_H":"TDP H","PTPD_Puestos_M":"TDP M",
               "independientes_H":"Independientes H","independientes_M":"Independientes M"}
        df_long["Serie"] = df_long["Serie"].map(ren).fillna(df_long["Serie"])
        fig = px.line(df_long, x="Mes", y="Valor", color="Serie",
                      color_discrete_sequence=[GUINDA, DORADO, VERDE, "#5c1a2f", "#c0708f", "#806443", "#d7b58a", "#0c4f2b", "#5fb083"],
                      markers=True, title=titulo)
        fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:,.0f}<extra></extra>")
        fig.update_layout(plot_bgcolor=BG, font=FONT, yaxis_title=ytitle, xaxis_title="Mes")
        return fig

    def line_rate(df, colrate, titulo):
        fig = px.line(df, x="Mes", y=colrate, color_discrete_sequence=[GUINDA], markers=True, title=titulo)
        fig.update_traces(hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra></extra>")
        fig.update_layout(plot_bgcolor=BG, font=FONT, yaxis_title="Porcentaje", xaxis_title="Mes")
        return fig

    # Nacional
    fig_nat_tot = line_multi(nat, ["PTPD_Aseg","PTPD_Puestos","independientes"],
                             "Nacional: Beneficiados, TDP e Independientes", "Personas")
    fig_nat_rate = line_rate(nat, "tasa_formalizacion", "Nacional: Tasa de formalización (TDP/Beneficiados)")
    fig_nat_bene = line_multi(nat, ["PTPD_Aseg_H","PTPD_Aseg_M"], "Nacional: Beneficiados por género", "Personas")
    fig_nat_tdp  = line_multi(nat, ["PTPD_Puestos_H","PTPD_Puestos_M"], "Nacional: TDP por género", "Personas")
    fig_nat_ind  = line_multi(nat, ["independientes_H","independientes_M"], "Nacional: Independientes por género", "Personas")

    # CDMX
    fig_cdmx_tot = line_multi(cdmx_agg, ["PTPD_Aseg","PTPD_Puestos","independientes"],
                              "CDMX: Beneficiados, TDP e Independientes", "Personas")
    fig_cdmx_rate = line_rate(cdmx_agg, "tasa_formalizacion", "CDMX: Tasa de formalización (TDP/Beneficiados)")
    fig_cdmx_bene = line_multi(cdmx_agg, ["PTPD_Aseg_H","PTPD_Aseg_M"], "CDMX: Beneficiados por género", "Personas")
    fig_cdmx_tdp  = line_multi(cdmx_agg, ["PTPD_Puestos_H","PTPD_Puestos_M"], "CDMX: TDP por género", "Personas")
    fig_cdmx_ind  = line_multi(cdmx_agg, ["independientes_H","independientes_M"], "CDMX: Independientes por género", "Personas")

    return html.Div([
        html.H2("Evolución – Nacional", style={"color": GUINDA}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_tot),  style={"width": "48%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_rate), style={"width": "48%", "display": "inline-block", "float": "right"}),
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_bene), style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_tdp),  style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_ind),  style={"width": "32%", "display": "inline-block"}),
        ], style={"marginBottom": "26px"}),

        html.H2("Evolución – Ciudad de México", style={"color": GUINDA}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_tot),  style={"width": "48%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_rate), style={"width": "48%", "display": "inline-block", "float": "right"}),
        ], style={"marginBottom": "10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_bene), style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_tdp),  style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_ind),  style={"width": "32%", "display": "inline-block"}),
        ])
    ])

# ================== App y Tabs ==================
app = dash.Dash(__name__, title="IMSS Plataformas Digitales – v5")

# Carga de datos
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
        dcc.Tab(label="Julio", children=[layout_mes(df_jul, "Julio", app)]),
        dcc.Tab(label="Agosto", children=[layout_mes(df_ago, "Agosto", app)]),
        dcc.Tab(label="Septiembre", children=[layout_mes(df_sep, "Septiembre", app)]),
        dcc.Tab(label="Evolución", children=[layout_evolucion(df_jul, df_ago, df_sep)])
    ])
])

if __name__ == "__main__":
    # Para Render: 0.0.0.0 + puerto fijo
    app.run(host="0.0.0.0", port=10000, debug=False)
