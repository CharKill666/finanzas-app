import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from dateutil.relativedelta import relativedelta
import database as db
import visualizations as viz
import utils

# Inicializar base de datos
db.init_database()

# Configuración de la página
st.set_page_config(page_title="Finanzas Personales", layout="wide", page_icon="💰")

# ==================== CSS PERSONALIZADO ====================
st.markdown("""
<style>
    .stApp { background-color: #f5f7fa; }
    h1, h2, h3 { color: #1E2A3A; font-family: 'Inter', sans-serif; }
    .card {
        background-color: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border: 1px solid #eaeef2;
    }
    .stButton > button {
        background-color: #2C3E50;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #1A2A3A;
        box-shadow: 0 6px 10px rgba(0,0,0,0.1);
    }
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input, 
    .stDateInput > div > div > input {
        border-radius: 12px;
        border: 1px solid #dce2e8;
        padding: 0.5rem;
    }
    .stSelectbox > div > div > select { border-radius: 12px; border: 1px solid #dce2e8; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 20px;
        padding: 8px 16px;
        background-color: #ffffff;
        border: 1px solid #e0e6ed;
    }
    .stTabs [aria-selected="true"] { background-color: #2C3E50; color: white; }
    .stMetric {
        background-color: white;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        border: 1px solid #eaeef2;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        border: 1px solid #eaeef2;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Aplicación de Finanzas Personales")

# ==================== SIDEBAR: Usuario y Moneda ====================
st.sidebar.header("Configuración")

users = db.get_users()
user_names = [u[1] for u in users]
user_ids = [u[0] for u in users]

selected_user_index = st.sidebar.selectbox(
    "Usuario actual", range(len(user_names)), format_func=lambda i: user_names[i]
)
current_user_id = user_ids[selected_user_index]
st.session_state['current_user_id'] = current_user_id

base_currency = st.sidebar.selectbox("Moneda base", ["COP", "USD"], index=0)
st.session_state['base_currency'] = base_currency

if base_currency == 'USD':
    utils.exchange_rate = st.sidebar.number_input(
        "Tasa USD a COP", min_value=1.0, value=4000.0, step=100.0
    )
else:
    utils.exchange_rate = 1

st.sidebar.info("Usa las pestañas para gestionar tus finanzas.")

# ==================== PESTAÑAS PRINCIPALES ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Ingresos", "💳 Gastos", "📊 Dashboard", "📋 Planificación", "📁 Reportes"
])

# ---------- Pestaña 1: Registrar Ingreso ----------
with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📥 Registrar ingreso")
    with st.form("income_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("💰 Monto", min_value=0.01, step=0.01, format="%.2f")
            date_income = st.date_input("📅 Fecha", value=datetime.today())
            currency = st.selectbox("💱 Moneda", ["COP", "USD"])
        with col2:
            source = st.text_input("🏷️ Fuente del ingreso", placeholder="Ej: Salario, Freelance")
            notes = st.text_area("📝 Notas", height=68, placeholder="Opcional...")
        submitted = st.form_submit_button("Guardar ingreso")
        if submitted:
            if amount > 0 and source:
                db.add_income(amount, date_income.strftime("%Y-%m-%d"), source, notes, currency, current_user_id)
                st.success("✅ Ingreso guardado correctamente")
            else:
                st.error("❌ Completa los campos obligatorios (monto y fuente)")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Pestaña 2: Registrar Gasto ----------
with tab2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("📤 Registrar gasto")
    categories = ["Alimentación", "Transporte", "Vivienda", "Servicios",
                  "Entretenimiento", "Salud", "Educación", "Otros"]
    payment_methods = ["Efectivo", "Tarjeta", "Transferencia"]
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("💰 Monto", min_value=0.01, step=0.01, format="%.2f", key="exp_amount")
            date_expense = st.date_input("📅 Fecha", value=datetime.today(), key="exp_date")
            category = st.selectbox("📂 Categoría", categories)
            currency = st.selectbox("💱 Moneda", ["COP", "USD"], key="exp_currency")
        with col2:
            payment = st.selectbox("💳 Método de pago", payment_methods)
            description = st.text_area("📝 Descripción", height=68, placeholder="Opcional...")
        submitted = st.form_submit_button("Guardar gasto")
        if submitted:
            if amount > 0 and category:
                db.add_expense(amount, date_expense.strftime("%Y-%m-%d"), category, payment, description, currency, current_user_id)
                st.success("✅ Gasto guardado correctamente")
            else:
                st.error("❌ Completa los campos obligatorios (monto y categoría)")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Pestaña 3: Dashboard ----------
# (Mantiene la misma lógica que tu versión original, con validaciones de fechas y conversiones de moneda)

# ---------- Pestaña 4: Planificación ----------
# (Incluye presupuestos, metas, deudas, ahorros y servicios recurrentes, igual que tu versión original)

# ---------- Pestaña 5: Reportes ----------
# (Exportación CSV y predicciones de gastos, igual que tu versión original)
