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

# Selector de usuario (colaboración)
users = db.get_users()
user_names = [u[1] for u in users]
user_ids = [u[0] for u in users]
selected_user_index = st.sidebar.selectbox("Usuario actual", range(len(user_names)), format_func=lambda i: user_names[i])
current_user_id = user_ids[selected_user_index]
st.session_state['current_user_id'] = current_user_id

# Selector de moneda base
base_currency = st.sidebar.selectbox("Moneda base", ["COP", "USD"], index=0)
st.session_state['base_currency'] = base_currency

# Tasa de cambio (si base es USD, permitir ajustar)
if base_currency == 'USD':
    utils.exchange_rate = st.sidebar.number_input("Tasa USD a COP", min_value=1.0, value=4000.0, step=100.0)
else:
    utils.exchange_rate = 1  # No se usa si base es COP, pero dejamos consistencia

st.sidebar.info("Usa las pestañas para gestionar tus finanzas.")

# ==================== PESTAÑAS PRINCIPALES ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Ingresos", "💳 Gastos", "📊 Dashboard", "📋 Planificación", "📁 Reportes"])

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
with tab3:
    st.header("📊 Dashboard Financiero")

    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicial", value=date(datetime.today().year, 1, 1))
    with col2:
        end_date = st.date_input("Fecha final", value=datetime.today())

    if start_date > end_date:
        st.error("La fecha inicial debe ser anterior a la final")
    else:
        # Obtener datos filtrados del usuario actual
        df_income, df_expenses = db.get_combined_data(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            user_id=current_user_id
        )

        # Convertir monedas a la base seleccionada
        if not df_income.empty:
            df_income['amount'] = df_income.apply(
                lambda row: utils.convert_currency(row['amount'], row['currency'], base_currency), axis=1)
        if not df_expenses.empty:
            df_expenses['amount'] = df_expenses.apply(
                lambda row: utils.convert_currency(row['amount'], row['currency'], base_currency), axis=1)

        # Mostrar alerta de gastos
        alert = utils.spending_alert(df_income, df_expenses)
        if alert:
            st.warning(alert)

        # Métricas rápidas
        total_income = df_income['amount'].sum() if not df_income.empty else 0
        total_expenses = df_expenses['amount'].sum() if not df_expenses.empty else 0
        balance = total_income - total_expenses

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"💰 Ingresos totales ({base_currency})", f"{base_currency} {total_income:,.2f}")
        with col2:
            st.metric(f"💸 Gastos totales ({base_currency})", f"{base_currency} {total_expenses:,.2f}")
        with col3:
            st.metric(f"📊 Balance ({base_currency})", f"{base_currency} {balance:,.2f}")

        # Gráfico 1: Comparativa Ingresos vs Gastos
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Comparativa Ingresos vs Gastos")
        fig1 = viz.bar_income_vs_expenses(df_income, df_expenses)
        st.plotly_chart(fig1, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

        # Dos gráficos en columnas
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("🥧 Distribución por Categoría")
            fig2 = viz.pie_expenses_by_category(df_expenses)
            st.plotly_chart(fig2, width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📈 Evolución del Ahorro")
            fig3 = viz.line_cumulative_balance(df_income, df_expenses)
            st.plotly_chart(fig3, width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)

        # Gráfico de barras apiladas
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Gastos Mensuales por Categoría")
        fig4 = viz.stacked_bar_expenses_by_month(df_expenses)
        st.plotly_chart(fig4, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

        # Heatmap
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔥 Heatmap de Gastos Diarios")
        col1, col2 = st.columns(2)
        with col1:
            year_heat = st.number_input("Año", min_value=2000, max_value=2100, value=datetime.today().year)
        with col2:
            month_heat = st.selectbox("Mes", range(1,13), format_func=lambda x: calendar.month_name[x])
        fig5 = viz.heatmap_daily_expenses(df_expenses, year_heat, month_heat)
        st.plotly_chart(fig5, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Pestaña 4: Planificación ----------
with tab4:
    st.header("📋 Planificación Financiera")
    plan_tabs = st.tabs(["Presupuestos", "Metas", "Deudas", "Ahorros", "Servicios"])

    # --- Presupuestos ---
    with plan_tabs[0]:
        st.subheader("Establecer presupuestos mensuales")
        with st.form("budget_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                budget_month = st.date_input("Mes", value=datetime.today(), format="YYYY-MM")
                budget_month_str = budget_month.strftime("%Y-%m")
            with col2:
                budget_category = st.selectbox("Categoría", categories)
            with col3:
                budget_amount = st.number_input("Límite", min_value=0.0, step=1000.0)
            submitted = st.form_submit_button("Guardar presupuesto")
            if submitted:
                db.set_budget(current_user_id, budget_category, budget_month_str, budget_amount, base_currency)
                st.success("Presupuesto guardado")

        budgets_df = db.get_budgets(current_user_id)
        if not budgets_df.empty:
            st.dataframe(budgets_df)
        else:
            st.info("No hay presupuestos definidos.")

        # Alertas de presupuesto del mes actual
        today = datetime.today()
        current_month = today.strftime("%Y-%m")
        df_income, df_expenses = db.get_combined_data(user_id=current_user_id)
        # Convertir monedas para la comparación (presupuestos ya están en base_currency)
        if not df_expenses.empty:
            df_expenses['amount'] = df_expenses.apply(
                lambda row: utils.convert_currency(row['amount'], row['currency'], base_currency), axis=1)
        alerts = utils.check_budget_alerts(current_user_id, df_expenses, budgets_df, current_month)
        if alerts:
            for alert in alerts:
                st.warning(alert)

    # --- Metas ---
    with plan_tabs[1]:
        st.subheader("Metas de ahorro")
        with st.form("goal_form"):
            col1, col2 = st.columns(2)
            with col1:
                goal_name = st.text_input("Nombre de la meta")
                goal_target = st.number_input("Monto objetivo", min_value=0.0, step=10000.0)
            with col2:
                goal_current = st.number_input("Monto actual", min_value=0.0, step=1000.0, value=0.0)
                goal_date = st.date_input("Fecha objetivo", value=None)
            submitted = st.form_submit_button("Crear meta")
            if submitted:
                db.add_goal(current_user_id, goal_name, goal_target, goal_current,
                            goal_date.strftime("%Y-%m-%d") if goal_date else None, base_currency)
                st.success("Meta creada")

        goals_df = db.get_goals(current_user_id)
        if not goals_df.empty:
            goals_df = utils.calculate_savings_progress(goals_df)
            for _, goal in goals_df.iterrows():
                st.metric(f"{goal['name']} - {goal['progress']:.1f}%",
                          f"{goal['current_amount']:,.2f} / {goal['target_amount']:,.2f} {base_currency}")
                st.progress(min(goal['progress']/100, 1.0))
        else:
            st.info("No hay metas definidas.")

    # --- Deudas ---
    with plan_tabs[2]:
        st.subheader("Deudas")
        with st.form("debt_form"):
            col1, col2 = st.columns(2)
            with col1:
                debt_name = st.text_input("Nombre de la deuda")
                debt_total = st.number_input("Monto total", min_value=0.0, step=10000.0)
                debt_remaining = st.number_input("Monto restante", min_value=0.0, step=1000.0, value=debt_total)
            with col2:
                debt_interest = st.number_input("Tasa de interés (%)", min_value=0.0, step=0.1, value=0.0)
                debt_due = st.date_input("Fecha de vencimiento", value=None)
                debt_currency = st.selectbox("Moneda", ["COP", "USD"])
            debt_notes = st.text_area("Notas")
            submitted = st.form_submit_button("Registrar deuda")
            if submitted:
                db.add_debt(current_user_id, debt_name, debt_total, debt_remaining, debt_interest,
                            debt_due.strftime("%Y-%m-%d") if debt_due else None, debt_currency, debt_notes)
                st.success("Deuda registrada")

        debts_df = db.get_debts(current_user_id)
        if not debts_df.empty:
            # Convertir montos a base_currency para mostrar
            debts_display = debts_df.copy()
            if base_currency != 'COP':
                debts_display['remaining_amount'] = debts_display.apply(
                    lambda row: utils.convert_currency(row['remaining_amount'], row['currency'], base_currency), axis=1)
                debts_display['total_amount'] = debts_display.apply(
                    lambda row: utils.convert_currency(row['total_amount'], row['currency'], base_currency), axis=1)
            st.dataframe(debts_display[['name', 'total_amount', 'remaining_amount', 'interest_rate', 'due_date']])

            # Sección para pagos
            st.subheader("Registrar pago de deuda")
            debt_options = {row['id']: f"{row['name']} (restante: {row['remaining_amount']} {row['currency']})" for _, row in debts_df.iterrows()}
            selected_debt = st.selectbox("Seleccionar deuda", options=list(debt_options.keys()),
                                         format_func=lambda x: debt_options[x])
            with st.form("payment_form"):
                payment_amount = st.number_input("Monto del pago", min_value=0.01, step=1000.0)
                payment_date = st.date_input("Fecha", value=datetime.today())
                payment_notes = st.text_input("Notas")
                if st.form_submit_button("Registrar pago"):
                    # El pago se registra en la moneda original de la deuda
                    debt_currency = debts_df[debts_df['id'] == selected_debt].iloc[0]['currency']
                    # Opcional: convertir si el usuario ingresa en otra moneda? Por simplicidad asumimos misma moneda.
                    db.add_debt_payment(selected_debt, payment_amount, payment_date.strftime("%Y-%m-%d"), payment_notes)
                    st.success("Pago registrado")
                    st.rerun()
        else:
            st.info("No hay deudas registradas.")

    # --- Ahorros ---
    with plan_tabs[3]:
        st.subheader("Cuentas de ahorro")
        with st.form("saving_form"):
            saving_name = st.text_input("Nombre de la cuenta")
            saving_balance = st.number_input("Saldo actual", min_value=0.0, step=1000.0, value=0.0)
            saving_currency = st.selectbox("Moneda", ["COP", "USD"])
            saving_notes = st.text_area("Notas")
            submitted = st.form_submit_button("Añadir cuenta")
            if submitted:
                db.add_saving(current_user_id, saving_name, saving_balance, saving_currency, saving_notes)
                st.success("Cuenta añadida")

        savings_df = db.get_savings(current_user_id)
        if not savings_df.empty:
            # Mostrar en base_currency
            savings_display = savings_df.copy()
            if base_currency != 'COP':
                savings_display['balance'] = savings_display.apply(
                    lambda row: utils.convert_currency(row['balance'], row['currency'], base_currency), axis=1)
            st.dataframe(savings_display[['name', 'balance', 'currency', 'notes']])

            # Opción para actualizar saldo
            saving_options = {row['id']: row['name'] for _, row in savings_df.iterrows()}
            selected_saving = st.selectbox("Seleccionar cuenta para actualizar", options=list(saving_options.keys()),
                                           format_func=lambda x: saving_options[x])
            new_balance = st.number_input("Nuevo saldo", min_value=0.0, step=1000.0)
            if st.button("Actualizar saldo"):
                db.update_saving_balance(selected_saving, new_balance)
                st.success("Saldo actualizado")
                st.rerun()
        else:
            st.info("No hay cuentas de ahorro.")

    # --- Servicios recurrentes ---
    with plan_tabs[4]:
        st.subheader("Servicios recurrentes")
        with st.form("service_form"):
            col1, col2 = st.columns(2)
            with col1:
                service_name = st.text_input("Nombre del servicio")
                service_amount = st.number_input("Monto", min_value=0.01, step=1000.0)
                service_currency = st.selectbox("Moneda", ["COP", "USD"])
            with col2:
                service_freq = st.selectbox("Frecuencia", ["Mensual", "Anual"])
                service_date = st.date_input("Próximo vencimiento", value=datetime.today())
                service_category = st.selectbox("Categoría", categories + ["Servicios"])
            service_notes = st.text_area("Notas")
            submitted = st.form_submit_button("Añadir servicio")
            if submitted:
                freq_map = {"Mensual": "monthly", "Anual": "yearly"}
                db.add_recurring_service(current_user_id, service_name, service_amount, service_currency,
                                         freq_map[service_freq], service_date.strftime("%Y-%m-%d"),
                                         service_category, service_notes)
                st.success("Servicio añadido")

        services_df = db.get_recurring_services(current_user_id)
        if not services_df.empty:
            # Mostrar próximos vencimientos
            st.dataframe(services_df[['name', 'amount', 'currency', 'frequency', 'next_due_date', 'category']])
            # Botón para marcar como pagado
            service_options = {row['id']: f"{row['name']} - {row['next_due_date']}" for _, row in services_df.iterrows()}
            selected_service = st.selectbox("Seleccionar servicio pagado", options=list(service_options.keys()),
                                            format_func=lambda x: service_options[x])
            if st.button("Registrar pago y actualizar fecha"):
                service = services_df[services_df['id'] == selected_service].iloc[0]
                current_date = datetime.strptime(service['next_due_date'], "%Y-%m-%d")
                if service['frequency'] == 'monthly':
                    new_date = current_date + relativedelta(months=1)
                else:
                    new_date = current_date + relativedelta(years=1)
                db.update_next_due_date(selected_service, new_date.strftime("%Y-%m-%d"))
                # Registrar gasto automático
                db.add_expense(service['amount'], datetime.today().strftime("%Y-%m-%d"),
                               service['category'], "Automático", f"Pago de {service['name']}",
                               service['currency'], current_user_id)
                st.success("Pago registrado y fecha actualizada")
                st.rerun()
        else:
            st.info("No hay servicios recurrentes.")

# ---------- Pestaña 5: Reportes ----------
with tab5:
    st.header("📁 Exportar Reportes y Predicciones")

    col1, col2 = st.columns(2)
    with col1:
        start_rep = st.date_input("Fecha inicial (reporte)", value=date(datetime.today().year, 1, 1))
    with col2:
        end_rep = st.date_input("Fecha final (reporte)", value=datetime.today())

    if st.button("📥 Generar archivos CSV"):
        df_inc = db.get_income(start_rep.strftime("%Y-%m-%d"), end_rep.strftime("%Y-%m-%d"), current_user_id)
        df_exp = db.get_expenses(start_rep.strftime("%Y-%m-%d"), end_rep.strftime("%Y-%m-%d"), current_user_id)

        csv_inc = df_inc.to_csv(index=False).encode('utf-8')
        csv_exp = df_exp.to_csv(index=False).encode('utf-8')

        st.download_button("📄 Descargar Ingresos CSV", data=csv_inc, file_name="ingresos.csv", mime="text/csv")
        st.download_button("📄 Descargar Gastos CSV", data=csv_exp, file_name="gastos.csv", mime="text/csv")

    st.subheader("🔮 Predicción de Gastos")
    df_inc_all, df_exp_all = db.get_combined_data(user_id=current_user_id)
    pred = utils.simple_prediction(df_exp_all)
    if pred:
        st.success(f"📈 **Gasto estimado para el próximo mes:** {base_currency} {pred:,.2f} (basado en promedio móvil de últimos 3 meses)")
    else:
        st.info("No hay suficientes datos históricos para realizar una predicción (necesitamos al menos 3 meses).")

    st.subheader("📋 Resumen de Datos Actuales")
    st.write("Últimos 10 ingresos:")
    df_inc_all_display = df_inc_all.sort_values('date', ascending=False).head(10)
    st.dataframe(df_inc_all_display)

    st.write("Últimos 10 gastos:")
    df_exp_all_display = df_exp_all.sort_values('date', ascending=False).head(10)
    st.dataframe(df_exp_all_display)