# -*- coding: utf-8 -*-
"""
Dashboard IMSS – Plataformas Digitales (v6, ajustado)
Cambios principales:
- Barras de beneficiadas / TDP más grandes (se ven todos los estados).
- Proporción por sector: pie chart clásico (solo % en blanco dentro).
- Brecha salarial por sector: círculos con % en blanco por sector.
- Tablas de evolución:
    * Agregadas columnas de variación porcentual (Var. %).
- Tablas de salario base promedio y brecha: más angostas y centradas.
"""

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px
import unicodedata

# ======== Paletas ========
GUINDA = "#9d2148"
DORADO = "#b28e5c"
VERDE  = "#027a35"

# Paleta “porcentajes/razones”
BLUE_DARK   = "#2F5761"
BLUE_LIGHT  = "#628184"
BROWN_LIGHT = "#C17A5A"
BEIGE       = "#FEF0C1"
WHITE       = "#FFFFFF"

FONT = dict(family="Tahoma, sans-serif", color="#333")
BG   = "white"


# ======== Utilidades ========
def norm_txt(s):
    if not isinstance(s, str):
        return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                if unicodedata.category(c) != 'Mn')
    return s.strip()


def fmt_num(x):
    try:
        return f"{int(round(float(x), 0)):,}"
    except Exception:
        return "0"


def pct(a, b):
    a = float(a)
    b = float(b)
    return (a / b * 100.0) if b != 0 else 0.0


def filtro_cdmx(df: pd.DataFrame) -> pd.DataFrame:
    if "entidad_nacimiento" not in df.columns:
        return df.iloc[0:0].copy()
    ent_norm = df["entidad_nacimiento"].astype(str).apply(norm_txt)
    mask = ent_norm.str.contains("ciudad de mexico|cdmx|distrito federal", na=False)
    return df[mask].copy()


# ======== Carga de datos ========
def cargar_pd(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, encoding="utf-8-sig")
    df["Mes"] = etiqueta_mes
    df["entidad_display"] = df["entidad_nacimiento"].astype(str)
    df["entidad_norm"] = df["entidad_display"].apply(norm_txt)

    for col in ["PTPD_Aseg_H", "PTPD_Aseg_M",
                "PTPD_Puestos_H", "PTPD_Puestos_M",
                "PTPD_Aseg", "PTPD_Puestos"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["independientes_H"] = df["PTPD_Aseg_H"] - df["PTPD_Puestos_H"]
    df["independientes_M"] = df["PTPD_Aseg_M"] - df["PTPD_Puestos_M"]
    df["independientes"]   = df["independientes_H"] + df["independientes_M"]
    return df


def cargar_sbc(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, encoding="utf-8-sig")
    df["Mes"] = etiqueta_mes

    if "División" in df.columns:
        df["Sector"] = df["División"].astype(str)
    elif "CVE_DIVISION" in df.columns:
        df["Sector"] = df["CVE_DIVISION"].astype(str)
    else:
        df["Sector"] = "Sector"

    for c in ["SalarioFem", "SalarioMasc", "PTPD_Puestos"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    if "entidad_nacimiento" in df.columns:
        df["entidad_norm"] = df["entidad_nacimiento"].astype(str).apply(norm_txt)
    else:
        df["entidad_norm"] = ""

    if "Rango_edad_2" not in df.columns:
        df["Rango_edad_2"] = ""

    return df


# ===================== Bloque Totales =====================
def bloque_totales(df: pd.DataFrame, df_cdmx: pd.DataFrame,
                   app: dash.Dash, titulo: str) -> html.Div:
    ben_n = df["PTPD_Aseg"].sum()
    tdp_n = df["PTPD_Puestos"].sum()
    ind_n = df["independientes"].sum()

    ben_c = df_cdmx["PTPD_Aseg"].sum() if not df_cdmx.empty else 0
    tdp_c = df_cdmx["PTPD_Puestos"].sum() if not df_cdmx.empty else 0
    ind_c = df_cdmx["independientes"].sum() if not df_cdmx.empty else 0

    card_style = {
        "backgroundColor": BEIGE,
        "borderRadius": "18px",
        "padding": "16px 18px",
        "boxShadow": "0 6px 16px rgba(0,0,0,.08)"
    }
    label_style = {"fontSize": "18px", "color": BLUE_LIGHT, "margin": "4px 0"}
    value_style = {"fontSize": "30px", "fontWeight": "700", "color": BLUE_DARK}
    icon_repa = app.get_asset_url("repa.png")

    def columna(scope, ben, tdp, ind):
        return html.Div([
            html.H3(scope, style={"color": GUINDA, "marginTop": 0, "marginBottom": "8px"}),
            html.Div([
                html.Span("Beneficiados", style=label_style),
                html.Div(fmt_num(ben), style=value_style)
            ]),
            html.Div([
                html.Span("Trab. de plataformas (TDP)", style=label_style),
                html.Div(fmt_num(tdp), style=value_style)
            ]),
            html.Div([
                html.Span("Trab. independientes", style=label_style),
                html.Div(fmt_num(ind), style=value_style)
            ]),
        ], style={"width": "44%", "display": "inline-block", "verticalAlign": "top"})

    return html.Div([
        html.H2(titulo, style={"color": GUINDA}),
        html.Div([
            columna("Nacional", ben_n, tdp_n, ind_n),
            html.Div(
                [html.Img(src=icon_repa, style={
                    "height": "120px",
                    "display": "block",
                    "margin": "0 auto"
                })],
                style={"width": "12%", "display": "inline-block", "textAlign": "center"}
            ),
            columna("CDMX", ben_c, tdp_c, ind_c),
        ], style=card_style)
    ], style={"marginTop": "8px", "marginBottom": "16px"})


# ===================== Bloque Estructura de género =====================
def bloque_genero(df: pd.DataFrame, df_cdmx: pd.DataFrame,
                  app: dash.Dash, titulo: str) -> html.Div:

    def perc_cat(h, m):
        tot = h + m
        return pct(h, tot), pct(m, tot)

    # Nacional
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
        "backgroundColor": BLUE_DARK,
        "borderRadius": "18px",
        "padding": "18px 20px",
        "boxShadow": "0 6px 16px rgba(0,0,0,.08)",
        "color": WHITE
    }
    big = {"fontSize": "30px", "fontWeight": "800"}
    tag_h = {
        "color": WHITE,
        "backgroundColor": BLUE_LIGHT,
        "padding": "2px 8px",
        "borderRadius": "999px",
        "fontSize": "14px",
        "marginRight": "8px"
    }
    tag_m = {
        "color": WHITE,
        "backgroundColor": BROWN_LIGHT,
        "padding": "2px 8px",
        "borderRadius": "999px",
        "fontSize": "14px",
        "marginLeft": "8px"
    }
    icon_hm = app.get_asset_url("H-M.png")

    def panel(scope, Hvals, Mvals):
        (bH_, tH_, iH_) = Hvals
        (bM_, tM_, iM_) = Mvals
        return html.Div([
            html.H3(scope, style={"color": DORADO, "marginTop": 0}),
            html.Div([
                html.Div([
                    html.Div([html.Span("Hombres", style=tag_h)],
                             style={"marginBottom": "6px"}),
                    html.Div([
                        html.Div("Beneficiados", style={"fontSize": "16px"}),
                        html.Div(f"{bH_:.1f}%", style=big)
                    ]),
                    html.Div([
                        html.Div("TDP", style={"fontSize": "16px", "marginTop": "8px"}),
                        html.Div(f"{tH_:.1f}%", style=big)
                    ]),
                    html.Div([
                        html.Div("Independientes",
                                 style={"fontSize": "16px", "marginTop": "8px"}),
                        html.Div(f"{iH_:.1f}%", style=big)
                    ]),
                ], style={"width": "40%", "display": "inline-block", "verticalAlign": "top"}),

                html.Div([
                    html.Img(src=icon_hm, style={
                        "height": "120px",
                        "display": "block",
                        "margin": "0 auto"
                    })
                ], style={"width": "20%", "display": "inline-block", "textAlign": "center"}),

                html.Div([
                    html.Div([html.Span("Mujeres", style=tag_m)],
                             style={"textAlign": "right", "marginBottom": "6px"}),
                    html.Div([
                        html.Div("Beneficiadas",
                                 style={"fontSize": "16px", "textAlign": "right"}),
                        html.Div(f"{bM_:.1f}%", style={**big, "textAlign": "right"})
                    ]),
                    html.Div([
                        html.Div("TDP", style={
                            "fontSize": "16px",
                            "textAlign": "right",
                            "marginTop": "8px"
                        }),
                        html.Div(f"{tM_:.1f}%", style={**big, "textAlign": "right"})
                    ]),
                    html.Div([
                        html.Div("Independientes", style={
                            "fontSize": "16px",
                            "textAlign": "right",
                            "marginTop": "8px"
                        }),
                        html.Div(f"{iM_:.1f}%", style={**big, "textAlign": "right"})
                    ]),
                ], style={"width": "40%", "display": "inline-block", "verticalAlign": "top"}),
            ])
        ], style=card_style)

    return html.Div([
        html.H2(titulo, style={"color": GUINDA, "marginTop": "12px"}),
        html.Div([
            html.Div(
                panel("Nacional", (bH, tH, iH), (bM, tM, iM)),
                style={"width": "49%", "display": "inline-block",
                       "verticalAlign": "top", "marginRight": "2%"}
            ),
            html.Div(
                panel("CDMX", (bHc, tHc, iHc), (bMc, tMc, iMc)),
                style={"width": "49%", "display": "inline-block",
                       "verticalAlign": "top"}
            )
        ])
    ], style={"marginBottom": "18px"})


def bloque_sectores(df_sbc: pd.DataFrame, titulo: str) -> html.Div:
    """Bloque de sectores para un ámbito (nacional o CDMX)"""

    # === Colores fijos por sector ===
    COLOR_SECTOR = {
        "Transportes y comunicaciones": BLUE_DARK,
        "Servicios para empresas": BROWN_LIGHT
    }

    # ================================================================
    # 1) Proporción por sector (TDP) -> PIE
    # ================================================================
    prop = (df_sbc.groupby("Sector", as_index=False)["PTPD_Puestos"].sum())
    total_tdp = prop["PTPD_Puestos"].sum()
    if total_tdp == 0:
        prop["Proporcion"] = 0.0
    else:
        prop["Proporcion"] = prop["PTPD_Puestos"] / total_tdp * 100

    # Ordenar para asegurar consistencia de color
    prop["Sector"] = pd.Categorical(
        prop["Sector"],
        categories=["Transportes y comunicaciones", "Servicios para empresas"],
        ordered=True
    )

    fig_prop = px.pie(
        prop,
        names="Sector",
        values="PTPD_Puestos",
        title="Proporción de personas trabajadoras de plataformas por sector",
        hole=0
    )
    fig_prop.update_traces(
        textinfo="percent",
        textfont=dict(color=WHITE),
        hovertemplate="<b>%{label}</b><br>Proporción: %{percent}<extra></extra>",
        marker=dict(colors=[COLOR_SECTOR.get(s, "#ccc") for s in prop["Sector"]])
    )
    fig_prop.update_layout(
        plot_bgcolor=BG,
        font=FONT,
        legend_title_text="Sector"
    )

    # ================================================================
    # 2) Salario promedio por género por sector
    # ================================================================
    sal = (df_sbc.groupby("Sector", as_index=False)[["SalarioFem", "SalarioMasc"]]
           .mean().fillna(0))
    sal_long = sal.melt(
        id_vars="Sector",
        value_vars=["SalarioFem", "SalarioMasc"],
        var_name="Genero",
        value_name="Salario"
    )
    sal_long["Genero"] = sal_long["Genero"].map({
        "SalarioFem": "Mujeres",
        "SalarioMasc": "Hombres"
    })

    fig_sal = px.bar(
        sal_long,
        y="Sector",
        x="Salario",
        color="Genero",
        orientation="h",
        barmode="group",
        color_discrete_map={
            "Mujeres": BROWN_LIGHT,
            "Hombres": BLUE_DARK
        },
        title="Salario base de cotización promedio por sexo (por sector)"
    )
    fig_sal.update_traces(
        hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.2f}<extra></extra>"
    )
    fig_sal.update_layout(
        plot_bgcolor=BG,
        font=FONT,
        xaxis_title="Salario promedio",
        yaxis_title="",
        legend_title_text="Género"
    )

    # ================================================================
    # 3) Pirámide salarial por edad
    # ================================================================
    pir = (df_sbc.groupby("Rango_edad_2", as_index=False)[
        ["SalarioMasc", "SalarioFem"]
    ].mean().fillna(0))
    pir = pir.sort_values("Rango_edad_2")
    pir["Sal_H_neg"] = -pir["SalarioMasc"].abs()

    fig_pir = px.bar(
        pir,
        x="Sal_H_neg",
        y="Rango_edad_2",
        orientation="h",
        color_discrete_sequence=[BLUE_DARK],
        title="Pirámide salarial por edad (salario promedio)"
    )
    fig_pir.add_bar(
        x=pir["SalarioFem"],
        y=pir["Rango_edad_2"],
        orientation="h",
        marker_color=BROWN_LIGHT,
        name="Mujeres",
        hovertemplate="<b>Mujeres</b> – salario: %{x:,.2f}<br>Edad: %{y}<extra></extra>"
    )
    fig_pir.add_bar(
        x=pir["Sal_H_neg"],
        y=pir["Rango_edad_2"],
        orientation="h",
        marker_color=BLUE_DARK,
        name="Hombres",
        hovertemplate="<b>Hombres</b> – salario: %{customdata:,.2f}<br>Edad: %{y}<extra></extra>",
        customdata=pir["SalarioMasc"]
    )
    fig_pir.update_layout(
        barmode="overlay",
        plot_bgcolor=BG,
        font=FONT,
        xaxis_title="Salario promedio (H izq / M der)",
        yaxis_title="Edad"
    )

    # ================================================================
    # 4) Resumen de salarios y brecha promedio
    # ================================================================
    prom_m = sal["SalarioMasc"].mean()
    prom_f = sal["SalarioFem"].mean()
    brecha_prom = ((prom_m - prom_f) / prom_m * 100) if prom_m else 0
    n_sect = prop["Sector"].nunique()

    card_style = {
        "backgroundColor": BEIGE,
        "borderRadius": "14px",
        "padding": "12px 14px",
        "boxShadow": "0 6px 16px rgba(0,0,0,.06)",
        "marginBottom": "10px"
    }

    resumen = html.Div([
        html.Div([
            html.Div([
                html.Div("Sectores", style={"color": BLUE_LIGHT}),
                html.Div(fmt_num(n_sect), style={
                    "fontSize": "24px",
                    "fontWeight": "800",
                    "color": BLUE_DARK
                })
            ], style={"display": "inline-block", "width": "25%"}),

            html.Div([
                html.Div("Salario H (prom.)", style={"color": BLUE_LIGHT}),
                html.Div(f"{prom_m:,.2f}", style={
                    "fontSize": "24px",
                    "fontWeight": "800",
                    "color": BLUE_DARK
                })
            ], style={"display": "inline-block", "width": "25%"}),

            html.Div([
                html.Div("Salario M (prom.)", style={"color": BLUE_LIGHT}),
                html.Div(f"{prom_f:,.2f}", style={
                    "fontSize": "24px",
                    "fontWeight": "800",
                    "color": BLUE_DARK
                })
            ], style={"display": "inline-block", "width": "25%"}),

            html.Div([
                html.Div("Brecha salarial prom. entre hombres y mujeres (%)",
                         style={"color": BLUE_LIGHT, "marginBottom": "4px"}),
                html.Div(f"{brecha_prom:.1f}%", style={
                    "fontSize": "24px",
                    "fontWeight": "800",
                    "color": BLUE_DARK
                })
            ], style={"display": "inline-block", "width": "25%"}),
        ])
    ], style=card_style)

    # ================================================================
    # 5) Brecha salarial por sector (círculos)
    # ================================================================
    brecha = sal.copy()
    brecha["Brecha (%)"] = ((brecha["SalarioMasc"] - brecha["SalarioFem"]) /
                            brecha["SalarioMasc"].replace(0, pd.NA) * 100).fillna(0)

    circle_base = {
        "width": "100px",
        "height": "100px",
        "borderRadius": "50%",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "color": WHITE,
        "fontSize": "22px",
        "fontWeight": "800",
        "margin": "0 auto"
    }

    brecha_circulos = []
    for _, row in brecha.iterrows():
        color = COLOR_SECTOR.get(row["Sector"], BLUE_DARK)
        style_circle = dict(circle_base)
        style_circle["backgroundColor"] = color
        brecha_circulos.append(
            html.Div([
                html.Div(row["Sector"], style={
                    "fontSize": "14px",
                    "marginBottom": "6px",
                    "color": "#333",
                    "textAlign": "center"
                }),
                html.Div(f"{row['Brecha (%)']:.1f}%", style=style_circle)
            ], style={"display": "inline-block", "margin": "8px 16px"})
        )

    brecha_div = html.Div([
        html.H4("Brecha salarial entre hombres y mujeres por sector",
                style={"color": GUINDA, "marginTop": "12px",
                       "textAlign": "center", "fontWeight": "700"}),
        html.Div(brecha_circulos, style={"textAlign": "center"})
    ])

    # ================================================================
    # 6) Ensamble final
    # ================================================================
    return html.Div([
        html.H3(titulo, style={"color": GUINDA}),
        resumen,
        html.Div([
            html.Div(dcc.Graph(figure=fig_prop),
                     style={"width": "49%", "display": "inline-block",
                            "verticalAlign": "top", "marginRight": "2%"}),
            html.Div(dcc.Graph(figure=fig_sal),
                     style={"width": "49%", "display": "inline-block",
                            "verticalAlign": "top"})
        ], style={"marginTop": "10px"}),
        brecha_div,
        html.Div([
            html.Div(dcc.Graph(figure=fig_pir),
                     style={"width": "60%", "margin": "0 auto"})
        ], style={"marginTop": "10px", "marginBottom": "18px"})
    ], style={"marginTop": "14px", "marginBottom": "22px"})

def bloque_sectores_nal_cdmx(df_sbc: pd.DataFrame) -> html.Div:
    df_cdmx = df_sbc[df_sbc["entidad_norm"].astype(str)
                    .str.contains("ciudad de mexico|cdmx|distrito federal",
                                  na=False)].copy()
    panel_n = bloque_sectores(df_sbc, "Sectores – Nacional")
    panel_c = bloque_sectores(df_cdmx, "Sectores – CDMX") if not df_cdmx.empty else html.Div()
    return html.Div([panel_n, panel_c])


# ===================== Gráficas por mes =====================
def layout_mes(df: pd.DataFrame, df_sbc: pd.DataFrame,
               mes_label: str, app: dash.Dash) -> html.Div:
    # 1) Beneficiadas por entidad (barras más altas)
    ent = (df.groupby("entidad_display", as_index=False)["PTPD_Aseg"]
           .sum().sort_values("PTPD_Aseg", ascending=True))
    fig1 = px.bar(
        ent,
        x="PTPD_Aseg",
        y="entidad_display",
        orientation="h",
        color_discrete_sequence=[GUINDA],
        title=f"Total de personas beneficiadas por entidad ({mes_label})",
        height=800
    )
    fig1.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Personas beneficiadas: %{x:,.0f}<extra></extra>"
    )
    fig1.update_layout(
        plot_bgcolor=BG,
        font=FONT,
        xaxis_title="Personas beneficiadas",
        yaxis_title="",
        margin=dict(l=80, r=40, t=60, b=30)
    )

    # 2) Beneficiadas vs TDP (barras altas)
    agg = (df.groupby("entidad_display", as_index=False)[["PTPD_Aseg", "PTPD_Puestos"]]
           .sum().sort_values("PTPD_Aseg", ascending=True))
    fig2 = px.bar(
        agg,
        y="entidad_display",
        x=["PTPD_Aseg", "PTPD_Puestos"],
        orientation="h",
        barmode="group",
        color_discrete_map={"PTPD_Aseg": GUINDA, "PTPD_Puestos": DORADO},
        title=f"Personas beneficiadas vs Personas trabajadoras de plataformas (TDP) ({mes_label})",
        height=800
    )
    fig2.update_traces(
        hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>"
    )
    fig2.for_each_trace(lambda t: t.update(
        name="Personas beneficiadas" if "Aseg" in t.name
        else "Personas trabajadoras de plataformas (TDP)"
    ))
    fig2.update_layout(
        plot_bgcolor=BG,
        font=FONT,
        xaxis_title="Registros",
        yaxis_title="",
        legend_title_text="Indicador",
        margin=dict(l=80, r=40, t=60, b=30)
    )

    # 3) Pirámide nacional (beneficiadas)
    age_nat = (df.groupby("Rango_edad_2", as_index=False)[
        ["PTPD_Aseg_H", "PTPD_Aseg_M"]
    ].sum().sort_values("Rango_edad_2"))
    men_nat_abs = age_nat["PTPD_Aseg_H"].abs()
    age_nat["PTPD_Aseg_H_neg"] = -men_nat_abs

    fig3 = px.bar(
        age_nat,
        x="PTPD_Aseg_H_neg",
        y="Rango_edad_2",
        orientation="h",
        color_discrete_sequence=[VERDE],
        title=f"Pirámide poblacional de personas beneficiadas – Nacional ({mes_label})"
    )
    fig3.add_bar(
        x=age_nat["PTPD_Aseg_M"],
        y=age_nat["Rango_edad_2"],
        orientation="h",
        marker_color=GUINDA,
        name="Mujeres",
        hovertemplate="<b>Mujeres beneficiadas</b>: %{x:,.0f}<br>Edad: %{y}<extra></extra>"
    )
    fig3.add_bar(
        x=age_nat["PTPD_Aseg_H_neg"],
        y=age_nat["Rango_edad_2"],
        orientation="h",
        marker_color=VERDE,
        name="Hombres",
        hovertemplate="<b>Hombres beneficiados</b>: %{customdata:,.0f}<br>Edad: %{y}<extra></extra>",
        customdata=men_nat_abs
    )
    fig3.update_layout(
        barmode="overlay",
        plot_bgcolor=BG,
        font=FONT,
        xaxis_title="Personas",
        yaxis_title="Edad"
    )

    # 4) Pirámide CDMX
    df_cdmx = filtro_cdmx(df)
    if not df_cdmx.empty:
        age_cdmx = (df_cdmx.groupby("Rango_edad_2", as_index=False)[
            ["PTPD_Aseg_H", "PTPD_Aseg_M"]
        ].sum().sort_values("Rango_edad_2"))
        men_cdmx_abs = age_cdmx["PTPD_Aseg_H"].abs()
        age_cdmx["PTPD_Aseg_H_neg"] = -men_cdmx_abs

        fig4 = px.bar(
            age_cdmx,
            x="PTPD_Aseg_H_neg",
            y="Rango_edad_2",
            orientation="h",
            color_discrete_sequence=[VERDE],
            title=f"Pirámide poblacional de personas beneficiadas – CDMX ({mes_label})"
        )
        fig4.add_bar(
            x=age_cdmx["PTPD_Aseg_M"],
            y=age_cdmx["Rango_edad_2"],
            orientation="h",
            marker_color=GUINDA,
            name="Mujeres",
            hovertemplate="<b>Mujeres beneficiadas</b>: %{x:,.0f}<br>Edad: %{y}<extra></extra>"
        )
        fig4.add_bar(
            x=age_cdmx["PTPD_Aseg_H_neg"],
            y=age_cdmx["Rango_edad_2"],
            orientation="h",
            marker_color=VERDE,
            name="Hombres",
            hovertemplate="<b>Hombres beneficiados</b>: %{customdata:,.0f}<br>Edad: %{y}<extra></extra>",
            customdata=men_cdmx_abs
        )
        fig4.update_layout(
            barmode="overlay",
            plot_bgcolor=BG,
            font=FONT,
            xaxis_title="Personas",
            yaxis_title="Edad"
        )
    else:
        fig4 = px.bar(
            title=f"Pirámide poblacional CDMX ({mes_label}) – sin registros"
        )
        fig4.update_layout(plot_bgcolor=BG, font=FONT)

    totales_div = bloque_totales(df, df_cdmx, app, "Totales (números absolutos)")
    genero_div  = bloque_genero(df, df_cdmx, app, "Estructura por sexo (% por categoría)")
    sectores_div = bloque_sectores_nal_cdmx(df_sbc)

    return html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig1),
                     style={"width": "48%", "display": "inline-block",
                            "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig2),
                     style={"width": "48%", "display": "inline-block",
                            "verticalAlign": "top", "float": "right"})
        ], style={"marginBottom": "18px"}),

        html.Div([
            html.Div(dcc.Graph(figure=fig3),
                     style={"width": "48%", "display": "inline-block",
                            "verticalAlign": "top"}),
            html.Div(dcc.Graph(figure=fig4),
                     style={"width": "48%", "display": "inline-block",
                            "verticalAlign": "top", "float": "right"})
        ], style={"marginBottom": "18px"}),

        totales_div,
        genero_div,

        html.H2("Sectores", style={"color": GUINDA}),
        sectores_div
    ])


# ===================== Tablas para Evolución =====================
def tabla_html(df: pd.DataFrame, titulo: str) -> html.Div:
    th_style = {
        "backgroundColor": GUINDA,
        "color": "white",
        "padding": "6px 10px",
        "border": "1px solid #cccccc",
        "fontWeight": "600",
        "fontSize": "13px",
        "textAlign": "center"
    }
    td_style = {
        "padding": "4px 8px",
        "border": "1px solid #dddddd",
        "fontSize": "13px",
        "backgroundColor": "white"
    }
    table_style = {
        "borderCollapse": "collapse",
        "width": "100%",
        "marginTop": "6px",
        "marginBottom": "12px"
    }

    header = html.Tr([html.Th(col, style=th_style) for col in df.columns])
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for col, val in row.items():
            is_num = False
            if isinstance(val, (int, float)):
                is_num = True
            else:
                try:
                    float(str(val).replace(" ", "").replace(",", ""))
                    is_num = True
                except Exception:
                    is_num = False

            style = dict(td_style)
            style["textAlign"] = "right" if is_num else "left"
            cells.append(html.Td(str(val), style=style))
        body_rows.append(html.Tr(cells))

    return html.Div([
        html.H3(titulo, style={"color": GUINDA, "marginTop": "10px"}),
        html.Table([
            html.Thead(header),
            html.Tbody(body_rows)
        ], style=table_style)
    ])


def tabla_html_narrow(df: pd.DataFrame, titulo: str) -> html.Div:
    """Versión más angosta y centrada (para salario y brecha)."""
    th_style = {
        "backgroundColor": GUINDA,
        "color": "white",
        "padding": "6px 10px",
        "border": "1px solid #cccccc",
        "fontWeight": "600",
        "fontSize": "13px",
        "textAlign": "center"
    }
    td_style = {
        "padding": "4px 8px",
        "border": "1px solid #dddddd",
        "fontSize": "13px",
        "backgroundColor": "white"
    }
    table_style = {
        "borderCollapse": "collapse",
        "width": "60%",
        "marginTop": "6px",
        "marginBottom": "12px",
        "marginLeft": "auto",
        "marginRight": "auto"
    }

    header = html.Tr([html.Th(col, style=th_style) for col in df.columns])
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for col, val in row.items():
            is_num = False
            if isinstance(val, (int, float)):
                is_num = True
            else:
                try:
                    float(str(val).replace(" ", "").replace(",", ""))
                    is_num = True
                except Exception:
                    is_num = False

            style = dict(td_style)
            style["textAlign"] = "right" if is_num else "left"
            cells.append(html.Td(str(val), style=style))
        body_rows.append(html.Tr(cells))

    return html.Div([
        html.H3(titulo, style={"color": GUINDA, "marginTop": "10px", "textAlign": "center"}),
        html.Table([
            html.Thead(header),
            html.Tbody(body_rows)
        ], style=table_style)
    ])


# ===================== Evolución =====================
def layout_evolucion(df_jul: pd.DataFrame, df_ago: pd.DataFrame, df_sep: pd.DataFrame,
                     sbc_jul: pd.DataFrame, sbc_ago: pd.DataFrame, sbc_sep: pd.DataFrame) -> html.Div:
    df_all = pd.concat([df_jul, df_ago, df_sep], ignore_index=True)
    orden = ["Julio", "Agosto", "Septiembre"]
    df_all["Mes"] = pd.Categorical(df_all["Mes"], categories=orden, ordered=True)

    nat = (df_all.groupby("Mes", as_index=False)[[
        "PTPD_Aseg", "PTPD_Puestos", "independientes",
        "PTPD_Aseg_H", "PTPD_Aseg_M",
        "PTPD_Puestos_H", "PTPD_Puestos_M",
        "independientes_H", "independientes_M"
    ]].sum())
    nat["tasa_formalizacion"] = (nat["PTPD_Puestos"] / nat["PTPD_Aseg"] * 100).round(2)

    cdmx_all = filtro_cdmx(df_all)
    cdmx_agg = (cdmx_all.groupby("Mes", as_index=False)[[
        "PTPD_Aseg", "PTPD_Puestos", "independientes",
        "PTPD_Aseg_H", "PTPD_Aseg_M",
        "PTPD_Puestos_H", "PTPD_Puestos_M",
        "independientes_H", "independientes_M"
    ]].sum())
    cdmx_agg["tasa_formalizacion"] = (cdmx_agg["PTPD_Puestos"] /
                                      cdmx_agg["PTPD_Aseg"] * 100).round(2)

    # ---- Gráficas líneas ----
    def line_multi(df, cols, titulo, ytitle):
        df_long = df.melt(id_vars="Mes", value_vars=cols,
                          var_name="Serie", value_name="Valor")
        ren = {
            "PTPD_Aseg": "Beneficiados",
            "PTPD_Puestos": "TDP",
            "independientes": "Independientes",
            "PTPD_Aseg_H": "Beneficiados H",
            "PTPD_Aseg_M": "Beneficiados M",
            "PTPD_Puestos_H": "TDP H",
            "PTPD_Puestos_M": "TDP M",
            "independientes_H": "Independientes H",
            "independientes_M": "Independientes M"
        }
        df_long["Serie"] = df_long["Serie"].map(ren).fillna(df_long["Serie"])
        fig = px.line(
            df_long, x="Mes", y="Valor", color="Serie",
            color_discrete_sequence=[
                GUINDA, DORADO, VERDE,
                "#5c1a2f", "#c0708f",
                "#806443", "#d7b58a",
                "#0c4f2b", "#5fb083"
            ],
            markers=True,
            title=titulo
        )
        fig.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:,.0f}<extra></extra>"
        )
        fig.update_layout(
            plot_bgcolor=BG,
            font=FONT,
            yaxis_title=ytitle,
            xaxis_title="Mes"
        )
        return fig

    def line_rate(df, colrate, titulo):
        fig = px.line(
            df, x="Mes", y=colrate,
            color_discrete_sequence=[GUINDA],
            markers=True,
            title=titulo
        )
        fig.update_traces(
            hovertemplate="<b>%{x}</b>: %{y:.2f}%<extra></extra>"
        )
        fig.update_layout(
            plot_bgcolor=BG,
            font=FONT,
            yaxis_title="Porcentaje",
            xaxis_title="Mes"
        )
        return fig

    fig_nat_tot = line_multi(
        nat, ["PTPD_Aseg", "PTPD_Puestos", "independientes"],
        "Nacional: Beneficiados, TDP e Independientes", "Personas"
    )
    fig_nat_rate = line_rate(
        nat, "tasa_formalizacion",
        "Nacional: Tasa de formalización (TDP/Beneficiados)"
    )
    fig_nat_bene = line_multi(
        nat, ["PTPD_Aseg_H", "PTPD_Aseg_M"],
        "Nacional: Beneficiados por género", "Personas"
    )
    fig_nat_tdp = line_multi(
        nat, ["PTPD_Puestos_H", "PTPD_Puestos_M"],
        "Nacional: TDP por género", "Personas"
    )
    fig_nat_ind = line_multi(
        nat, ["independientes_H", "independientes_M"],
        "Nacional: Independientes por género", "Personas"
    )

    fig_cdmx_tot = line_multi(
        cdmx_agg, ["PTPD_Aseg", "PTPD_Puestos", "independientes"],
        "CDMX: Beneficiados, TDP e Independientes", "Personas"
    )
    fig_cdmx_rate = line_rate(
        cdmx_agg, "tasa_formalizacion",
        "CDMX: Tasa de formalización (TDP/Beneficiados)"
    )
    fig_cdmx_bene = line_multi(
        cdmx_agg, ["PTPD_Aseg_H", "PTPD_Aseg_M"],
        "CDMX: Beneficiados por género", "Personas"
    )
    fig_cdmx_tdp = line_multi(
        cdmx_agg, ["PTPD_Puestos_H", "PTPD_Puestos_M"],
        "CDMX: TDP por género", "Personas"
    )
    fig_cdmx_ind = line_multi(
        cdmx_agg, ["independientes_H", "independientes_M"],
        "CDMX: Independientes por género", "Personas"
    )

    # ========= Tablas de evolución =========
    periodo_map = {
        "Julio": "jul-25",
        "Agosto": "ago-25",
        "Septiembre": "sep-25"
    }

    nat_tab = nat.copy()
    nat_tab["Periodo"] = nat_tab["Mes"].map(periodo_map)
    nat_tab["Var_ben"] = nat_tab["PTPD_Aseg"].diff()
    nat_tab["Var_tdp"] = nat_tab["PTPD_Puestos"].diff()
    nat_tab["Var_pct_ben"] = nat_tab["PTPD_Aseg"].pct_change() * 100
    nat_tab["Var_pct_tdp"] = nat_tab["PTPD_Puestos"].pct_change() * 100

    def fmt_diff(x):
        if pd.isna(x):
            return "-"
        return f"{x:+,.0f}"

    def fmt_diff_pct(x):
        if pd.isna(x):
            return "-"
        return f"{x:+.1f}%"

    tabla_nat = pd.DataFrame({
        "Periodo": nat_tab["Periodo"],
        "Personas beneficiadas": nat_tab["PTPD_Aseg"].map(fmt_num),
        "Var. abs. beneficiadas": nat_tab["Var_ben"].map(fmt_diff),
        "Var. % beneficiadas": nat_tab["Var_pct_ben"].map(fmt_diff_pct),
        "Personas TDP": nat_tab["PTPD_Puestos"].map(fmt_num),
        "Var. abs. TDP": nat_tab["Var_tdp"].map(fmt_diff),
        "Var. % TDP": nat_tab["Var_pct_tdp"].map(fmt_diff_pct),
        "Tasa de formalización laboral (%)": nat_tab["tasa_formalizacion"].map(
            lambda x: f"{x:.2f}"
        )
    })

    cdmx_tab = cdmx_agg.copy()
    cdmx_tab["Periodo"] = cdmx_tab["Mes"].map(periodo_map)
    cdmx_tab["Var_ben"] = cdmx_tab["PTPD_Aseg"].diff()
    cdmx_tab["Var_tdp"] = cdmx_tab["PTPD_Puestos"].diff()
    cdmx_tab["Var_pct_ben"] = cdmx_tab["PTPD_Aseg"].pct_change() * 100
    cdmx_tab["Var_pct_tdp"] = cdmx_tab["PTPD_Puestos"].pct_change() * 100

    tabla_cdmx = pd.DataFrame({
        "Periodo": cdmx_tab["Periodo"],
        "Personas beneficiadas": cdmx_tab["PTPD_Aseg"].map(fmt_num),
        "Var. abs. beneficiadas": cdmx_tab["Var_ben"].map(fmt_diff),
        "Var. % beneficiadas": cdmx_tab["Var_pct_ben"].map(fmt_diff_pct),
        "Personas TDP": cdmx_tab["PTPD_Puestos"].map(fmt_num),
        "Var. abs. TDP": cdmx_tab["Var_tdp"].map(fmt_diff),
        "Var. % TDP": cdmx_tab["Var_pct_tdp"].map(fmt_diff_pct),
        "Tasa de formalización laboral (%)": cdmx_tab["tasa_formalizacion"].map(
            lambda x: f"{x:.2f}"
        )
    })

    # ---- Salarios y brecha promedio (Nacional / CDMX) ----
    def resumen_salario(df_sbc_list, mes_labels):
        rows = []
        for df_sbc, mes in zip(df_sbc_list, mes_labels):
            prom_m = df_sbc["SalarioMasc"].mean()
            prom_f = df_sbc["SalarioFem"].mean()
            brecha = ((prom_m - prom_f) / prom_m * 100) if prom_m else 0
            rows.append({
                "Mes": mes,
                "SalarioMasc": prom_m,
                "SalarioFem": prom_f,
                "Brecha": brecha
            })
        return pd.DataFrame(rows)

    sal_nat_raw = resumen_salario(
        [sbc_jul, sbc_ago, sbc_sep],
        ["Julio", "Agosto", "Septiembre"]
    )
    sal_nat_raw["Periodo"] = sal_nat_raw["Mes"].map(periodo_map)

    tabla_sal_nat = pd.DataFrame({
        "Periodo": sal_nat_raw["Periodo"],
        "Salario base de cotización promedio": sal_nat_raw["SalarioMasc"].map(
            lambda x: f"{x:,.2f}"
        ),
        "Brecha salarial promedio entre hombres y mujeres (%)": sal_nat_raw["Brecha"].map(
            lambda x: f"{x:.2f}"
        )
    })

    def filtra_cdmx_sbc(df_sbc):
        return df_sbc[df_sbc["entidad_norm"].astype(str)
                     .str.contains("ciudad de mexico|cdmx|distrito federal",
                                   na=False)].copy()

    sal_cdmx_raw = resumen_salario(
        [filtra_cdmx_sbc(sbc_jul),
         filtra_cdmx_sbc(sbc_ago),
         filtra_cdmx_sbc(sbc_sep)],
        ["Julio", "Agosto", "Septiembre"]
    )
    sal_cdmx_raw["Periodo"] = sal_cdmx_raw["Mes"].map(periodo_map)

    tabla_sal_cdmx = pd.DataFrame({
        "Periodo": sal_cdmx_raw["Periodo"],
        "Salario base de cotización promedio": sal_cdmx_raw["SalarioMasc"].map(
            lambda x: f"{x:,.2f}"
        ),
        "Brecha salarial promedio entre hombres y mujeres (%)": sal_cdmx_raw["Brecha"].map(
            lambda x: f"{x:.2f}"
        )
    })

    # ---- Construcción del layout ----
    return html.Div([
        html.H2("Evolución – Nacional", style={"color": GUINDA}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_tot),
                     style={"width": "48%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_rate),
                     style={"width": "48%", "display": "inline-block",
                            "float": "right"}),
        ], style={"marginBottom": "10px"}),

        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_bene),
                     style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_tdp),
                     style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_ind),
                     style={"width": "32%", "display": "inline-block"}),
        ], style={"marginBottom": "20px"}),

        tabla_html(tabla_nat, "Tabla nacional – Beneficiados, TDP y tasa de formalización"),
        tabla_html_narrow(tabla_sal_nat,
                          "Tabla nacional – Evolución de salario base y brecha salarial entre hombres y mujeres"),

        html.H2("Evolución – Ciudad de México", style={"color": GUINDA, "marginTop": "18px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_tot),
                     style={"width": "48%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_rate),
                     style={"width": "48%", "display": "inline-block",
                            "float": "right"}),
        ], style={"marginBottom": "10px"}),

        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_bene),
                     style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_tdp),
                     style={"width": "32%", "display": "inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_ind),
                     style={"width": "32%", "display": "inline-block"}),
        ], style={"marginBottom": "20px"}),

        tabla_html(tabla_cdmx, "Tabla CDMX – Beneficiados, TDP y tasa de formalización"),
        tabla_html_narrow(tabla_sal_cdmx,
                          "Tabla CDMX – Evolución de salario base y brecha salarial entre hombres y mujeres")
    ])


# ===================== Construcción de la app =====================
app = dash.Dash(__name__, title="IMSS Plataformas Digitales – v6")

# Carga de bases PD
df_jul = cargar_pd("PD_jul.csv", "Julio")
df_ago = cargar_pd("PD_ago.csv", "Agosto")
df_sep = cargar_pd("PD_sep.csv", "Septiembre")

# Carga de bases SBC (salarios/división)
sbc_jul = cargar_sbc("sbc_jul.csv", "Julio")
sbc_ago = cargar_sbc("sbc_ago.csv", "Agosto")
sbc_sep = cargar_sbc("sbc_sep.csv", "Septiembre")

app.layout = html.Div(style={
    "fontFamily": "Tahoma, sans-serif",
    "backgroundColor": "#ffffff",
    "padding": "12px"
}, children=[

    html.H1("Dashboard IMSS – Plataformas Digitales",
            style={"color": GUINDA, "textAlign": "center",
                   "marginBottom": "12px"}),

    dcc.Tabs([
        dcc.Tab(label="Julio",
                children=[layout_mes(df_jul, sbc_jul, "Julio", app)]),
        dcc.Tab(label="Agosto",
                children=[layout_mes(df_ago, sbc_ago, "Agosto", app)]),
        dcc.Tab(label="Septiembre",
                children=[layout_mes(df_sep, sbc_sep, "Septiembre", app)]),
        dcc.Tab(label="Evolución",
                children=[layout_evolucion(df_jul, df_ago, df_sep,
                                           sbc_jul, sbc_ago, sbc_sep)])
    ])
])


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)


