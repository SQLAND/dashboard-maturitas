import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Dashboard Maturitas Risiko",
    layout="wide"
)

# =========================
# GLOBAL STYLE
# =========================
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top, #0B1220 0%, #0E1117 45%, #05070A 100%);
        color: #FFFFFF;
    }

    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetric"] {
        background: transparent;
        padding: 10px 0px;
    }

    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800;
    }

    .dashboard-title {
        text-align: center;
        font-size: 42px;
        font-weight: 900;
        color: white;
        margin-top: 10px;
        margin-bottom: 2px;
    }

    .dashboard-subtitle {
        text-align: center;
        color: #CBD5E1;
        font-size: 15px;
        margin-bottom: 28px;
    }

    .running-wrapper {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        border: 1px solid #1E90FF;
        border-radius: 8px;
        padding: 8px 0;
        margin-top: -8px;
        margin-bottom: 22px;
        box-shadow: 0 0 12px #1E90FF;
        background: rgba(15, 23, 42, 0.65);
    }

    .running-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 14s linear infinite;
        font-size: 21px;
        font-weight: 900;
        color: #49B8FF;
        text-shadow:
            0 0 4px #CFE8FF,
            0 0 8px #7EC8FF,
            0 0 14px #1E90FF;
    }

    @keyframes marquee {
        0%   { transform: translateX(0%); }
        100% { transform: translateX(-100%); }
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        overflow: hidden;
    }

    .section-card {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 0 20px rgba(15, 23, 42, 0.35);
    }
</style>
""", unsafe_allow_html=True)

# =========================
# LOGO HEADER
# =========================
logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
with logo_col2:
    st.image("logo.png", use_container_width=True)

# =========================
# RUNNING TEXT
# =========================
st.markdown("""
<div class="running-wrapper">
    <div class="running-text">
        SMART CAMPUS TO DRIVE INNOVATION &nbsp;&nbsp; • &nbsp;&nbsp;
        SMART CAMPUS TO DRIVE INNOVATION &nbsp;&nbsp; • &nbsp;&nbsp;
        SMART CAMPUS TO DRIVE INNOVATION
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# GOOGLE SHEETS CONNECTION
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = {
    "type": st.secrets["gcp_service_account"]["type"],
    "project_id": st.secrets["gcp_service_account"]["project_id"],
    "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
    "private_key": st.secrets["gcp_service_account"]["private_key"],
    "client_email": st.secrets["gcp_service_account"]["client_email"],
    "client_id": st.secrets["gcp_service_account"]["client_id"],
    "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
    "token_uri": st.secrets["gcp_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gcp_service_account"]["universe_domain"]
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    service_account_info,
    scope
)

client = gspread.authorize(creds)
sheet = client.open(
    "KKE PM Maturitas MR BLU Poltekkes Kemenkes Manado 2026"
).worksheet("Dashboard_Data")

data = sheet.get_all_records(numericise_ignore=["all"])
df = pd.DataFrame(data)
df.columns = df.columns.str.strip()

# =========================
# HELPER FUNCTIONS
# =========================
def angka_id(x):
    if pd.isna(x):
        return None

    x = str(x).strip()

    if x == "" or x.lower() == "none":
        return None

    x = x.replace("%", "")
    x = x.replace(".", "")
    x = x.replace(",", ".")

    return pd.to_numeric(x, errors="coerce")


# =========================
# CLEAN DATA
# =========================
numeric_cols = [
    "BOBOT",
    "BOBOT_THD_ASPEK",
    "SKOR_MAKSIMAL_ASPEK",
    "SKORMAKS_PARAMETER",
    "NILAI",
    "Nilai_Parameter",
    "Nilai_Indikator",
    "Nilai_Aspek",
    "CAPAIAN"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].apply(angka_id)

for col in ["ASPEK", "INDIKATOR"]:
    if col in df.columns:
        df[col] = df[col].replace("", pd.NA).ffill()

df["PARAMETER"] = df["PARAMETER"].astype(str).str.strip()

df = df[
    (df["PARAMETER"].notna()) &
    (df["PARAMETER"] != "") &
    (df["PARAMETER"].str.lower() != "none")
].copy()

df = df.reset_index(drop=True)

# =========================
# TOTAL MATURITAS
# =========================
aspek_score_df = (
    df[["ASPEK", "SKOR_MAKSIMAL_ASPEK", "Nilai_Aspek"]]
    .dropna(subset=["ASPEK", "SKOR_MAKSIMAL_ASPEK", "Nilai_Aspek"])
    .drop_duplicates(subset=["ASPEK"])
    .copy()
)

aspek_score_df = aspek_score_df.round(2)

total_maksimal = 5
total_aktual = aspek_score_df["Nilai_Aspek"].sum()
capaian_total = (total_aktual / total_maksimal) * 100 if total_maksimal else 0

bobot_aspek_df = pd.DataFrame({
    "ASPEK": ["PERENCANAAN", "KAPABILITAS", "HASIL"],
    "BOBOT": [40, 30, 30]
})

# =========================
# HEADER TITLE
# =========================
st.markdown("""
<div class="dashboard-title">
    Dashboard Maturitas Manajemen Risiko
</div>
<div class="dashboard-subtitle">
    BLU Poltekkes Kemenkes Manado - Tahun Penilaian 2026
</div>
""", unsafe_allow_html=True)

# =========================
# KPI UTAMA
# =========================
kpi1, kpi2, kpi3 = st.columns(3)

kpi1.metric("Nilai Maturitas Aktual", f"{total_aktual:.2f} / 5")
kpi2.metric("Skor Maksimal", "5.00")
kpi3.metric("Capaian Total", f"{capaian_total:.2f}%")

# =========================
# MAIN VISUAL ROW
# =========================
col_gauge, col_pie, col_progress = st.columns(3)

# LEVEL MATURITAS
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=total_aktual,
    number={"suffix": " / 5", "font": {"color": "white", "size": 54}},
    title={"text": "LEVEL MATURITAS PENERAPAN MR BLU", "font": {"color": "white", "size": 16}},
    gauge={
        "axis": {
            "range": [1, 5],
            "tickvals": [1, 2, 3, 4, 5],
            "ticktext": ["1", "2", "3", "4", "5"],
            "tickfont": {"color": "white"}
        },
        "bar": {"color": "#111111", "thickness": 0.15},
        "steps": [
            {"range": [1, 2], "color": "#ff4b4b"},
            {"range": [2, 3], "color": "#ffa500"},
            {"range": [3, 4], "color": "#ffd700"},
            {"range": [4, 5], "color": "#2ecc71"},
        ],
        "threshold": {
            "line": {"color": "white", "width": 5},
            "thickness": 0.85,
            "value": total_aktual
        }
    }
))

gauge.update_layout(
    height=380,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=60, b=20),
    font=dict(color="white")
)

with col_gauge:
    st.plotly_chart(gauge, use_container_width=True)

# PIE BOBOT
pie_bobot = px.pie(
    bobot_aspek_df,
    names="ASPEK",
    values="BOBOT",
    hole=0.45,
    title="Distribusi Bobot Aspek"
)

pie_bobot.update_traces(
    textinfo="label+percent",
    textposition="inside"
)

pie_bobot.update_layout(
    height=380,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=60, b=20),
    font=dict(color="white"),
    title_font=dict(color="white")
)

with col_pie:
    st.plotly_chart(pie_bobot, use_container_width=True)

# CAPAIAN PER ASPEK
capaian_aspek_df = (
    df[["ASPEK", "CAPAIAN"]]
    .dropna(subset=["ASPEK", "CAPAIAN"])
    .drop_duplicates(subset=["ASPEK"])
    .copy()
)

capaian_aspek_df["CAPAIAN"] = capaian_aspek_df["CAPAIAN"].round(2)
capaian_aspek_df = capaian_aspek_df.sort_values("CAPAIAN", ascending=True)

warna_bar = []

for nilai in capaian_aspek_df["CAPAIAN"]:
    if nilai < 60:
        warna_bar.append("#FF4D4D")   # Merah terang
    elif nilai <= 80:
        warna_bar.append("#FFD43B")   # Kuning emas
    else:
        warna_bar.append("#00C853")   # Hijau terang

fig_progress = go.Figure()

fig_progress.add_trace(go.Bar(
    x=capaian_aspek_df["CAPAIAN"],
    y=capaian_aspek_df["ASPEK"],
    orientation="h",
    text=[f"{x:.2f}%" for x in capaian_aspek_df["CAPAIAN"]],
    textposition="outside",
    marker=dict(color=warna_bar)
))

fig_progress.update_layout(
    title="Progress Capaian per Aspek",
    xaxis=dict(
        title="Capaian (%)",
        range=[0, 105],
        color="white"
    ),
    yaxis=dict(
        title="",
        color="white"
    ),
    height=380,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=80, t=60, b=20),
    font=dict(color="white"),
    title_font=dict(color="white")
)

with col_progress:
    st.plotly_chart(fig_progress, use_container_width=True)

# =========================
# LOWER ROW
# =========================
left_bottom, right_bottom = st.columns([1, 2])

with left_bottom:
    st.subheader("Ringkasan Nilai per Aspek")
    st.dataframe(
        aspek_score_df,
        use_container_width=True,
        hide_index=True
    )

with right_bottom:
    st.subheader("Detail per Aspek")

    aspek_options = sorted(df["ASPEK"].dropna().unique())

    aspek_pilihan = st.selectbox(
        "Pilih Aspek",
        options=aspek_options
    )

    detail_aspek = df[df["ASPEK"] == aspek_pilihan].copy()

    ringkasan_aspek = (
        detail_aspek[["ASPEK", "SKOR_MAKSIMAL_ASPEK", "Nilai_Aspek", "CAPAIAN"]]
        .dropna(subset=["ASPEK"])
        .drop_duplicates(subset=["ASPEK"])
    )

    if not ringkasan_aspek.empty:
        skor_maks_aspek = ringkasan_aspek["SKOR_MAKSIMAL_ASPEK"].iloc[0]
        nilai_aspek = ringkasan_aspek["Nilai_Aspek"].iloc[0]
        capaian_aspek = ringkasan_aspek["CAPAIAN"].iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Skor Maksimal Aspek", f"{skor_maks_aspek:.2f}")
        c2.metric("Nilai Aktual Aspek", f"{nilai_aspek:.2f}")
        c3.metric("Capaian Aspek", f"{capaian_aspek:.2f}%")

    kolom_detail_tampil = [
        "INDIKATOR",
        "PARAMETER",
        "BOBOT_THD_ASPEK",
        "SKOR_MAKSIMAL_ASPEK",
        "SKORMAKS_PARAMETER",
        "NILAI",
        "Nilai_Parameter"
    ]

    available_cols = [col for col in kolom_detail_tampil if col in detail_aspek.columns]
    detail_tampil = detail_aspek[available_cols].copy()
    detail_tampil = detail_tampil.round(2)

    indikator_unik = detail_tampil["INDIKATOR"].dropna().unique()

    palette_indikator = [
        "#FADBD8",
        "#FDEBD0",
        "#FCF3CF",
        "#D5F5E3",
        "#D6EAF8",
        "#E8DAEF",
        "#D1F2EB",
        "#F9E79F",
        "#F5CBA7",
        "#D7BDE2",
    ]

    warna_per_indikator = {
        indikator: palette_indikator[i % len(palette_indikator)]
        for i, indikator in enumerate(indikator_unik)
    }

    def style_by_indikator(row):
        indikator = row["INDIKATOR"]
        bg = warna_per_indikator.get(indikator, "#F5F5F5")
        return [f"background-color: {bg}; color: #111111;" for _ in row]

    styled_table = detail_tampil.style.apply(style_by_indikator, axis=1)

    st.dataframe(
        styled_table,
        use_container_width=True,
        hide_index=True,
        height=360
    )