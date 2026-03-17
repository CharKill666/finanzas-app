import streamlit as st
import pandas as pd
from datetime import datetime, date
import database as db
import visualizations as viz
import utils

# Inicializar base de datos
db.init_database()

# Configuración de la página
st.set_page_config(page_title="Finanzas Personales", layout="wide")
st.title("💰 Aplicación de Finanzas Personales")

# Sidebar con información de navegación (opcional)
st.sidebar.header("Opciones")
st.sidebar.info("Usa las pestañas para registrar ingresos, gastos y ver el dashboard.")

# Crear pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📥 Registrar Ingreso", "📤 Registrar Gasto", "📊 Dashboard", "📁 Reportes"])

# ---------- Pestaña 1: Registrar Ingreso ----------
with tab1:
    st.header("Registrar nuevo ingreso")
    with st.form("income_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Monto", min_value=0.01, step=0.01, format="%.2f")
            date_income = st.date_input("Fecha", value=datetime.today())
        with col2:
            source = st.text_input("Fuente del ingreso (ej. Salario, Freelance)")
            notes = st.text_area("Notas (opcional)", height=68)

        submitted = st.form_submit_button("Guardar ingreso")
        if submitted:
            if amount > 0 and source:
                db.add_income(amount, date_income.strftime("%Y-%m-%d"), source, notes)
                st.success("Ingreso guardado correctamente")
            else:
                st.error("Por favor, completa los campos obligatorios (monto y fuente)")

# ---------- Pestaña 2: Registrar Gasto ----------
with tab2:
    st.header("Registrar nuevo gasto")
    categories = ["Alimentación", "Transporte", "Vivienda", "Servicios",
                  "Entretenimiento", "Salud", "Educación", "Otros"]
    payment_methods = ["Efectivo", "Tarjeta", "Transferencia"]

    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Monto", min_value=0.01, step=0.01, format="%.2f", key="exp_amount")
            date_expense = st.date_input("Fecha", value=datetime.today(), key="exp_date")
            category = st.selectbox("Categoría", categories)
        with col2:
            payment = st.selectbox("Método de pago", payment_methods)
            description = st.text_area("Descripción (opcional)", height=68)

        submitted = st.form_submit_button("Guardar gasto")
        if submitted:
            if amount > 0 and category:
                db.add_expense(amount, date_expense.strftime("%Y-%m-%d"), category, payment, description)
                st.success("Gasto guardado correctamente")
            else:
                st.error("Por favor, completa los campos obligatorios (monto y categoría)")

# ---------- Pestaña 3: Dashboard ----------
with tab3:
    st.header("Dashboard Financiero")

    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicial", value=date(datetime.today().year, 1, 1))
    with col2:
        end_date = st.date_input("Fecha final", value=datetime.today())

    if start_date > end_date:
        st.error("La fecha inicial debe ser anterior a la final")
    else:
        # Obtener datos filtrados
        df_income, df_expenses = db.get_combined_data(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        # Mostrar alerta si corresponde (basado en mes actual)
        alert = utils.spending_alert(df_income, df_expenses)
        if alert:
            st.warning(alert)

        # Métricas rápidas
        total_income = df_income['amount'].sum() if not df_income.empty else 0
        total_expenses = df_expenses['amount'].sum() if not df_expenses.empty else 0
        balance = total_income - total_expenses

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Ingresos", f"${total_income:,.2f}")
        col2.metric("Total Gastos", f"${total_expenses:,.2f}")
        col3.metric("Balance", f"${balance:,.2f}")

        # Gráficas
        st.subheader("Comparativa Ingresos vs Gastos")
        fig1 = viz.bar_income_vs_expenses(df_income, df_expenses)
        st.plotly_chart(fig1, use_container_width=True)

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Distribución de Gastos por Categoría")
            fig2 = viz.pie_expenses_by_category(df_expenses)
            st.plotly_chart(fig2, use_container_width=True)

        with col_right:
            st.subheader("Evolución del Ahorro")
            fig3 = viz.line_cumulative_balance(df_income, df_expenses)
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Gastos Mensuales por Categoría")
        fig4 = viz.stacked_bar_expenses_by_month(df_expenses)
        st.plotly_chart(fig4, use_container_width=True)

        st.subheader("Heatmap de Gastos Diarios")
        # Permitir seleccionar mes y año para el heatmap
        col1, col2 = st.columns(2)
        with col1:
            year_heat = st.number_input("Año", min_value=2000, max_value=2100, value=datetime.today().year)
        with col2:
            month_heat = st.selectbox("Mes", range(1,13), format_func=lambda x: calendar.month_name[x])
        fig5 = viz.heatmap_daily_expenses(df_expenses, year_heat, month_heat)
        st.plotly_chart(fig5, use_container_width=True)

# ---------- Pestaña 4: Reportes ----------
with tab4:
    st.header("Exportar Reportes y Predicciones")

    # Filtros de fecha para exportación
    col1, col2 = st.columns(2)
    with col1:
        start_rep = st.date_input("Fecha inicial (reporte)", value=date(datetime.today().year, 1, 1))
    with col2:
        end_rep = st.date_input("Fecha final (reporte)", value=datetime.today())

    if st.button("Generar archivos CSV"):
        df_inc = db.get_income(start_rep.strftime("%Y-%m-%d"), end_rep.strftime("%Y-%m-%d"))
        df_exp = db.get_expenses(start_rep.strftime("%Y-%m-%d"), end_rep.strftime("%Y-%m-%d"))

        # Convertir a CSV
        csv_inc = df_inc.to_csv(index=False).encode('utf-8')
        csv_exp = df_exp.to_csv(index=False).encode('utf-8')

        st.download_button("Descargar Ingresos CSV", data=csv_inc, file_name="ingresos.csv", mime="text/csv")
        st.download_button("Descargar Gastos CSV", data=csv_exp, file_name="gastos.csv", mime="text/csv")

    st.subheader("Predicción de Gastos")
    # Obtener todos los datos sin filtrar para la predicción
    df_inc_all, df_exp_all = db.get_combined_data()
    pred = utils.simple_prediction(df_exp_all)
    if pred:
        st.write(f"📈 **Gasto estimado para el próximo mes:** ${pred:.2f} (basado en promedio móvil de últimos 3 meses)")
    else:
        st.write("No hay suficientes datos históricos para realizar una predicción (necesitamos al menos 3 meses).")

    st.subheader("Resumen de Datos Actuales")
    st.write("Últimos 10 ingresos:")
    df_inc_all_display = df_inc_all.sort_values('date', ascending=False).head(10)
    st.dataframe(df_inc_all_display)

    st.write("Últimos 10 gastos:")
    df_exp_all_display = df_exp_all.sort_values('date', ascending=False).head(10)
    st.dataframe(df_exp_all_display)