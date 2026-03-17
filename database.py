import sqlite3
import pandas as pd
from contextlib import contextmanager

DB_PATH = "finanzas.db"

@contextmanager
def get_db_connection():
    """Administrador de contexto para conexiones a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Crea las tablas necesarias si no existen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Tabla de ingresos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                source TEXT NOT NULL,
                notes TEXT
            )
        """)
        # Tabla de gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                description TEXT
            )
        """)
        conn.commit()

# ---------- Ingresos ----------
def add_income(amount, date, source, notes=""):
    """Inserta un nuevo ingreso."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO income (amount, date, source, notes) VALUES (?, ?, ?, ?)",
            (amount, date, source, notes)
        )
        conn.commit()

def get_income(start_date=None, end_date=None):
    """Devuelve un DataFrame con todos los ingresos, opcionalmente filtrados por fecha."""
    query = "SELECT * FROM income"
    params = []
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    return df

# ---------- Gastos ----------
def add_expense(amount, date, category, payment_method, description=""):
    """Inserta un nuevo gasto."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, date, category, payment_method, description) VALUES (?, ?, ?, ?, ?)",
            (amount, date, category, payment_method, description)
        )
        conn.commit()

def get_expenses(start_date=None, end_date=None):
    """Devuelve un DataFrame con todos los gastos, opcionalmente filtrados por fecha."""
    query = "SELECT * FROM expenses"
    params = []
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    return df

# ---------- Datos combinados para dashboard ----------
def get_combined_data(start_date=None, end_date=None):
    """
    Devuelve dos DataFrames: ingresos y gastos, ambos con columna 'month' (periodo año-mes).
    """
    df_income = get_income(start_date, end_date)
    df_expenses = get_expenses(start_date, end_date)

    if not df_income.empty:
        df_income['month'] = df_income['date'].dt.to_period('M').astype(str)
    if not df_expenses.empty:
        df_expenses['month'] = df_expenses['date'].dt.to_period('M').astype(str)

    return df_income, df_expenses