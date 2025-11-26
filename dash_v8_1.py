# -*- coding: utf-8 -*-
"""
Dashboard IMSS – Plataformas Digitales (Versión Final)
"""

import json
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ALL, ctx
import plotly.express as px
import plotly.graph_objects as go
import unicodedata

# ==========================================
# 1. CONFIGURACIÓN DE ESTILO Y COLORES
# ==========================================

# --- Paleta Institucional ---
GUINDA = "#9d2148"
DORADO = "#b28e5c"
CREMA_FONDO = "#F9F7F2"
BLANCO_PURO = "#FFFFFF"
TEXTO_GRIS = "#333333"

# --- Paleta de Datos ---
COL_BENEF = "#f08217"   # Afiliaciones (Total)
COL_TDP   = "#266cb4"   # TDP
COL_TI    = "#73cae6"   # TI
COL_HOMBRES = "#027a35"
COL_MUJERES = "#ac6d14"

SECTOR_TRANS = "#8F4889"
SECTOR_SERV  = "#fdc60a"
BRECHA_TRANS = "#c79ad5"
BRECHA_SERV  = "#ffe58a"

# Alias
MORADO = SECTOR_TRANS
GRIS   = SECTOR_SERV

# Fuente
FONT_FAMILY = "'Montserrat', sans-serif"

# --- Estilos CSS Inline ---
CARD_STYLE = {
    "backgroundColor": BLANCO_PURO,
    "borderRadius": "15px",
    "padding": "20px",
    "boxShadow": "0 4px 15px rgba(0,0,0,0.05)",
    "border": "1px solid rgba(0,0,0,0.02)",
    "marginBottom": "24px"
}

H2_STYLE = {
    "color": GUINDA, 
    "fontWeight": "700", 
    "letterSpacing": "-0.5px",
    "marginBottom": "20px",
    "marginTop": "10px",
    "borderLeft": f"5px solid {DORADO}",
    "paddingLeft": "15px"
}

TAB_STYLE = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '12px',
    'backgroundColor': 'rgba(0,0,0,0)',
    'color': GUINDA,
    'fontWeight': '600',
    'fontFamily': FONT_FAMILY,
    'cursor': 'pointer'
}

TAB_SELECTED_STYLE = {
    'borderTop': f'4px solid {GUINDA}',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': BLANCO_PURO,
    'color': GUINDA,
    'padding': '12px',
    'fontWeight': 'bold',
    'fontFamily': FONT_FAMILY,
    'borderRadius': '10px 10px 0px 0px'
}

# ==========================================
# 2. UTILIDADES Y CARGA DE DATOS
# ==========================================

ORDEN_EDAD = [
    "Entre 15 y 20 años", "15 y 20 años",
    "Entre 20 y 25 años", "20 y 25 años",
    "Entre 25 y 30 años", "25 y 30 años",
    "Entre 30 y 35 años", "30 y 35 años",
    "Entre 35 y 40 años", "35 y 40 años",
    "Entre 40 y 45 años", "40 y 45 años",
    "Entre 45 y 50 años", "45 y 50 años",
    "Entre 50 y 55 años", "50 y 55 años",
    "Entre 55 y 60 años", "55 y 60 años",
    "Entre 60 y 65 años", "60 y 65 años",
    "Entre 65 y 70 años", "65 y 70 años",
    "Entre 70 y 75 años", "70 y 75 años",
    "75 años y más"
]

def sort_ages(df, col_name="Rango_edad_2"):
    if col_name in df.columns:
        cats = [c for c in ORDEN_EDAD if c in df[col_name].unique()]
        extras = [c for c in df[col_name].unique() if c not in ORDEN_EDAD]
        full_order = cats + extras
        df[col_name] = pd.Categorical(df[col_name], categories=full_order, ordered=True)
        return df.sort_values(col_name)
    return df

def apply_theme(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family=FONT_FAMILY, color=TEXTO_GRIS),
        margin=dict(t=50, l=20, r=20, b=40),
        xaxis=dict(showgrid=False, zeroline=True, zerolinecolor='#E5E5E5'),
        yaxis=dict(showgrid=True, gridcolor='#F0F0F0', zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def norm_txt(s):
    if not isinstance(s, str): return s
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return s.strip()

def fmt_num(x):
    try: return f"{int(round(float(x), 0)):,}"
    except: return "0"

def filtro_cdmx(df: pd.DataFrame) -> pd.DataFrame:
    if "entidad_nacimiento" not in df.columns: return df.iloc[0:0].copy()
    ent_norm = df["entidad_nacimiento"].astype(str).apply(norm_txt)
    mask = ent_norm.str.contains("ciudad de mexico|cdmx|distrito federal", na=False)
    return df[mask].copy()

# --- Carga de Datos ---
def cargar_pd(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    try: df = pd.read_csv(path_csv, encoding="utf-8-sig")
    except: return pd.DataFrame() 
    df["Mes"] = etiqueta_mes
    df["entidad_display"] = df["entidad_nacimiento"].astype(str).replace({"México": "Estado de México", "Mexico": "Estado de México"})
    df["entidad_norm"] = df["entidad_display"].apply(norm_txt)
    for col in ["PTPD_Aseg_H", "PTPD_Aseg_M", "PTPD_Puestos_H", "PTPD_Puestos_M", "PTPD_Aseg", "PTPD_Puestos"]:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["independientes_H"] = df.get("PTPD_Aseg_H", 0) - df.get("PTPD_Puestos_H", 0)
    df["independientes_M"] = df.get("PTPD_Aseg_M", 0) - df.get("PTPD_Puestos_M", 0)
    df["independientes"]   = df["independientes_H"] + df["independientes_M"]
    return df

def cargar_sbc(path_csv: str, etiqueta_mes: str) -> pd.DataFrame:
    try: df = pd.read_csv(path_csv, encoding="utf-8-sig")
    except: return pd.DataFrame()
    df["Mes"] = etiqueta_mes
    if "División" in df.columns: df["Sector"] = df["División"].astype(str)
    elif "CVE_DIVISION" in df.columns: df["Sector"] = df["CVE_DIVISION"].astype(str)
    else: df["Sector"] = "Sector"
    for c in ["SalarioFem", "SalarioMasc", "PTPD_Puestos"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "entidad_nacimiento" in df.columns: df["entidad_norm"] = df["entidad_nacimiento"].astype(str).apply(norm_txt)
    else: df["entidad_norm"] = ""
    if "Rango_edad_2" not in df.columns: df["Rango_edad_2"] = ""
    return df

# ==========================================
# 3. COMPONENTES VISUALES
# ==========================================

def bloque_totales(df, df_cdmx, app, titulo):
    ben_n = df["PTPD_Aseg"].sum() if not df.empty else 0
    tdp_n = df["PTPD_Puestos"].sum() if not df.empty else 0
    ind_n = df["independientes"].sum() if not df.empty else 0
    
    ben_c = df_cdmx["PTPD_Aseg"].sum() if not df_cdmx.empty else 0
    tdp_c = df_cdmx["PTPD_Puestos"].sum() if not df_cdmx.empty else 0
    ind_c = df_cdmx["independientes"].sum() if not df_cdmx.empty else 0
    
    icon_repa = app.get_asset_url("repa.png")

    def kpi(label, val, color):
        return html.Div([
            html.Div(label, style={"fontSize": "13px", "color": "#777", "marginBottom": "4px"}),
            html.Div(fmt_num(val), style={"fontSize": "26px", "fontWeight": "800", "color": color})
        ], style={"marginBottom": "12px"})

    def col_kpi(ambito, b, t, i):
        return html.Div([
            html.H4(ambito.upper(), style={"color": GUINDA, "borderBottom": f"2px solid {DORADO}", "marginBottom": "10px"}),
            kpi("Afiliaciones", b, COL_BENEF),
            kpi("Trab. Plataformas (TDP)", t, COL_TDP),
            kpi("Trab. Independientes (TI)", i, COL_TI),
        ], style={"flex": 1, "padding": "0 10px"})

    return html.Div([
        html.H2(titulo, style=H2_STYLE),
        html.Div([
            col_kpi("Nacional", ben_n, tdp_n, ind_n),
            html.Div([html.Img(src=icon_repa, style={"height": "130px", "opacity":"0.9"})], 
                     style={"display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "0 20px"}),
            col_kpi("Ciudad de México", ben_c, tdp_c, ind_c)
        ], style={"display": "flex", "flexDirection": "row"})
    ], style=CARD_STYLE)

def bloque_genero(df, df_cdmx, app, titulo):
    def safe_sum(d, c): return d[c].sum() if not d.empty and c in d.columns else 0
    
    bh = safe_sum(df, "PTPD_Aseg_H"); bm = safe_sum(df, "PTPD_Aseg_M")
    th = safe_sum(df, "PTPD_Puestos_H"); tm = safe_sum(df, "PTPD_Puestos_M")
    ih = safe_sum(df, "independientes_H"); im = safe_sum(df, "independientes_M")
    
    bhc = safe_sum(df_cdmx, "PTPD_Aseg_H"); bmc = safe_sum(df_cdmx, "PTPD_Aseg_M")
    thc = safe_sum(df_cdmx, "PTPD_Puestos_H"); tmc = safe_sum(df_cdmx, "PTPD_Puestos_M")
    ihc = safe_sum(df_cdmx, "independientes_H"); imc = safe_sum(df_cdmx, "independientes_M")
    
    def get_pcts(h, m):
        t = h + m
        return (h/t*100, m/t*100) if t > 0 else (0,0)

    (bH, bM) = get_pcts(bh, bm); (tH, tM) = get_pcts(th, tm); (iH, iM) = get_pcts(ih, im)
    (bHc, bMc) = get_pcts(bhc, bmc); (tHc, tMc) = get_pcts(thc, tmc); (iHc, iMc) = get_pcts(ihc, imc)
    
    INST_GREEN_STYLE = {
        "backgroundColor": COL_HOMBRES, 
        "borderRadius": "15px", "padding": "20px", "color": "white", "marginBottom": "20px"
    }
    
    BOX_CONCEPT_STYLE = {
        "backgroundColor": "rgba(255,255,255,0.15)",
        "borderRadius": "8px",
        "padding": "10px",
        "marginBottom": "10px",
        "border": "1px solid rgba(255,255,255,0.2)"
    }

    # Colores texto claro para contraste
    TEXT_BLANCO = "#FFFFFF"
    TEXT_CREMA  = "#FEF0C1"

    def concept_box(label, h_pct, m_pct):
        return html.Div([
            html.Div(label, style={"color":DORADO, "fontSize":"14px", "fontWeight":"bold", "marginBottom":"6px", "textAlign":"center", "textTransform":"uppercase"}),
            html.Div([
                html.Div([html.Div(f"{h_pct:.1f}%", style={"fontWeight":"bold", "fontSize":"22px", "color":TEXT_CREMA}), 
                          html.Div("Hombres", style={"fontSize":"10px", "color": TEXT_CREMA, "fontWeight":"600"})]),
                
                html.Div([html.Div(f"{m_pct:.1f}%", style={"fontWeight":"bold", "fontSize":"22px", "color":TEXT_CREMA}), 
                          html.Div("Mujeres", style={"fontSize":"10px", "color": TEXT_CREMA, "fontWeight":"600", "textAlign":"right"})], style={"textAlign":"right"})
            ], style={"display":"flex", "justifyContent":"space-between"})
        ], style=BOX_CONCEPT_STYLE)

    def panel(titulo_panel, vals_h, vals_m):
        return html.Div([
            html.H4(titulo_panel, style={"color": TEXT_BLANCO, "borderBottom": "2px solid rgba(255,255,255,0.5)", "marginBottom": "15px", "paddingBottom":"5px"}),
            concept_box("Afiliaciones", vals_h[0], vals_m[0]),
            concept_box("TDP", vals_h[1], vals_m[1]),
            concept_box("Independientes", vals_h[2], vals_m[2]),
        ], style={"flex": 1})

    return html.Div([
        html.H2(titulo, style={**H2_STYLE, "color": TEXT_BLANCO, "borderLeft": f"5px solid {TEXT_BLANCO}"}), 
        html.Div([
            panel("Nacional", (bH, tH, iH), (bM, tM, iM)),
            panel("Ciudad de México", (bHc, tHc, iHc), (bMc, tMc, iMc)),
        ], style={"display": "flex", "gap": "20px", "justifyContent": "space-between"})
    ], style=INST_GREEN_STYLE)

def bloque_sectores(df_sbc, titulo, mes):
    if df_sbc.empty: return html.Div()
    
    # 1. Pie
    prop = df_sbc.groupby("Sector", as_index=False)["PTPD_Puestos"].sum()
    fig_prop = px.pie(prop, names="Sector", values="PTPD_Puestos", hole=0.6, 
                     color="Sector", color_discrete_map={"Transportes y comunicaciones": MORADO, "Servicios para empresas": GRIS})
    fig_prop.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>TDP: %{value:,.0f}<extra></extra>")
    fig_prop = apply_theme(fig_prop)
    fig_prop.update_layout(showlegend=False, annotations=[dict(text='TDP', x=0.5, y=0.5, font_size=20, showarrow=False)])

    # 2. Barras Salarios
    sal = df_sbc.groupby("Sector", as_index=False)[["SalarioFem", "SalarioMasc"]].mean().fillna(0)
    sal_long = sal.melt(id_vars="Sector", value_vars=["SalarioFem", "SalarioMasc"], var_name="Genero", value_name="Salario")
    sal_long["Genero"] = sal_long["Genero"].map({"SalarioFem": "Mujeres", "SalarioMasc": "Hombres"})
    
    fig_sal = px.bar(sal_long, y="Sector", x="Salario", color="Genero", orientation="h", barmode="group",
                     color_discrete_map={"Mujeres": COL_MUJERES, "Hombres": COL_HOMBRES})
    fig_sal.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: $%{x:,.2f}<extra></extra>")
    fig_sal = apply_theme(fig_sal)
    fig_sal.update_layout(yaxis_title=None, xaxis_title="Salario Promedio", legend_title_text="")

    # 3. Pirámide Salarial
    pir = df_sbc.groupby("Rango_edad_2", as_index=False)[["SalarioMasc", "SalarioFem"]].mean().fillna(0)
    pir = sort_ages(pir, "Rango_edad_2")
    pir["Sal_H_neg"] = -pir["SalarioMasc"].abs()
    
    max_val = max(pir["SalarioMasc"].max(), pir["SalarioFem"].max())
    if pd.isna(max_val) or max_val == 0: max_val = 1000
    tick_step = 100 if max_val < 500 else 200
    tick_vals = [x for x in range(-int(max_val), int(max_val)+1, tick_step)]
    tick_text = [str(abs(x)) for x in tick_vals]

    fig_pir = fig_pir = px.bar(
    pir,
    x="Sal_H_neg",
    y="Rango_edad_2",
    orientation="h",
    color_discrete_sequence=[COL_HOMBRES]
)
    fig_pir.data[0].name = "Hombres"   
    
    fig_pir.update_traces(
    hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{customdata:.1f}%<extra></extra>"
)
     

    fig_pir.add_bar(x=pir["SalarioFem"], y=pir["Rango_edad_2"], orientation="h", marker_color=COL_MUJERES, name="Mujeres")
    fig_pir.add_bar(x=[0], y=[pir["Rango_edad_2"].iloc[0]], orientation="h", marker_color=COL_HOMBRES, name="Hombres", showlegend=True)
    
    if not pir.empty:
        fig_pir.update_traces(hovertemplate="<b>%{y}</b><br>Salario Promedio: $%{customdata:,.2f}<extra></extra>")
        fig_pir.data[0].customdata = pir["SalarioMasc"]
        fig_pir.data[1].customdata = pir["SalarioFem"]

    fig_pir = apply_theme(fig_pir)
    fig_pir.update_layout(barmode="overlay", yaxis_title=None, xaxis=dict(title="Salario Promedio", tickvals=tick_vals, ticktext=tick_text), legend=dict(y=1.1, x=0.5, xanchor="center"))

    # KPIs
    prom_m = sal["SalarioMasc"].mean(); prom_f = sal["SalarioFem"].mean()
    brecha_gen = ((prom_m - prom_f) / prom_m * 100) if prom_m else 0
    
    kpis_html = html.Div([
        html.Div([html.Div("Salario Hombres", style={"fontSize":"12px", "color":"#999"}), html.Div(f"${prom_m:,.2f}", style={"fontSize":"20px", "fontWeight":"bold", "color":TEXTO_GRIS})], style={"flex":1, "textAlign":"center"}),
        html.Div([html.Div("Salario Mujeres", style={"fontSize":"12px", "color":"#999"}), html.Div(f"${prom_f:,.2f}", style={"fontSize":"20px", "fontWeight":"bold", "color":TEXTO_GRIS})], style={"flex":1, "textAlign":"center"}),
        html.Div([html.Div("Brecha Global", style={"fontSize":"12px", "color":"#999"}), html.Div(f"{brecha_gen:.1f}%", style={"fontSize":"24px", "fontWeight":"bold", "color":COL_BENEF})], style={"flex":1, "textAlign":"center"}),
    ], style={"display":"flex", "padding":"15px", "borderBottom":"1px solid #eee", "marginBottom":"15px"})

    # Circulos
    brecha = sal.copy()
    brecha["Brecha"] = ((brecha["SalarioMasc"] - brecha["SalarioFem"]) / brecha["SalarioMasc"] * 100).fillna(0)
    circs = []
    for _, r in brecha.iterrows():
        c = BRECHA_TRANS if "Transportes" in r["Sector"] else BRECHA_SERV
        circs.append(html.Div([
            html.Div(f"{r['Brecha']:.1f}%", style={"width":"70px","height":"70px","borderRadius":"50%","backgroundColor":c, "color":"white","display":"flex","alignItems":"center","justifyContent":"center","fontWeight":"bold","marginBottom":"5px"}),
            html.Div(r["Sector"], style={"fontSize":"10px","textAlign":"center","width":"70px"})
        ], style={"margin":"0 10px"}))

    # IDs únicos usando 'mes'
    return html.Div([
        html.H2(titulo, style=H2_STYLE),
        html.Div([
            html.Div([
                html.H4("Distribución Sectorial (TDP)", style={"textAlign":"center", "fontSize":"14px", "color":GUINDA}),
                dcc.Graph(figure=fig_prop, style={"height":"250px"}, id={'type': 'copy-graph', 'index': f"pie-{titulo}-{mes}"}) 
            ], style={**CARD_STYLE, "flex":1, "marginRight":"15px"}),
            html.Div([
                kpis_html,
                dcc.Graph(figure=fig_sal, style={"height":"200px"}, id={'type': 'copy-graph', 'index': f"bar-{titulo}-{mes}"})
            ], style={**CARD_STYLE, "flex":2})
        ], style={"display":"flex"}),
        html.Div([
            html.Div([
                html.H4("Brecha Salarial por Sector", style={"textAlign":"center", "fontSize":"14px", "color":GUINDA, "marginBottom":"15px"}),
                html.Div(circs, style={"display":"flex", "justifyContent":"center"})
            ], style={**CARD_STYLE, "flex":1, "marginRight":"15px"}),
             html.Div([
                html.H4("Pirámide Salarial por Edad", style={"textAlign":"center", "fontSize":"14px", "color":GUINDA}),
                dcc.Graph(figure=fig_pir, style={"height":"300px"}, id={'type': 'copy-graph', 'index': f"pir-{titulo}-{mes}"})
            ], style={**CARD_STYLE, "flex":2})
        ], style={"display":"flex"})
    ])

# ==========================================
# 4. LAYOUTS DE PESTAÑAS
# ==========================================

def layout_mes(df, df_sbc, mes_label, app):
    agg = df.groupby("entidad_display", as_index=False)[["PTPD_Aseg", "PTPD_Puestos"]].sum().sort_values("PTPD_Aseg", ascending=True)
    agg["TI"] = agg["PTPD_Aseg"] - agg["PTPD_Puestos"]
    
    fig_geo = px.bar(agg, y="entidad_display", x=["TI", "PTPD_Puestos"], orientation="h", 
                     color_discrete_map={"TI": COL_TI, "PTPD_Puestos": COL_TDP}, height=800)
    
    fig_geo.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{x:,.0f}<extra></extra>")
    new_names = {"TI": "Trabajadores Independientes (TI)", "PTPD_Puestos": "Trabajadores de Plataformas (TDP)"}
    fig_geo.for_each_trace(lambda t: t.update(name = new_names.get(t.name, t.name)))
    
    fig_geo.add_trace(go.Scatter(
        x=agg["PTPD_Aseg"], y=agg["entidad_display"], mode="text",
        text=agg["PTPD_Aseg"].apply(lambda x: f"<b>{x:,.0f}</b>"),
        textfont=dict(color=COL_BENEF, size=11), 
        textposition="middle right", 
        cliponaxis=False,
        showlegend=False, hoverinfo="skip"
    ))
    
    fig_geo.update_layout(
        margin=dict(r=220, t=60, b=50),
        legend=dict(orientation="h", y=1.08, x=0),
        annotations=[
            dict(
                x=.85,                # 1. Fijar exactamente al borde derecho del área de barras
                y=1.02,             # 2. Un poco por encima del tope (ajusta si choca con la barra superior)
                xref="paper", 
                yref="paper",
                text="<b>Total<br>Afiliaciones</b>",
                showarrow=False,
                font=dict(color=COL_BENEF, size=12),
                xanchor="left",     # 3. Importante: El texto crece hacia la derecha
                align="left",
                xshift=10           # 4. Moverlo 10px a la derecha del borde (fijo, no porcentual)
            )
        ]
    )
    fig_geo = apply_theme(fig_geo)
    fig_geo.update_layout(yaxis_title="", xaxis_title="Total Afiliaciones", legend=dict(title=None))

    def make_pop_pyramid(d, title):
        if d.empty: return go.Figure()
        age_df = d.groupby("Rango_edad_2", as_index=False)[["PTPD_Aseg_H", "PTPD_Aseg_M"]].sum()
        age_df = sort_ages(age_df, "Rango_edad_2")
        
        tot = age_df["PTPD_Aseg_H"].sum() + age_df["PTPD_Aseg_M"].sum()
        if tot > 0:
            age_df["H"] = age_df["PTPD_Aseg_H"]/tot*100
            age_df["M"] = age_df["PTPD_Aseg_M"]/tot*100
        else:
            age_df["H"]=0; age_df["M"]=0
            
        age_df["H_neg"] = -age_df["H"]
        
        max_pct = max(age_df["H"].max(), age_df["M"].max())
        if pd.isna(max_pct) or max_pct == 0: max_pct = 10
        t_vals = [-max_pct, -max_pct/2, 0, max_pct/2, max_pct]
        t_text = [f"{abs(x):.1f}%" for x in t_vals]

        # 1. Crear la figura base
        fig = px.bar(age_df, x="H_neg", y="Rango_edad_2", orientation="h", color_discrete_sequence=[COL_HOMBRES])
        
        # --- CORRECCIÓN AQUÍ ---
        # Asignamos explícitamente el nombre "Hombres" a la traza principal de datos
        fig.data[0].name = "Hombres"
        # Aseguramos que no duplique la leyenda (ya que tienes una barra dummy abajo para eso)
        fig.data[0].showlegend = False 
        # -----------------------

        fig.add_bar(x=age_df["M"], y=age_df["Rango_edad_2"], orientation="h", marker_color=COL_MUJERES, name="Mujeres")
        
        # Esta es tu barra dummy para forzar la leyenda (la mantenemos igual)
        fig.add_bar(x=[0], y=[age_df["Rango_edad_2"].iloc[0]], orientation="h", marker_color=COL_HOMBRES, name="Hombres", showlegend=True)
        
        if not age_df.empty:
            # Ahora %{fullData.name} leerá "Hombres" correctamente en la traza 0
            fig.update_traces(hovertemplate="<b>%{y}</b><br>%{fullData.name}: %{customdata:.1f}%<extra></extra>")
            fig.data[0].customdata = age_df["H"]
            fig.data[1].customdata = age_df["M"]
        
        fig = apply_theme(fig)
        fig.update_layout(
            barmode="overlay", title=title, xaxis_title="% Población", yaxis_title=None,
            xaxis=dict(tickvals=t_vals, ticktext=t_text),
            legend=dict(y=1.1, x=0.5, xanchor="center")
        )
        return fig

    fig_pir_nal = make_pop_pyramid(df, "Nacional")
    fig_pir_cdmx = make_pop_pyramid(filtro_cdmx(df), "CDMX")

    return html.Div([
        bloque_totales(df, filtro_cdmx(df), app, "Resumen Ejecutivo"),
        bloque_genero(df, filtro_cdmx(df), app, "Estructura Demográfica"),
        
        html.Div([
            html.H2("Distribución Geográfica por entidad de nacimiento", style=H2_STYLE),
            dcc.Graph(figure=fig_geo, id={'type': 'copy-graph', 'index': f"geo-{mes_label}"})
        ], style=CARD_STYLE),
        
        html.Div([
            html.H2("Pirámides de Edad (Afiliaciones)", style=H2_STYLE),
            html.Div([
                html.Div(dcc.Graph(figure=fig_pir_nal, id={'type': 'copy-graph', 'index': f"pir-nal-{mes_label}"}), style={"flex":1}),
                html.Div(dcc.Graph(figure=fig_pir_cdmx, id={'type': 'copy-graph', 'index': f"pir-cdmx-{mes_label}"}), style={"flex":1})
            ], style={"display":"flex"})
        ], style=CARD_STYLE),
        
        # Pasar el MES para IDs únicos
        bloque_sectores(df_sbc, "Análisis Sectorial - Nacional", mes_label),
        bloque_sectores(filtro_cdmx(df_sbc), "Análisis Sectorial - CDMX", mes_label)
    ])

# --- Pestaña Evolución ---
def layout_evolucion(df_jul, df_ago, df_sep, df_oct, sj, sa, ss, so):
    df_all = pd.concat([df_jul, df_ago, df_sep, df_oct], ignore_index=True)
    order = ["Julio", "Agosto", "Septiembre", "Octubre"]
    df_all["Mes"] = pd.Categorical(df_all["Mes"], categories=order, ordered=True)
    sbc_all = pd.concat([sj, sa, ss, so], ignore_index=True)
    sbc_all["Mes"] = pd.Categorical(sbc_all["Mes"], categories=order, ordered=True)

    nat = df_all.groupby("Mes", as_index=False)[["PTPD_Aseg","PTPD_Puestos","independientes","PTPD_Aseg_H","PTPD_Aseg_M","PTPD_Puestos_H","PTPD_Puestos_M","independientes_H","independientes_M"]].sum()
    nat["Tasa"] = (nat["PTPD_Puestos"]/nat["PTPD_Aseg"]*100).fillna(0)
    cdmx_all = filtro_cdmx(df_all)
    cdmx = cdmx_all.groupby("Mes", as_index=False)[["PTPD_Aseg","PTPD_Puestos","independientes","PTPD_Aseg_H","PTPD_Aseg_M","PTPD_Puestos_H","PTPD_Puestos_M","independientes_H","independientes_M"]].sum()
    cdmx["Tasa"] = (cdmx["PTPD_Puestos"]/cdmx["PTPD_Aseg"]*100).fillna(0)

    def make_var_table(data):
        d = data.copy()
        d["Var_abs_ben"] = d["PTPD_Aseg"].diff()
        d["Var_pct_ben"] = d["PTPD_Aseg"].pct_change() * 100
        d["Var_abs_tdp"] = d["PTPD_Puestos"].diff()
        d["Var_pct_tdp"] = d["PTPD_Puestos"].pct_change() * 100
        
        final = pd.DataFrame()
        final["Periodo"] = d["Mes"]
        final["Afiliaciones"] = d["PTPD_Aseg"].apply(fmt_num)
        final["Var. abs. afiliaciones"] = d["Var_abs_ben"].apply(lambda x: f"{x:+,.0f}" if pd.notna(x) else "-")
        final["Var. % afiliaciones"] = d["Var_pct_ben"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
        final["Personas TDP"] = d["PTPD_Puestos"].apply(fmt_num)
        final["Var. abs. TDP"] = d["Var_abs_tdp"].apply(lambda x: f"{x:+,.0f}" if pd.notna(x) else "-")
        final["Var. % TDP"] = d["Var_pct_tdp"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
        final["Tasa de formalización (%)"] = d["Tasa"].apply(lambda x: f"{x:.2f}")
        return final

    def make_sal_table(sbc_data, is_cdmx=False):
        if is_cdmx: sbc_data = filtro_cdmx(sbc_data)
        g = sbc_data.groupby("Mes", as_index=False)[["SalarioMasc", "SalarioFem"]].mean()
        g["Brecha"] = (g["SalarioMasc"] - g["SalarioFem"]) / g["SalarioMasc"] * 100
        
        final = pd.DataFrame()
        final["Periodo"] = g["Mes"]
        final["Salario base promedio"] = g["SalarioMasc"].apply(lambda x: f"{x:,.2f}")
        final["Brecha salarial H/M (%)"] = g["Brecha"].apply(lambda x: f"{x:.2f}")
        return final

    TH_STYLE = {"backgroundColor": GUINDA, "color": "white", "padding": "10px", "textAlign": "center", "border": "1px solid #ddd"}
    TD_STYLE = {"padding": "8px", "border": "1px solid #ddd", "textAlign": "center"}

    def render_html_table(df, title):
        return html.Div([
            html.H4(title, style={"color":GUINDA, "textAlign":"center", "marginBottom":"10px"}),
            html.Table(
                [html.Tr([html.Th(c, style=TH_STYLE) for c in df.columns])] +
                [html.Tr([html.Td(df.iloc[i][c], style=TD_STYLE) for c in df.columns]) for i in range(len(df))],
                style={"width":"100%", "borderCollapse":"collapse", "fontSize":"13px", "margin":"0 auto"}
            )
        ], style={"marginBottom":"30px", "overflowX":"auto"})

    def plot_lines(data, cols, names, colors, title, y_title):
        fig = go.Figure()
        for col, name, color in zip(cols, names, colors):
            fig.add_trace(go.Scatter(
                x=data["Mes"], y=data[col], mode='lines+markers', name=name,
                line=dict(color=color, width=3), marker=dict(size=8),
                hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:,.0f}}<extra></extra>"
            ))
        fig = apply_theme(fig)
        fig.update_layout(title=title, yaxis_title=y_title, hovermode="closest", legend=dict(y=1.1))
        return fig

    def build_section(data, sbc_data, title_sec, is_cdmx):
        f1 = plot_lines(data, ["PTPD_Aseg", "PTPD_Puestos", "independientes"], ["Afiliaciones", "TDP", "TI"], [COL_BENEF, COL_TDP, COL_TI], "Totales", "Personas")
        fig_rate = go.Figure()
        fig_rate.add_trace(go.Scatter(x=data["Mes"], y=data["Tasa"], mode='lines+markers', name="Tasa", line=dict(color=GUINDA, width=3), marker=dict(size=8), hovertemplate="<b>%{x}</b><br>Tasa: %{y:.2f}%<extra></extra>"))
        fig_rate = apply_theme(fig_rate)
        fig_rate.update_layout(title="Tasa Formalización", yaxis_title="%")

        f_sex_ben = plot_lines(data, ["PTPD_Aseg_H", "PTPD_Aseg_M"], ["Hombres", "Mujeres"], [COL_HOMBRES, COL_MUJERES], "Afiliaciones", "Personas")
        f_sex_tdp = plot_lines(data, ["PTPD_Puestos_H", "PTPD_Puestos_M"], ["Hombres", "Mujeres"], [COL_HOMBRES, COL_MUJERES], "TDP", "Personas")
        f_sex_ind = plot_lines(data, ["independientes_H", "independientes_M"], ["Hombres", "Mujeres"], [COL_HOMBRES, COL_MUJERES], "Independientes", "Personas")
        
        df_vars = make_var_table(data)
        df_sal = make_sal_table(sbc_data, is_cdmx)
        suffix = "CDMX" if is_cdmx else "Nacional"
        
        return html.Div([
            html.H2(title_sec, style=H2_STYLE),
            html.Div([
                html.Div(dcc.Graph(figure=f1, id={'type': 'copy-graph', 'index': f"evo-tot-{suffix}"}), style={**CARD_STYLE, "flex":1, "marginRight":"15px"}),
                html.Div(dcc.Graph(figure=fig_rate, id={'type': 'copy-graph', 'index': f"evo-rat-{suffix}"}), style={**CARD_STYLE, "flex":1})
            ], style={"display":"flex"}),
            
            html.H4("Evolución por Sexo", style={"color":GUINDA, "marginLeft":"10px", "marginTop":"20px"}),
            html.Div([
                html.Div(dcc.Graph(figure=f_sex_ben, id={'type': 'copy-graph', 'index': f"evo-ben-{suffix}"}), style={**CARD_STYLE, "flex":1, "marginRight":"10px"}),
                html.Div(dcc.Graph(figure=f_sex_tdp, id={'type': 'copy-graph', 'index': f"evo-tdp-{suffix}"}), style={**CARD_STYLE, "flex":1, "marginRight":"10px"}),
                html.Div(dcc.Graph(figure=f_sex_ind, id={'type': 'copy-graph', 'index': f"evo-ind-{suffix}"}), style={**CARD_STYLE, "flex":1}),
            ], style={"display":"flex"}),
            
            html.Div([
                render_html_table(df_vars, f"Tabla {suffix} – Afiliaciones, TDP y Tasa"),
                render_html_table(df_sal, f"Tabla {suffix} – Salario Base y Brecha")
            ], style=CARD_STYLE)
        ])

    return html.Div([
        build_section(nat, sbc_all, "Evolución Nacional", False),
        build_section(cdmx, sbc_all, "Evolución Ciudad de México", True)
    ])

# ==========================================
# 5. APP PRINCIPAL
# ==========================================
app = dash.Dash(__name__, title="IMSS Plataformas - Final v5", suppress_callback_exceptions=True)

glosario = html.Details([
    html.Summary("Glosario de Términos y Notas Metodológicas (Clic para desplegar)", style={"cursor":"pointer", "color":GUINDA, "fontWeight":"bold", "fontSize":"16px", "padding":"10px", "backgroundColor":"#eee", "borderRadius":"5px"}),
    html.Div([
        # --- Conceptos Existentes ---
        html.Div([
            html.Strong("Afiliaciones: "), 
            "Registros de personas que prestan servicios o realizan tareas en un esquema de trabajo presencial mediado por plataformas digitales.",
            html.Br(),
            "A partir de la Reforma Laboral de Plataformas Digitales, todas estas personas están cubiertas por el seguro ante ",
            html.Strong("Riesgos de Trabajo"), " del IMSS mientras realizan su actividad laboral.",
            html.Br(), html.Small("Nota: Este total se refiere al total de las afiliaciones de personas que trabajan a través de plataformas digitales. No son registros únicos, por lo que puede incluir registros de personas que trabajan en más de una plataforma.")
        ], style={"marginBottom":"10px"}),
        
        html.Div([
            html.Strong("Personas Trabajadoras de Plataforma Digital (TDP): "),
            "Personas que trabajan en plataformas digitales y que al final de un mes calendario alcanzaron el umbral de ingresos necesario para ser consideradas Personas Trabajadoras de Plataforma Digital.",
            html.Br(),
            "Es decir, después de descontar el ", html.Strong("Factor de Exclusión"), ", su ingreso neto resultó igual o superior al ",
            html.Strong("Salario Mínimo de la Ciudad de México."),
            html.Br(),
            "Estas personas trabajadoras tienen acceso a una cobertura integral en las 5 áreas de aseguramiento que ofrece el IMSS."
        ], style={"marginBottom":"10px"}),
        
        html.Div([
            html.Strong("Personas Trabajadoras Independientes (TI): "),
            "Personas que trabajan en plataformas digitales y que al término de un mes calendario no alcanzaron el umbral de ingresos necesario para ser consideradas TDP.",
            html.Br(),
            "Estas personas siempre están cubiertas por el seguro de ", html.Strong("Riesgos de Trabajo"),
            ", así como la cobertura por el seguro de ", html.Strong("Enfermedades y Maternidad en especie.")
        ], style={"marginBottom":"10px"}),
        
        html.Div([
            html.Strong("Factor de exclusión: "),
            "Mecanismo contable que se aplica al ingreso bruto de quien trabaja a través de una Plataforma Digital para determinar quién es una Persona Trabajadora Independiente y quién es Persona Trabajadora de Plataforma.",
            html.Br(),
            "El factor depende del medio de transporte que use cada persona para trabajar.",
            html.Br(),
            html.Ul([
                html.Li("Vehículos de 4 ruedas con motor: 55%"),
                html.Li("Vehículos de 2 ruedas con motor: 40%"),
                html.Li("Vehículos sin motor o sin vehículo: 12%")
            ])
        ], style={"marginBottom":"10px"}),

        # --- NUEVO: Tasa de formalización ---
        html.Div([
            html.Strong("Tasa de formalización: "),
            "Es la proporción de los registros de Personas Trabajadoras de Plataformas Digitales con respecto al total de Afiliaciones. ",
            "Se emplea el término “tasa de formalización” para enfatizar el carácter flexible y continuo del proceso de incorporación de las y los trabajadores de plataformas digitales al Régimen Obligatorio del Instituto Mexicano del Seguro Social (IMSS)."
        ], style={"marginBottom":"20px"}),

        # --- Línea divisoria ---
        html.Hr(style={"borderTop": "1px solid #ccc", "margin": "20px 0"}),

        # --- NUEVO: Nota Metodológica y Fuente ---
        html.Div([
            html.H5("Nota metodológica", style={"color": GUINDA, "marginTop": "0", "marginBottom": "10px"}),
            
            html.Div([
                html.Strong("Distribución geográfica: "),
                "La distribución por entidad geográfica se realiza utilizando la variable para ",
                html.Strong("entidad de nacimiento"), "."
            ], style={"marginBottom":"10px"}),

             html.Div([
                html.Strong("Brechas salariales:"),
                " La información disponible no permite conocer el tiempo trabajado por cada persona afiliada, por lo que los SBC no comparten una misma unidad de tiempo base. Además, el tipo de vehículo utilizado para laborar influye en el cálculo del ingreso neto mediante el factor de exclusión, lo que determina la magnitud del SBC. Por lo tanto, las diferencias salariales observadas pueden reflejar tanto la composición del trabajo como difrencias en actividades para cada grupo además de difrerencias estrictamente salariales",
               "."
            ], style={"marginBottom":"10px"}),


    
            html.Div([
                html.Strong("Fuente: "),
                "Programa Piloto de Personas Trabajadoras de Plataformas Digitales. IMSS. ",
                html.A("Ver Fuente (Tableau Public)", 
                       href="https://public.tableau.com/app/profile/imss.cpe/viz/ProgramaPilotodePersonasTrabajadorasdePlataformasDigitales/PruebaPilotodeIncorporacindePTPD", 
                       target="_blank", 
                       style={"color": COL_TDP, "textDecoration": "underline"})
            ])
        ], style={"fontSize": "13px", "backgroundColor": "#f9f9f9", "padding": "15px", "borderRadius": "5px", "borderLeft": f"4px solid {DORADO}"})

    ], style={"padding":"20px", "lineHeight":"1.6", "fontSize":"14px", "color":"#333", "textAlign": "justify"})
], style={**CARD_STYLE, "padding":"0"})
# Carga
df_j = cargar_pd("PD_jul.csv", "Julio"); sbc_j = cargar_sbc("sbc_jul.csv", "Julio")
df_a = cargar_pd("PD_ago.csv", "Agosto"); sbc_a = cargar_sbc("sbc_ago.csv", "Agosto")
df_s = cargar_pd("PD_sep.csv", "Septiembre"); sbc_s = cargar_sbc("sbc_sep.csv", "Septiembre")
df_o = cargar_pd("PD_oct.csv", "Octubre"); sbc_o = cargar_sbc("sbc_oct.csv", "Octubre")

header = html.Div([
    html.Div([
        html.H1("TABLERO DE DATOS", style={"color":BLANCO_PURO, "margin":0, "fontSize":"24px"}),
        html.Div("IMSS – Personas Trabajadoras de Plataformas Digitales", style={"color":DORADO})
    ])
], style={"backgroundColor":GUINDA, "padding":"20px 40px", "boxShadow":"0 4px 10px rgba(0,0,0,0.2)"})

clipboard = dcc.Clipboard(id="clipboard", style={"display": "none"})
notify = html.Div(id="notify-copy", style={"position":"fixed", "bottom":"20px", "right":"20px", "backgroundColor":"#333", "color":"white", "padding":"10px 20px", "borderRadius":"5px", "display":"none", "zIndex":9999}, children="Dato copiado")

app.layout = html.Div([
    html.Link(href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap", rel="stylesheet"),
    header,
    html.Div([
        glosario,
        dcc.Tabs([
            dcc.Tab(label="Julio", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE, children=[layout_mes(df_j, sbc_j, "Julio", app)]),
            dcc.Tab(label="Agosto", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE, children=[layout_mes(df_a, sbc_a, "Agosto", app)]),
            dcc.Tab(label="Septiembre", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE, children=[layout_mes(df_s, sbc_s, "Septiembre", app)]),
            dcc.Tab(label="Octubre", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE, children=[layout_mes(df_o, sbc_o, "Octubre", app)]),
            dcc.Tab(label="Evolución", style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE, children=[layout_evolucion(df_j, df_a, df_s, df_o, sbc_j, sbc_a, sbc_s, sbc_o)]),
        ], style={"marginTop":"20px"}),
        clipboard,
        notify
    ], style={"maxWidth":"1400px", "margin":"0 auto", "padding":"20px"})
], style={"backgroundColor":CREMA_FONDO, "minHeight":"100vh", "fontFamily":FONT_FAMILY})

@app.callback(
    Output("clipboard", "content"),
    Output("notify-copy", "style"),
    Input({'type': 'copy-graph', 'index': ALL}, 'clickData'),
    prevent_initial_call=True
)
def copy_to_clipboard(clickData):
    if not ctx.triggered:
        return dash.no_update, {"display": "none"}

    click = ctx.triggered[0]['value']
    if not click or 'points' not in click:
        return dash.no_update, {"display": "none"}

    p = click['points'][0]

    raw = None

    # 1. customdata (pirámides, pirámides salariales)
    if 'customdata' in p and p['customdata'] not in [None, [], ""]:
        cd = p['customdata']
        raw = cd[0] if isinstance(cd, list) else cd

    # 2. value (pie charts)
    if raw is None and 'value' in p:
        raw = p['value']

    # 3. y (líneas, barras verticales)
    if raw is None and isinstance(p.get('y', None), (int, float)):
        raw = p['y']

    # 4. x (pirámides, barras horizontales)
    if raw is None and isinstance(p.get('x', None), (int, float)):
        raw = abs(p['x'])   # ← esto arregla los negativos en pirámides

    if raw is None:
        return dash.no_update, {"display": "none"}

    # -- Formateo
    try:
        num = float(raw)
        raw_str = f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
    except:
        raw_str = str(raw)

    return raw_str, {
        "position": "fixed",
        "bottom": "20px",
        "right": "20px",
        "backgroundColor": "#333",
        "color": "white",
        "padding": "10px 20px",
        "borderRadius": "5px",
        "display": "block"
    }

    return dash.no_update, {"display": "none"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)

