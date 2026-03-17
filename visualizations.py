import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar

def bar_income_vs_expenses(df_income, df_expenses):
    """Gráfico de barras: Ingresos vs Gastos por mes."""
    # Agrupar por mes
    if not df_income.empty:
        income_monthly = df_income.groupby('month')['amount'].sum().reset_index()
    else:
        income_monthly = pd.DataFrame(columns=['month', 'amount'])

    if not df_expenses.empty:
        expenses_monthly = df_expenses.groupby('month')['amount'].sum().reset_index()
    else:
        expenses_monthly = pd.DataFrame(columns=['month', 'amount'])

    # Unir ambos en un solo DataFrame para Plotly
    all_months = pd.concat([income_monthly['month'], expenses_monthly['month']]).unique()
    all_months = sorted(all_months)
    df_plot = pd.DataFrame({'month': all_months})
    df_plot = df_plot.merge(income_monthly, on='month', how='left').rename(columns={'amount': 'Ingresos'})
    df_plot = df_plot.merge(expenses_monthly, on='month', how='left').rename(columns={'amount': 'Gastos'})
    df_plot = df_plot.fillna(0)

    fig = px.bar(df_plot, x='month', y=['Ingresos', 'Gastos'],
                 title="Ingresos vs Gastos por Mes",
                 barmode='group',
                 labels={'value': 'Monto', 'month': 'Mes'},
                 color_discrete_map={'Ingresos': 'green', 'Gastos': 'red'})
    return fig

def pie_expenses_by_category(df_expenses):
    """Gráfico circular: Distribución de gastos por categoría."""
    if df_expenses.empty:
        return px.pie(title="No hay datos de gastos")
    category_totals = df_expenses.groupby('category')['amount'].sum().reset_index()
    fig = px.pie(category_totals, values='amount', names='category',
                 title="Distribución de Gastos por Categoría")
    return fig

def line_cumulative_balance(df_income, df_expenses):
    """Gráfico de línea: Evolución del ahorro acumulado."""
    # Combinar todos los movimientos en orden cronológico
    if df_income.empty and df_expenses.empty:
        return px.line(title="No hay datos")

    # Crear una serie temporal con todos los días
    all_dates = pd.concat([df_income['date'], df_expenses['date']]).drop_duplicates().sort_values()
    if all_dates.empty:
        return px.line(title="No hay datos")

    # Acumular ingresos y gastos día a día
    balance = []
    cumulative = 0
    for date in all_dates:
        inc = df_income[df_income['date'] == date]['amount'].sum()
        exp = df_expenses[df_expenses['date'] == date]['amount'].sum()
        cumulative += inc - exp
        balance.append({'date': date, 'balance': cumulative})

    df_balance = pd.DataFrame(balance)
    fig = px.line(df_balance, x='date', y='balance',
                  title="Evolución del Ahorro Acumulado",
                  labels={'date': 'Fecha', 'balance': 'Ahorro acumulado'})
    return fig

def stacked_bar_expenses_by_month(df_expenses):
    """Gráfico de barras apiladas: Gastos mensuales por categoría."""
    if df_expenses.empty:
        return px.bar(title="No hay datos de gastos")
    # Agrupar por mes y categoría
    grouped = df_expenses.groupby(['month', 'category'])['amount'].sum().reset_index()
    fig = px.bar(grouped, x='month', y='amount', color='category',
                 title="Gastos Mensuales por Categoría",
                 labels={'month': 'Mes', 'amount': 'Monto', 'category': 'Categoría'})
    return fig

def heatmap_daily_expenses(df_expenses, year=None, month=None):
    """
    Heatmap de gastos diarios.
    Si no se especifica año/mes, usa el mes actual.
    """
    if df_expenses.empty:
        return go.Figure()

    # Si no se proporciona año/mes, usar el mes actual
    if year is None or month is None:
        today = pd.Timestamp.now()
        year = today.year
        month = today.month

    # Filtrar el DataFrame al mes deseado
    df_month = df_expenses[(df_expenses['date'].dt.year == year) &
                           (df_expenses['date'].dt.month == month)]
    if df_month.empty:
        return go.Figure()

    # Obtener los días del mes
    num_days = calendar.monthrange(year, month)[1]
    days = list(range(1, num_days + 1))

    # Crear matriz de gastos por día (puede haber varios gastos el mismo día, sumamos)
    daily_totals = df_month.groupby(df_month['date'].dt.day)['amount'].sum().reindex(days, fill_value=0)

    # Preparar datos para el heatmap (una fila)
    # Usaremos un heatmap con una sola fila y los días como columnas
    z = [daily_totals.values]  # lista de listas (1 fila)

    # Etiquetas para los días
    text = [[f"Día {d}: ${v:.2f}" for d, v in zip(days, daily_totals.values)]]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=days,
        y=['Gastos diarios'],
        colorscale='Reds',
        text=text,
        hoverinfo='text',
        showscale=True,
        colorbar=dict(title="Monto")
    ))
    fig.update_layout(
        title=f"Heatmap de Gastos Diarios - {calendar.month_name[month]} {year}",
        xaxis_title="Día del mes",
        yaxis=dict(showticklabels=False),
        height=200
    )
    return fig