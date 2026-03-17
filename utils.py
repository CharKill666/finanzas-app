import pandas as pd
from datetime import datetime

def parse_date(date_string):
    """Convierte string a datetime.date (formato YYYY-MM-DD)."""
    return pd.to_datetime(date_string).date()

def get_current_month_range():
    """Devuelve (primer_día_mes, último_día_mes) para el mes actual."""
    today = datetime.today()
    first_day = today.replace(day=1).strftime("%Y-%m-%d")
    last_day = today.replace(day=28)  # Aproximado, luego ajustamos
    while (last_day + pd.DateOffset(days=1)).month == today.month:
        last_day += pd.DateOffset(days=1)
    return first_day, last_day.strftime("%Y-%m-%d")

def spending_alert(df_income, df_expenses, threshold_percent=80):
    """
    Verifica si los gastos del mes actual superan el porcentaje dado de los ingresos del mes.
    Retorna un mensaje de alerta si corresponde.
    """
    today = datetime.today()
    current_month = today.strftime("%Y-%m")
    # Ingresos del mes actual
    income_current = df_income[df_income['month'] == current_month]['amount'].sum()
    # Gastos del mes actual
    expenses_current = df_expenses[df_expenses['month'] == current_month]['amount'].sum()

    if income_current > 0:
        ratio = (expenses_current / income_current) * 100
        if ratio >= threshold_percent:
            return f"⚠️ Alerta: Has gastado el {ratio:.1f}% de tus ingresos este mes."
    return None

def simple_prediction(df_expenses, periods=1):
    """
    Predice el gasto del próximo mes usando promedio móvil simple de los últimos 3 meses.
    Retorna el valor predicho o None si no hay suficientes datos.
    """
    if df_expenses.empty:
        return None
    # Agrupar por mes y sumar
    monthly = df_expenses.groupby('month')['amount'].sum().reset_index()
    monthly = monthly.sort_values('month')
    if len(monthly) < 3:
        return None
    # Promedio móvil de los últimos 3 meses
    last_3 = monthly.tail(3)['amount'].mean()
    return last_3