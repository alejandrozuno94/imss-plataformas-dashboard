# -*- coding: utf-8 -*-
"""
Dashboard IMSS – Plataformas Digitales (v5.2)
Novedad: Bloque “Sectores” por mes (Proporción TDP por sector + Estructura salarial:
- Salario promedio por género (por sector)
- Brecha salarial (%)
- Pirámide salarial por edad (H izq / M der)

Requisitos:
- CSV base: PD_jul.csv, PD_ago.csv, PD_sep.csv
- CSV salario/división: sbc_jul.csv, sbc_ago.csv, sbc_sep.csv
- Imágenes en ./assets: repa.png, H-M.png
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

# Paleta “porcentajes/razones” que nos diste
BLUE_DARK  = "#2F5761"
BLUE_LIGHT = "#628184"
BROWN_LIGHT = "#C17A5A"
BEIGE      = "#FEF0C1"
WHITE      = "#FFFFFF"

FONT = dict(family="Montserrat", color="#333")
BG = "white"

# ======== Utilidades ========
def norm_txt(s):
    if not isinstance(s, str): return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                if unicodedata.category(c) != 'Mn')
    return s.strip()

def fmt_num(x):
    try:
        return f"{int(round(float(x), 0)):,}".replace(",", " ")
    except Exception:
        return "0"

def pct(a, b):
    return (float(a)/float(b)*100.0) if float(b) != 0 else 0.0

def filtro_cdmx(df: pd.DataFrame) -> pd.DataFrame:
    if "entidad_nacimiento" not in df.columns:
        return df.iloc[0:0].copy()
    ent = df["entidad_nacimiento"].astype(str)
    ent_norm = ent.apply(norm_txt)
    mask = ent_norm.str.contains("ciudad de mexico|cdmx|distrito federal", na=False)
    return df[mask].copy()

# ======== Carga de bases por mes ========
def cargar_pd(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, encoding="utf-8-sig")
    df["Mes"] = etiqueta_mes
    df["entidad_display"] = df["entidad_nacimiento"].astype(str)
    df["entidad_norm"] = df["entidad_display"].apply(norm_txt)
    for col in ["PTPD_Aseg_H","PTPD_Aseg_M","PTPD_Puestos_H","PTPD_Puestos_M","PTPD_Aseg","PTPD_Puestos"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["independientes_H"] = df["PTPD_Aseg_H"] - df["PTPD_Puestos_H"]
    df["independientes_M"] = df["PTPD_Aseg_M"] - df["PTPD_Puestos_M"]
    df["independientes"]   = df["independientes_H"] + df["independientes_M"]
    return df

def cargar_sbc(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, encoding="utf-8-sig")
    df["Mes"] = etiqueta_mes
    # Estandariza nombres clave
    if "División" in df.columns:  # lo mostramos como "Sector"
        df["Sector"] = df["División"].astype(str)
    else:
        df["Sector"] = df["CVE_DIVISION"].astype(str)
    # Asegura numéricos
    for c in ["SalarioFem", "SalarioMasc", "PTPD_Puestos"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # normaliza entidad para filtrar CDMX
    if "entidad_nacimiento" in df.columns:
        df["entidad_norm"] = df["entidad_nacimiento"].astype(str).apply(norm_txt)
    else:
        df["entidad_norm"] = ""
    # Rango_edad_2 para pirámide
    if "Rango_edad_2" not in df.columns:
        df["Rango_edad_2"] = ""
    return df

# ======== Bloques Totales y Género (ya existentes) ========
def bloque_totales(df: pd.DataFrame, df_cdmx: pd.DataFrame, app: dash.Dash, titulo: str) -> html.Div:
    ben_n = df["PTPD_Aseg"].sum();  tdp_n = df["PTPD_Puestos"].sum();  ind_n = df["independientes"].sum()
    ben_c = df_cdmx["PTPD_Aseg"].sum() if not df_cdmx.empty else 0
    tdp_c = df_cdmx["PTPD_Puestos"].sum() if not df_cdmx.empty else 0
    ind_c = df_cdmx["independientes"].sum() if not df_cdmx.empty else 0

    card_style = {"backgroundColor": BEIGE, "borderRadius": "18px",
                  "padding": "16px 18px", "boxShadow": "0 6px 16px rgba(0,0,0,.08)"}
    label_style = {"fontSize": "18px", "color": BLUE_LIGHT, "margin": "4px 0"}
    value_style = {"fontSize": "30px", "fontWeight": "700", "color": BLUE_DARK}
    icon_repa = app.get_asset_url("repa.png")

    def columna(scope, ben, tdp, ind):
        return html.Div([
            html.H3(scope, style={"color": GUINDA, "marginTop": 0, "marginBottom": "8px"}),
            html.Div([html.Span("Beneficiados", style=label_style), html.Div(fmt_num(ben), style=value_style)]),
            html.Div([html.Span("Trab. de plataformas (TDP)", style=label_style), html.Div(fmt_num(tdp), style=value_style)]),
            html.Div([html.Span("Trab. independientes", style=label_style), html.Div(fmt_num(ind), style=value_style)]),
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
    def perc_cat(h, m):
        tot = h + m
        return pct(h, tot), pct(m, tot)

    bh, bm = df["PTPD_Aseg_H"].sum(), df["PTPD_Aseg_M"].sum()
    th, tm = df["PTPD_Puestos_H"].sum(), df["PTPD_Puestos_M"].sum()
    ih, im = df["independientes_H"].sum(), df["independientes_M"].sum()
    bH, bM = perc_cat(bh, bm);  tH, tM = perc_cat(th, tm);  iH, iM = perc_cat(ih, im)

    if not df_cdmx.empty:
        bhc, bmc = df_cdmx["PTPD_Aseg_H"].sum(), df_cdmx["PTPD_Aseg_M"].sum()
        thc, tmc = df_cdmx["PTPD_Puestos_H"].sum(), df_cdmx["PTPD_Puestos_M"].sum()
        ihc, imc = df_cdmx["independientes_H"].sum(), df_cdmx["independientes_M"].sum()
        bHc, bMc = perc_cat(bhc, bmc);  tHc, tMc = perc_cat(thc, tmc);  iHc, iMc = perc_cat(ihc, imc)
    else:
        bHc=bMc=tHc=tMc=iHc=iMc=0.0

    card_style = {"backgroundColor": BLUE_DARK, "borderRadius": "18px",
                  "padding": "18px 20px", "boxShadow": "0 6px 16px rgba(0,0,0,.08)", "color": WHITE}
    big = {"fontSize": "30px", "fontWeight": "800"}
    tag_h = {"color": WHITE, "backgroundColor": BLUE_LIGHT, "padding": "2px 8px",
             "borderRadius": "999px", "fontSize": "14px", "marginRight": "8px"}
    tag_m = {"color": WHITE, "backgroundColor": BROWN_LIGHT, "padding": "2px 8px",
             "borderRadius": "999px", "fontSize": "14px", "marginLeft": "8px"}
    icon_hm = app.get_asset_url("H-M.png")

    def panel(scope, Hvals, Mvals):
        (bH_, tH_, iH_) = Hvals; (bM_, tM_, iM_) = Mvals
        return html.Div([
            html.H3(scope, style={"color": DORADO, "marginTop": 0}),
            html.Div([
                html.Div([
                    html.Div([html.Span("Hombres", style=tag_h)], style={"marginBottom": "6px"}),
                    html.Div([html.Div("Beneficiados", style={"fontSize": "16px"}), html.Div(f"{bH_:.1f}%", style=big)]),
                    html.Div([html.Div("TDP", style={"fontSize": "16px","marginTop":"8px"}), html.Div(f"{tH_:.1f}%", style=big)]),
                    html.Div([html.Div("Independientes", style={"fontSize": "16px","marginTop":"8px"}), html.Div(f"{iH_:.1f}%", style=big)]),
                ], style={"width":"40%","display":"inline-block","verticalAlign":"top"}),
                html.Div([html.Img(src=icon_hm, style={"height":"120px","display":"block","margin":"0 auto"})],
                         style={"width":"20%","display":"inline-block","textAlign":"center"}),
                html.Div([
                    html.Div([html.Span("Mujeres", style=tag_m)], style={"textAlign":"right","marginBottom":"6px"}),
                    html.Div([html.Div("Beneficiadas", style={"fontSize":"16px","textAlign":"right"}),
                              html.Div(f"{bM_:.1f}%", style={**big,"textAlign":"right"})]),
                    html.Div([html.Div("TDP", style={"fontSize":"16px","textAlign":"right","marginTop":"8px"}),
                              html.Div(f"{tM_:.1f}%", style={**big,"textAlign":"right"})]),
                    html.Div([html.Div("Independientes", style={"fontSize":"16px","textAlign":"right","marginTop":"8px"}),
                              html.Div(f"{iM_:.1f}%", style={**big,"textAlign":"right"})]),
                ], style={"width":"40%","display":"inline-block","verticalAlign":"top"}),
            ])
        ], style=card_style)

    return html.Div([
        html.H2(titulo, style={"color": GUINDA, "marginTop":"12px"}),
        html.Div([
            html.Div(panel("Nacional",(bH,tH,iH),(bM,tM,iM)),
                    style={"width":"49%","display":"inline-block","verticalAlign":"top","marginRight":"2%"}),
            html.Div(panel("CDMX",(bHc,tHc,iHc),(bMc,tMc,iMc)),
                    style={"width":"49%","display":"inline-block","verticalAlign":"top"})
        ])
    ], style={"marginBottom":"18px"})

# ======== NUEVO: Bloque Sectores ========
def bloque_sectores(df_sbc: pd.DataFrame, titulo: str) -> html.Div:
    """Construye (para un ámbito: nacional o CDMX) el bloque con:
       - Proporción TDP por Sector
       - Salario promedio por género (por sector)
       - Brecha salarial (%)
       - Pirámide salarial por edad (promedio)
    """
    # --- Proporción por sector (TDP) ---
    prop = (df_sbc.groupby("Sector", as_index=False)["PTPD_Puestos"].sum())
    if prop["PTPD_Puestos"].sum() == 0:
        prop["Proporcion"] = 0.0
    else:
        prop["Proporcion"] = prop["PTPD_Puestos"] / prop["PTPD_Puestos"].sum() * 100
    prop = prop.sort_values("Proporcion", ascending=True)

    fig_prop = px.bar(prop, x="Proporcion", y="Sector", orientation="h",
                      color_discrete_sequence=[VERDE],
                      title="Proporción de trabajadores de plataformas por sector (%)")
    fig_prop.update_traces(hovertemplate="<b>%{y}</b><br>Proporción: %{x:.2f}%<extra></extra>")
    fig_prop.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Porcentaje", yaxis_title="")

    # --- Salario promedio por género (por sector) ---
    sal = (df_sbc.groupby("Sector", as_index=False)[["SalarioFem","SalarioMasc"]].mean().fillna(0))
    sal_long = sal.melt(id_vars="Sector", value_vars=["SalarioFem","SalarioMasc"],
                        var_name="Genero", value_name="Salario")
    sal_long["Genero"] = sal_long["Genero"].map({"SalarioFem":"Mujeres","SalarioMasc":"Hombres"})
    fig_sal = px.bar(sal_long, y="Sector", x="Salario", color="Genero",
                     orientation="h", barmode="group",
                     color_discrete_map={"Mujeres":BROWN_LIGHT, "Hombres":BLUE_DARK},
                     title="Salario base de cotización promedio por género (por sector)")
    fig_sal.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.2f}<extra></extra>")
    fig_sal.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Salario", yaxis_title="", legend_title_text="Género")

    # --- Brecha salarial (%): (Masc - Fem)/Masc*100 ---
    brecha = sal.copy()
    brecha["Brecha (%)"] = ((brecha["SalarioMasc"] - brecha["SalarioFem"]) /
                            brecha["SalarioMasc"].replace(0, pd.NA) * 100).fillna(0)
    brecha = brecha.sort_values("Brecha (%)", ascending=True)
    fig_brecha = px.bar(brecha, x="Brecha (%)", y="Sector", orientation="h",
                        color_discrete_sequence=[DORADO],
                        title="Brecha salarial de género (%) = (H - M)/H * 100")
    fig_brecha.update_traces(hovertemplate="<b>%{y}</b><br>Brecha: %{x:.2f}%<extra></extra>")
    fig_brecha.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Porcentaje", yaxis_title="")

    # --- Pirámide salarial por edad (promedios) ---
    pir = (df_sbc.groupby("Rango_edad_2", as_index=False)[["SalarioMasc","SalarioFem"]].mean().fillna(0))
    pir = pir.sort_values("Rango_edad_2")
    pir["Sal_H_neg"] = -pir["SalarioMasc"].abs()

    fig_pir = px.bar(pir, x="Sal_H_neg", y="Rango_edad_2", orientation="h",
                     color_discrete_sequence=[BLUE_DARK],
                     title="Pirámide salarial por edad (promedio)")
    fig_pir.add_bar(x=pir["SalarioFem"], y=pir["Rango_edad_2"],
                    orientation="h", marker_color=BROWN_LIGHT, name="Mujeres",
                    hovertemplate="<b>Mujeres</b> – salario: %{x:,.2f}<br>Edad: %{y}<extra></extra>")
    fig_pir.add_bar(x=pir["Sal_H_neg"], y=pir["Rango_edad_2"],
                    orientation="h", marker_color=BLUE_DARK, name="Hombres",
                    hovertemplate="<b>Hombres</b> – salario: %{customdata:,.2f}<br>Edad: %{y}<extra></extra>",
                    customdata=pir["SalarioMasc"])
    fig_pir.update_layout(barmode="overlay", plot_bgcolor=BG, font=FONT,
                          xaxis_title="Salario promedio (H izq / M der)", yaxis_title="Edad")

    # Tarjeta-resumen (opcional, compacta)
    card_style = {"backgroundColor": BEIGE, "borderRadius": "14px",
                  "padding": "12px 14px", "boxShadow": "0 6px 16px rgba(0,0,0,.06)"}
    n_sect = prop["Sector"].nunique()
    prom_m = sal["SalarioMasc"].mean()
    prom_f = sal["SalarioFem"].mean()
    brecha_prom = ((prom_m - prom_f) / prom_m * 100) if prom_m else 0
    top_sector = prop.sort_values("Proporcion", ascending=False).iloc[0]["Sector"] if len(prop) else "—"

    resumen = html.Div([
        html.Div([
            html.Div([html.Div("Sectores", style={"color": BLUE_LIGHT}),
                      html.Div(fmt_num(n_sect), style={"fontSize":"24px","fontWeight":"800","color":BLUE_DARK})],
                     style={"display":"inline-block","width":"24%"}),
            html.Div([html.Div("Salario H (prom.)", style={"color": BLUE_LIGHT}),
                      html.Div(f"{prom_m:,.2f}", style={"fontSize":"24px","fontWeight":"800","color":BLUE_DARK})],
                     style={"display":"inline-block","width":"24%"}),
            html.Div([html.Div("Salario M (prom.)", style={"color": BLUE_LIGHT}),
                      html.Div(f"{prom_f:,.2f}", style={"fontSize":"24px","fontWeight":"800","color":BLUE_DARK})],
                     style={"display":"inline-block","width":"24%"}),
            html.Div([html.Div("Brecha prom. (%)", style={"color": BLUE_LIGHT}),
                      html.Div(f"{brecha_prom:.2f}%", style={"fontSize":"24px","fontWeight":"800","color":BLUE_DARK})],
                     style={"display":"inline-block","width":"24%"}),
        ])
    ], style=card_style)

    # Ensamble de bloque
    return html.Div([
        html.H3(titulo, style={"color": GUINDA}),
        resumen,
        html.Div([
            html.Div(dcc.Graph(figure=fig_prop),   style={"width":"49%","display":"inline-block","verticalAlign":"top","marginRight":"2%"}),
            html.Div(dcc.Graph(figure=fig_sal),    style={"width":"49%","display":"inline-block","verticalAlign":"top"})
        ], style={"marginTop":"10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_brecha), style={"width":"49%","display":"inline-block","verticalAlign":"top","marginRight":"2%"}),
            html.Div(dcc.Graph(figure=fig_pir),    style={"width":"49%","display":"inline-block","verticalAlign":"top"})
        ], style={"marginTop":"10px"})
    ], style={"marginTop":"14px","marginBottom":"22px"})

def bloque_sectores_nal_cdmx(df_sbc: pd.DataFrame) -> html.Div:
    # Divide en Nacional / CDMX y arma ambos paneles
    df_cdmx = df_sbc[df_sbc.get("entidad_norm","").astype(str).str.contains("ciudad de mexico|cdmx|distrito federal", na=False)].copy()
    panel_n = bloque_sectores(df_sbc, "Sectores – Nacional")
    panel_c = bloque_sectores(df_cdmx, "Sectores – CDMX") if not df_cdmx.empty else html.Div()
    return html.Div([panel_n, panel_c])

# ======== Gráficas principales por mes + bloques ========
def layout_mes(df: pd.DataFrame, df_sbc: pd.DataFrame, mes_label: str, app: dash.Dash) -> html.Div:
    # 1) Beneficiadas por entidad
    ent = (df.groupby("entidad_display", as_index=False)["PTPD_Aseg"].sum()
             .sort_values("PTPD_Aseg", ascending=True))
    fig1 = px.bar(ent, x="PTPD_Aseg", y="entidad_display", orientation="h",
                  color_discrete_sequence=[GUINDA],
                  title=f"Total de personas beneficiadas por entidad ({mes_label})")
    fig1.update_traces(texttemplate="%{x:,.0f}", textposition="outside",
                       hovertemplate="<b>%{y}</b><br>Personas beneficiadas: %{x:,.0f}<extra></extra>")
    fig1.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Personas beneficiadas",
                       yaxis_title="", margin=dict(l=80,r=40,t=60,b=30))

    # 2) Beneficiadas vs TDP
    agg = (df.groupby("entidad_display", as_index=False)[["PTPD_Aseg","PTPD_Puestos"]].sum()
             .sort_values("PTPD_Aseg", ascending=True))
    fig2 = px.bar(agg, y="entidad_display", x=["PTPD_Aseg","PTPD_Puestos"],
                  orientation="h", barmode="group",
                  color_discrete_map={"PTPD_Aseg":GUINDA, "PTPD_Puestos":DORADO},
                  title=f"Personas beneficiadas vs Personas trabajadoras de plataformas (TDP) ({mes_label})")
    fig2.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>")
    fig2.for_each_trace(lambda t: t.update(name="Personas beneficiadas" if "Aseg" in t.name else "Personas trabajadoras de plataformas (TDP)"))
    fig2.update_layout(plot_bgcolor=BG, font=FONT, xaxis_title="Registros", yaxis_title="",
                       legend_title_text="Indicador", margin=dict(l=80,r=40,t=60,b=30))

    # 3) Pirámide nacional (beneficiadas)
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
    fig3.update_layout(barmode="overlay", plot_bgcolor=BG, font=FONT, xaxis_title="Personas", yaxis_title="Edad")

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
        fig4.update_layout(barmode="overlay", plot_bgcolor=BG, font=FONT, xaxis_title="Personas", yaxis_title="Edad")
    else:
        fig4 = px.bar(title=f"Pirámide poblacional CDMX ({mes_label}) – sin registros"); fig4.update_layout(plot_bgcolor=BG, font=FONT)

    # Bloques existentes
    totales_div = bloque_totales(df, df_cdmx, app, "Totales (números absolutos)")
    genero_div  = bloque_genero(df, df_cdmx, app, "Estructura de género (% por categoría)")

    # NUEVO: Bloque de Sectores (Nacional y CDMX)
    sectores_div = bloque_sectores_nal_cdmx(df_sbc)

    return html.Div([
        html.Div([
            html.Div(dcc.Graph(figure=fig1), style={"width":"48%","display":"inline-block","verticalAlign":"top"}),
            html.Div(dcc.Graph(figure=fig2), style={"width":"48%","display":"inline-block","verticalAlign":"top","float":"right"})
        ], style={"marginBottom":"18px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig3), style={"width":"48%","display":"inline-block","verticalAlign":"top"}),
            html.Div(dcc.Graph(figure=fig4), style={"width":"48%","display":"inline-block","verticalAlign":"top","float":"right"})
        ], style={"marginBottom":"18px"}),

        totales_div,
        genero_div,

        # 👉 Bloque Sectores
        html.H2("Sectores", style={"color": GUINDA}),
        sectores_div
    ])

# ======== Evolución (sin cambios de fondo) ========
def layout_evolucion(df_jul: pd.DataFrame, df_ago: pd.DataFrame, df_sep: pd.DataFrame) -> html.Div:
    df_all = pd.concat([df_jul, df_ago, df_sep], ignore_index=True)
    orden = ["Julio","Agosto","Septiembre"]
    df_all["Mes"] = pd.Categorical(df_all["Mes"], categories=orden, ordered=True)

    nat = (df_all.groupby("Mes", as_index=False)[
        ["PTPD_Aseg","PTPD_Puestos","independientes",
         "PTPD_Aseg_H","PTPD_Aseg_M","PTPD_Puestos_H","PTPD_Puestos_M",
         "independientes_H","independientes_M"]
    ].sum())
    nat["tasa_formalizacion"] = (nat["PTPD_Puestos"]/nat["PTPD_Aseg"]*100).round(2)

    cdmx = filtro_cdmx(df_all)
    cdmx_agg = (cdmx.groupby("Mes", as_index=False)[
        ["PTPD_Aseg","PTPD_Puestos","independientes",
         "PTPD_Aseg_H","PTPD_Aseg_M","PTPD_Puestos_H","PTPD_Puestos_M",
         "independientes_H","independientes_M"]
    ].sum())
    cdmx_agg["tasa_formalizacion"] = (cdmx_agg["PTPD_Puestos"]/cdmx_agg["PTPD_Aseg"]*100).round(2)

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

    fig_nat_tot = line_multi(nat, ["PTPD_Aseg","PTPD_Puestos","independientes"], "Nacional: Beneficiados, TDP e Independientes", "Personas")
    fig_nat_rate = line_rate(nat, "tasa_formalizacion", "Nacional: Tasa de formalización (TDP/Beneficiados)")
    fig_nat_bene = line_multi(nat, ["PTPD_Aseg_H","PTPD_Aseg_M"], "Nacional: Beneficiados por género", "Personas")
    fig_nat_tdp  = line_multi(nat, ["PTPD_Puestos_H","PTPD_Puestos_M"], "Nacional: TDP por género", "Personas")
    fig_nat_ind  = line_multi(nat, ["independientes_H","independientes_M"], "Nacional: Independientes por género", "Personas")

    fig_cdmx_tot = line_multi(cdmx_agg, ["PTPD_Aseg","PTPD_Puestos","independientes"], "CDMX: Beneficiados, TDP e Independientes", "Personas")
    fig_cdmx_rate = line_rate(cdmx_agg, "tasa_formalizacion", "CDMX: Tasa de formalización (TDP/Beneficiados)")
    fig_cdmx_bene = line_multi(cdmx_agg, ["PTPD_Aseg_H","PTPD_Aseg_M"], "CDMX: Beneficiados por género", "Personas")
    fig_cdmx_tdp  = line_multi(cdmx_agg, ["PTPD_Puestos_H","PTPD_Puestos_M"], "CDMX: TDP por género", "Personas")
    fig_cdmx_ind  = line_multi(cdmx_agg, ["independientes_H","independientes_M"], "CDMX: Independientes por género", "Personas")

    return html.Div([
        html.H2("Evolución – Nacional", style={"color": GUINDA}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_tot),  style={"width":"48%","display":"inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_rate), style={"width":"48%","display":"inline-block","float":"right"}),
        ], style={"marginBottom":"10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_nat_bene), style={"width":"32%","display":"inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_tdp),  style={"width":"32%","display":"inline-block"}),
            html.Div(dcc.Graph(figure=fig_nat_ind),  style={"width":"32%","display":"inline-block"}),
        ], style={"marginBottom":"26px"}),

        html.H2("Evolución – Ciudad de México", style={"color": GUINDA}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_tot),  style={"width":"48%","display":"inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_rate), style={"width":"48%","display":"inline-block","float":"right"}),
        ], style={"marginBottom":"10px"}),
        html.Div([
            html.Div(dcc.Graph(figure=fig_cdmx_bene), style={"width":"32%","display":"inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_tdp),  style={"width":"32%","display":"inline-block"}),
            html.Div(dcc.Graph(figure=fig_cdmx_ind),  style={"width":"32%","display":"inline-block"}),
        ])
    ])

# ======== App ========
app = dash.Dash(__name__, title="IMSS Plataformas Digitales – v5.2")

# Carga PD (personas) y SBC (salarios/divisiones)
df_jul = cargar_pd("PD_jul.csv",  "Julio")
df_ago = cargar_pd("PD_ago.csv",  "Agosto")
df_sep = cargar_pd("PD_sep.csv",  "Septiembre")

sbc_jul = cargar_sbc("sbc_jul.csv", "Julio")
sbc_ago = cargar_sbc("sbc_ago.csv", "Agosto")
sbc_sep = cargar_sbc("sbc_sep.csv", "Septiembre")

app.layout = html.Div(style={
    "fontFamily": "Montserrat",
    "backgroundColor": "#ffffff",
    "padding": "12px"
}, children=[
    html.H1("📊 Dashboard IMSS – Plataformas Digitales", style={"color": GUINDA, "textAlign": "center", "marginBottom":"12px"}),

    dcc.Tabs([
        dcc.Tab(label="Julio",       children=[layout_mes(df_jul, sbc_jul, "Julio", app)]),
        dcc.Tab(label="Agosto",      children=[layout_mes(df_ago, sbc_ago, "Agosto", app)]),
        dcc.Tab(label="Septiembre",  children=[layout_mes(df_sep, sbc_sep, "Septiembre", app)]),
        dcc.Tab(label="Evolución",   children=[layout_evolucion(df_jul, df_ago, df_sep)])
    ])
])

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)


