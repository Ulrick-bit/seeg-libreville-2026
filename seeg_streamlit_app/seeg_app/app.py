import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ============================================================
# CONFIG PAGE
# ============================================================
st.set_page_config(
    page_title="Délestages SEEG — Libreville Février 2026",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS PERSONNALISÉ
# ============================================================
st.markdown("""
<style>
    /* Fond principal */
    .stApp { background-color: #0a1628; color: #ffffff; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0d1f3c; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* Titres */
    h1, h2, h3 { color: #00d4ff !important; }
    
    /* Métriques KPI */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a3a6b, #0d2348);
        border: 1px solid #00d4ff;
        border-radius: 12px;
        padding: 15px;
    }
    [data-testid="stMetricLabel"] { color: #a0c4ff !important; font-size: 13px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: bold !important; }
    [data-testid="stMetricDelta"] { color: #00d4ff !important; }
    
    /* Navigation tabs */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #0d1f3c;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] { 
        color: #a0c4ff !important;
        font-weight: 600;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #00d4ff !important;
        color: #0a1628 !important;
    }

    /* Titre principal */
    .main-title {
        background: linear-gradient(90deg, #00d4ff, #0066ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        color: #a0c4ff;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 20px;
    }
    
    /* Séparateur */
    hr { border-color: #1a3a6b; }
    
    /* Selectbox et sliders */
    .stSelectbox label, .stMultiSelect label, .stSlider label { 
        color: #a0c4ff !important; 
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHARGEMENT ET PRÉPARATION DES DONNÉES
# ============================================================
@st.cache_data
def charger_donnees():
    df = pd.read_csv("seeg_data.csv", encoding="utf-8-sig")
    
    # Nettoyer les dates
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["date"])
    
    # Heure début → entier pour comparaisons
    def heure_to_int(h):
        if pd.isna(h): return None
        h = str(h).replace("h", ":").replace("H", ":")
        try:
            parts = h.split(":")
            return int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else int(parts[0]) * 60
        except: return None
    
    df["heure_min"] = df["heure_debut"].apply(heure_to_int)
    
    # Période de la journée
    def periode(h):
        if h is None: return "Inconnu"
        if 300 <= h < 720: return "Matin"
        elif 720 <= h < 1020: return "Après-midi"
        elif 1020 <= h < 1320: return "Soirée"
        else: return "Nuit"
    
    df["Periode_Journee"] = df["heure_min"].apply(periode)
    
    # Jour de la semaine
    jours_fr = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
    df["Jour_Semaine"] = df["date"].dt.dayofweek.map(jours_fr)
    df["Num_Jour"] = df["date"].dt.dayofweek
    
    # Semaine du mois
    def semaine_mois(d):
        j = d.day
        if j <= 7: return "S1 (1-7 fév)"
        elif j <= 14: return "S2 (8-14 fév)"
        elif j <= 21: return "S3 (15-21 fév)"
        else: return "S4 (22-28 fév)"
    
    df["Semaine_mois"] = df["date"].apply(semaine_mois)
    df["duree_heures"] = df["duree_minutes"] / 60
    df["jour"] = df["date"].dt.day
    
    # IPD Coefficient
    coef = {"Soirée": 3, "Après-midi": 2, "Matin": 1.5, "Nuit": 1}
    df["coef"] = df["Periode_Journee"].map(coef).fillna(1)
    df["ipd"] = df["duree_minutes"] * df["coef"] / 60
    
    return df

df = charger_donnees()

# ============================================================
# COULEURS
# ============================================================
COULEURS_PERIODE = {
    "Matin": "#FFD700",
    "Après-midi": "#FF8C00",
    "Soirée": "#FF4444",
    "Nuit": "#4444FF"
}

PALETTE = ["#00d4ff", "#0066ff", "#ff4444", "#ffd700", "#00ff88", "#ff8c00", "#aa44ff"]

# ============================================================
# EN-TÊTE
# ============================================================
col_titre, col_badge = st.columns([4, 1])
with col_titre:
    st.markdown('<p class="main-title">⚡ Analyse des Délestages SEEG</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Libreville, Grand Libreville — Février 2026 | Source : Plannings officiels SEEG</p>', unsafe_allow_html=True)
with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"📊 {len(df):,} délestages analysés")

st.markdown("---")

# ============================================================
# SIDEBAR — FILTRES GLOBAUX
# ============================================================
with st.sidebar:
    st.markdown("## 🎛️ Filtres")
    st.markdown("---")
    
    # Filtre période
    periodes_dispo = ["Toutes"] + sorted(df["Periode_Journee"].unique().tolist())
    periode_sel = st.selectbox("⏰ Période de la journée", periodes_dispo)
    
    # Filtre semaine
    semaines_dispo = ["Toutes"] + ["S1 (1-7 fév)", "S2 (8-14 fév)", "S3 (15-21 fév)", "S4 (22-28 fév)"]
    semaine_sel = st.selectbox("📅 Semaine du mois", semaines_dispo)
    
    # Filtre quartier (multi)
    st.markdown("---")
    top_quartiers = df["quartier"].value_counts().head(30).index.tolist()
    quartiers_sel = st.multiselect(
        "🏘️ Quartiers (Top 30)",
        options=top_quartiers,
        default=[],
        placeholder="Tous les quartiers"
    )
    
    st.markdown("---")
    st.markdown("### 📌 À propos")
    st.markdown("""
    Analyse des plannings officiels de délestage publiés par la SEEG sur ses canaux officiels.
    
    **Méthode** : OCR → Python → Géocodage OSM
    
    **Couverture** : 99,5% géocodé
    """)

# ============================================================
# APPLICATION DES FILTRES
# ============================================================
dff = df.copy()
if periode_sel != "Toutes":
    dff = dff[dff["Periode_Journee"] == periode_sel]
if semaine_sel != "Toutes":
    dff = dff[dff["Semaine_mois"] == semaine_sel]
if quartiers_sel:
    dff = dff[dff["quartier"].isin(quartiers_sel)]

# ============================================================
# ONGLETS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Vue Globale",
    "🗺️ Vue Géographique",
    "⏱️ Vue Temporelle",
    "🏆 Classement IPD"
])

# ============================================================
# TAB 1 — VUE GLOBALE
# ============================================================
with tab1:
    st.markdown("### 📊 Vue d'ensemble — Février 2026")
    
    # KPI Cards
    k1, k2, k3, k4, k5 = st.columns(5)
    
    total_del = len(dff)
    q_uniques = dff["quartier"].nunique()
    duree_moy = dff["duree_minutes"].mean()
    jours_del = dff["date"].nunique()
    pct_soiree = len(dff[dff["Periode_Journee"] == "Soirée"]) / max(total_del, 1) * 100
    
    k1.metric("⚡ Total Délestages", f"{total_del:,}")
    k2.metric("🏘️ Quartiers Impactés", f"{q_uniques:,}")
    k3.metric("⏱️ Durée Moyenne", f"{duree_moy:.0f} min")
    k4.metric("📅 Jours Planifiés", f"{jours_del}")
    k5.metric("🌙 Part Soirée", f"{pct_soiree:.1f}%")
    
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Courbe évolution quotidienne
        evo = dff.groupby("date").agg(
            Total=("quartier", "count"),
            Quartiers=("quartier", "nunique")
        ).reset_index()
        
        fig_evo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_evo.add_trace(
            go.Bar(x=evo["date"], y=evo["Total"], name="Total délestages",
                   marker_color="#00d4ff", opacity=0.8),
            secondary_y=False
        )
        fig_evo.add_trace(
            go.Scatter(x=evo["date"], y=evo["Quartiers"], name="Quartiers uniques",
                      line=dict(color="#ffd700", width=2.5), mode="lines+markers",
                      marker=dict(size=5)),
            secondary_y=True
        )
        
        # Annoter les pics
        if len(evo) > 0:
            idx_max = evo["Total"].idxmax()
            fig_evo.add_annotation(
                x=evo.loc[idx_max, "date"],
                y=evo.loc[idx_max, "Total"],
                text=f"📌 Pic : {evo.loc[idx_max, 'Total']}",
                showarrow=True, arrowhead=2,
                font=dict(color="#ff4444", size=11),
                bgcolor="#1a3a6b"
            )
        
        fig_evo.update_layout(
            title="Évolution quotidienne des délestages",
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"),
            legend=dict(bgcolor="#0d1f3c", bordercolor="#00d4ff"),
            height=350
        )
        fig_evo.update_yaxes(title_text="Total délestages", secondary_y=False,
                             gridcolor="#1a3a6b", color="white")
        fig_evo.update_yaxes(title_text="Quartiers uniques", secondary_y=True,
                             color="#ffd700")
        fig_evo.update_xaxes(gridcolor="#1a3a6b", color="white")
        st.plotly_chart(fig_evo, use_container_width=True)
    
    with col2:
        # Donut période
        periode_count = dff["Periode_Journee"].value_counts().reset_index()
        periode_count.columns = ["Période", "Count"]
        
        fig_donut = px.pie(
            periode_count, values="Count", names="Période",
            color="Période",
            color_discrete_map=COULEURS_PERIODE,
            hole=0.55,
            title="Répartition par période"
        )
        fig_donut.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"),
            legend=dict(bgcolor="#0d1f3c"),
            height=350,
            showlegend=True
        )
        fig_donut.update_traces(textinfo="percent", textfont_color="white")
        st.plotly_chart(fig_donut, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Top 10 quartiers
        top10 = dff["quartier"].value_counts().head(10).reset_index()
        top10.columns = ["Quartier", "Délestages"]
        
        fig_top = px.bar(
            top10.sort_values("Délestages"), x="Délestages", y="Quartier",
            orientation="h", title="Top 10 — Quartiers les plus touchés",
            color="Délestages",
            color_continuous_scale=["#0066ff", "#00d4ff", "#ffd700", "#ff4444"]
        )
        fig_top.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=320,
            coloraxis_showscale=False
        )
        fig_top.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_top.update_yaxes(color="white")
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col4:
        # Barres par semaine
        sem_data = dff.groupby("Semaine_mois").agg(
            Total=("quartier", "count"),
            Quartiers=("quartier", "nunique")
        ).reset_index()
        ordre_sem = ["S1 (1-7 fév)", "S2 (8-14 fév)", "S3 (15-21 fév)", "S4 (22-28 fév)"]
        sem_data["Semaine_mois"] = pd.Categorical(sem_data["Semaine_mois"], categories=ordre_sem, ordered=True)
        sem_data = sem_data.sort_values("Semaine_mois")
        
        fig_sem = make_subplots(specs=[[{"secondary_y": True}]])
        fig_sem.add_trace(
            go.Bar(x=sem_data["Semaine_mois"], y=sem_data["Total"],
                   name="Total", marker_color="#00d4ff", opacity=0.85),
            secondary_y=False
        )
        fig_sem.add_trace(
            go.Scatter(x=sem_data["Semaine_mois"], y=sem_data["Quartiers"],
                      name="Quartiers", line=dict(color="#ffd700", width=2),
                      mode="lines+markers+text",
                      text=sem_data["Quartiers"],
                      textposition="top center",
                      textfont=dict(color="#ffd700")),
            secondary_y=True
        )
        fig_sem.update_layout(
            title="Évolution par semaine du mois",
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=320,
            legend=dict(bgcolor="#0d1f3c")
        )
        fig_sem.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_sem.update_yaxes(gridcolor="#1a3a6b", color="white", secondary_y=False)
        fig_sem.update_yaxes(color="#ffd700", secondary_y=True)
        st.plotly_chart(fig_sem, use_container_width=True)

# ============================================================
# TAB 2 — VUE GÉOGRAPHIQUE
# ============================================================
with tab2:
    st.markdown("### 🗺️ Distribution géographique des délestages")
    
    geo_df = dff.dropna(subset=["latitude", "longitude"])
    
    # Agréger par quartier
    geo_agg = geo_df.groupby(["quartier", "latitude", "longitude"]).agg(
        Total=("quartier", "count"),
        Duree_Tot=("duree_minutes", "sum"),
        IPD=("ipd", "sum")
    ).reset_index()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Carte à bulles
        fig_map = px.scatter_mapbox(
            geo_agg,
            lat="latitude", lon="longitude",
            size="Total", color="IPD",
            hover_name="quartier",
            hover_data={"Total": True, "IPD": ":.1f", "Duree_Tot": True,
                       "latitude": False, "longitude": False},
            color_continuous_scale=["#00ff88", "#ffd700", "#ff8c00", "#ff4444"],
            size_max=40,
            zoom=11,
            center={"lat": 0.42, "lon": 9.45},
            mapbox_style="carto-darkmatter",
            title="Carte des délestages — Taille = fréquence | Couleur = IPD",
            labels={"Total": "Délestages", "IPD": "Indice IPD", "Duree_Tot": "Durée totale (min)"}
        )
        fig_map.update_layout(
            paper_bgcolor="#0a1628",
            font=dict(color="white"),
            height=480,
            coloraxis_colorbar=dict(
                title="IPD",
                tickfont=dict(color="white"),
                titlefont=dict(color="white")
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)
    
    with col2:
        # KPI carte
        top1 = geo_agg.nlargest(1, "Total").iloc[0]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a3a6b, #0d2348);
                    border: 2px solid #ff4444; border-radius: 12px; padding: 20px;
                    text-align: center; margin-bottom: 15px;">
            <p style="color: #a0c4ff; margin:0; font-size:12px;">🏆 QUARTIER LE PLUS TOUCHÉ</p>
            <p style="color: #ff4444; font-size: 24px; font-weight: bold; margin: 8px 0;">
                {top1['quartier']}
            </p>
            <p style="color: #ffd700; font-size: 32px; font-weight: bold; margin: 0;">
                {int(top1['Total'])} délestages
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Top 8 barres IPD
        top8_ipd = geo_agg.nlargest(8, "IPD")[["quartier", "IPD", "Total"]]
        
        fig_ipd_small = px.bar(
            top8_ipd.sort_values("IPD"),
            x="IPD", y="quartier", orientation="h",
            title="Top 8 — Indice IPD",
            color="IPD",
            color_continuous_scale=["#ffd700", "#ff8c00", "#ff4444"]
        )
        fig_ipd_small.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=300,
            coloraxis_showscale=False
        )
        fig_ipd_small.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_ipd_small.update_yaxes(color="white")
        st.plotly_chart(fig_ipd_small, use_container_width=True)
    
    # Tableau Top 15
    st.markdown("#### 📋 Top 15 quartiers — Détail complet")
    top15 = geo_agg.nlargest(15, "Total").copy()
    top15["Rang"] = range(1, 16)
    top15["Heures_Cumulées"] = (top15["Duree_Tot"] / 60).round(1)
    top15["IPD"] = top15["IPD"].round(1)
    top15 = top15[["Rang", "quartier", "Total", "IPD", "Heures_Cumulées"]].rename(
        columns={"quartier": "Quartier", "Total": "Délestages"}
    )
    st.dataframe(
        top15.style.background_gradient(subset=["Délestages", "IPD"], cmap="RdYlGn_r"),
        use_container_width=True, hide_index=True
    )

# ============================================================
# TAB 3 — VUE TEMPORELLE
# ============================================================
with tab3:
    st.markdown("### ⏱️ Analyse temporelle — Quand frappe le délestage ?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Heatmap heure × jour
        heat_df = dff.groupby(["heure_debut", "Jour_Semaine", "Num_Jour"]).size().reset_index(name="count")
        ordre_jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        heat_pivot = heat_df.pivot_table(
            index="heure_debut", columns="Jour_Semaine", values="count", fill_value=0
        )
        # Réordonner colonnes
        cols_present = [j for j in ordre_jours if j in heat_pivot.columns]
        heat_pivot = heat_pivot[cols_present]
        
        fig_heat = px.imshow(
            heat_pivot,
            color_continuous_scale=["#0d1f3c", "#0066ff", "#00d4ff", "#ffd700", "#ff4444"],
            title="Heatmap — Heure × Jour de la semaine",
            labels=dict(x="Jour", y="Heure début", color="Nb délestages"),
            aspect="auto"
        )
        fig_heat.update_layout(
            paper_bgcolor="#0a1628", font=dict(color="white"),
            height=420,
            coloraxis_colorbar=dict(tickfont=dict(color="white"), titlefont=dict(color="white"))
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    
    with col2:
        # Histogramme Top tranches horaires
        heure_count = dff["heure_debut"].value_counts().head(15).reset_index()
        heure_count.columns = ["Heure", "Count"]
        
        fig_heure = px.bar(
            heure_count.sort_values("Count"),
            x="Count", y="Heure", orientation="h",
            title="Top 15 tranches horaires",
            color="Count",
            color_continuous_scale=["#0066ff", "#00d4ff", "#ffd700", "#ff4444"]
        )
        fig_heure.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=420,
            coloraxis_showscale=False
        )
        fig_heure.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_heure.update_yaxes(color="white")
        st.plotly_chart(fig_heure, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Courbe par jour de semaine
        jour_data = dff.groupby(["Jour_Semaine", "Num_Jour"]).size().reset_index(name="Total")
        jour_data = jour_data.sort_values("Num_Jour")
        
        fig_jour = px.line(
            jour_data, x="Jour_Semaine", y="Total",
            title="Délestages par jour de la semaine",
            markers=True,
            line_shape="spline"
        )
        fig_jour.update_traces(
            line=dict(color="#00d4ff", width=3),
            marker=dict(size=10, color="#ffd700", line=dict(color="#ff4444", width=2))
        )
        fig_jour.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=300
        )
        fig_jour.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_jour.update_yaxes(gridcolor="#1a3a6b", color="white")
        st.plotly_chart(fig_jour, use_container_width=True)
    
    with col4:
        # Durée moyenne par période
        duree_periode = dff.groupby("Periode_Journee")["duree_minutes"].agg(["mean", "min", "max"]).reset_index()
        duree_periode.columns = ["Période", "Moyenne", "Min", "Max"]
        
        fig_duree = go.Figure()
        fig_duree.add_trace(go.Bar(
            x=duree_periode["Période"],
            y=duree_periode["Moyenne"],
            name="Durée moyenne",
            marker_color=[COULEURS_PERIODE.get(p, "#00d4ff") for p in duree_periode["Période"]],
            text=duree_periode["Moyenne"].round(0).astype(int).astype(str) + " min",
            textposition="outside", textfont=dict(color="white")
        ))
        fig_duree.add_hline(y=120, line_dash="dash", line_color="#ffffff",
                           annotation_text="Référence 120 min",
                           annotation_font_color="white")
        fig_duree.update_layout(
            title="Durée moyenne par période (minutes)",
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=300,
            showlegend=False
        )
        fig_duree.update_xaxes(color="white")
        fig_duree.update_yaxes(gridcolor="#1a3a6b", color="white", range=[0, 150])
        st.plotly_chart(fig_duree, use_container_width=True)

# ============================================================
# TAB 4 — CLASSEMENT IPD
# ============================================================
with tab4:
    st.markdown("### 🏆 Classement IPD — Indice de Pénalisation par Délestage")
    
    st.info("""
    **L'IPD (Indice de Pénalisation par Délestage)** pondère chaque délestage selon son impact réel sur les habitants :
    Soirée × 3 | Après-midi × 2 | Matin × 1,5 | Nuit × 1
    """)
    
    # Calculer IPD par quartier
    ipd_df = dff.groupby("quartier").agg(
        Total=("quartier", "count"),
        IPD=("ipd", "sum"),
        Heures=("duree_minutes", lambda x: x.sum() / 60),
        Jours=("date", "nunique")
    ).reset_index()
    ipd_df["Taux_Presence"] = (ipd_df["Jours"] / 25 * 100).round(1)
    ipd_df["IPD"] = ipd_df["IPD"].round(1)
    ipd_df["Heures"] = ipd_df["Heures"].round(1)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Barres Top 20 IPD
        top20 = ipd_df.nlargest(20, "IPD")
        
        fig_ipd = px.bar(
            top20.sort_values("IPD"),
            x="IPD", y="quartier", orientation="h",
            title="Top 20 — Classement IPD",
            color="IPD",
            color_continuous_scale=["#ffd700", "#ff8c00", "#ff4444", "#cc0000"],
            text="IPD"
        )
        fig_ipd.update_traces(texttemplate="%{text:.0f}", textposition="outside",
                              textfont=dict(color="white"))
        fig_ipd.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=550,
            coloraxis_showscale=False
        )
        fig_ipd.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_ipd.update_yaxes(color="white")
        st.plotly_chart(fig_ipd, use_container_width=True)
    
    with col2:
        # Scatter plot 4 quadrants
        med_total = ipd_df["Total"].median()
        med_ipd = ipd_df["IPD"].median()
        
        fig_scatter = px.scatter(
            ipd_df.nlargest(50, "Total"),
            x="Total", y="IPD",
            size="Heures", color="IPD",
            hover_name="quartier",
            color_continuous_scale=["#00ff88", "#ffd700", "#ff4444"],
            title="Fréquence vs Impact (Top 50)",
            labels={"Total": "Nombre de délestages", "IPD": "Indice IPD"},
            size_max=25
        )
        # Lignes des quadrants
        fig_scatter.add_vline(x=med_total, line_dash="dash",
                             line_color="#ffffff", opacity=0.4)
        fig_scatter.add_hline(y=med_ipd, line_dash="dash",
                             line_color="#ffffff", opacity=0.4)
        fig_scatter.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=330,
            coloraxis_showscale=False
        )
        fig_scatter.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_scatter.update_yaxes(gridcolor="#1a3a6b", color="white")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Barres heures cumulées Top 10
        top10h = ipd_df.nlargest(10, "Heures")[["quartier", "Heures"]].sort_values("Heures")
        
        fig_h = px.bar(
            top10h, x="Heures", y="quartier", orientation="h",
            title="Top 10 — Heures cumulées sans électricité",
            color="Heures",
            color_continuous_scale=["#0066ff", "#ff8c00", "#ff4444"],
            text="Heures"
        )
        fig_h.update_traces(texttemplate="%{text:.0f}h", textposition="outside",
                           textfont=dict(color="white"))
        fig_h.update_layout(
            plot_bgcolor="#0d1f3c", paper_bgcolor="#0a1628",
            font=dict(color="white"), height=320,
            coloraxis_showscale=False
        )
        fig_h.update_xaxes(gridcolor="#1a3a6b", color="white")
        fig_h.update_yaxes(color="white")
        st.plotly_chart(fig_h, use_container_width=True)
    
    # Tableau complet Top 30
    st.markdown("#### 📋 Tableau complet — Top 30")
    top30 = ipd_df.nlargest(30, "IPD").copy()
    top30.insert(0, "Rang", range(1, 31))
    top30 = top30.rename(columns={
        "quartier": "Quartier", "Total": "Délestages",
        "Heures": "Heures Cumulées", "Jours": "Jours Touchés"
    })
    
    st.dataframe(
        top30[["Rang", "Quartier", "Délestages", "IPD", "Heures Cumulées",
               "Jours Touchés", "Taux_Presence"]].style
        .background_gradient(subset=["IPD", "Délestages"], cmap="RdYlGn_r")
        .format({"IPD": "{:.1f}", "Heures Cumulées": "{:.1f}h", "Taux_Presence": "{:.0f}%"}),
        use_container_width=True, hide_index=True
    )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0c4ff; font-size: 12px; padding: 10px;">
    📊 Analyse des délestages SEEG — Grand Libreville | Février 2026<br>
    Données : Plannings officiels publiés sur les canaux SEEG | Méthodologie : OCR → Python → Géocodage OSM<br>
    <strong style="color: #00d4ff;">© 2026 — Tous droits réservés</strong>
</div>
""", unsafe_allow_html=True)
