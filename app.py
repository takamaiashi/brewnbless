import sqlite3
from datetime import date
import pandas as pd
import streamlit as st

# --- DATABASE SETUP ---
DB_FILE = "cafe_finance.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,          -- 'Revenue' or 'Cost'
            category TEXT NOT NULL,      -- e.g., 'Food Sales', 'Rent', 'Beans'
            amount REAL NOT NULL,
            description TEXT,
            entered_by TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


def run_query(query, params=(), fetch=True):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(query, params)
  if fetch:
    data = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    conn.close()
    return pd.DataFrame(data, columns=cols)
  else:
    conn.commit()
    conn.close()


# --- APP INTERFACE ---
st.set_page_config(
    page_title="Cafe P&L Tracker", page_icon="☕", layout="wide"
)

st.title("☕ Cafe Revenue & Cost Tracker")
st.markdown("Capture ad-hoc transactions and view real-time monthly P&L.")

# Sidebar Navigation
st.sidebar.header("Navigation")
menu = st.sidebar.radio(
    "Go to", ["Dashboard & P&L", "Add Transaction", "Manage Data"]
)

# User Identification (for multi-user tracking)
username = st.sidebar.text_input("Your Name / Initials", value="Staff")

# --- 1. ADD TRANSACTION ---
if menu == "Add Transaction":
  st.header("📝 Record Ad-Hoc Transaction")

  with st.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      trans_type = st.selectbox(
          "Transaction Type", ["Revenue", "Cost of Goods Sold (COGS)", "Expense"]
      )
      category = st.text_input(
          "Category",
          placeholder="e.g., Beverage Sales, Rent, Electricity, Beans",
      )
      amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")

    with col2:
      trans_date = st.date_input("Date", value=date.today())
      description = st.text_area(
          "Description / Notes", placeholder="Optional details..."
      )

    submitted = st.form_submit_button("Save Transaction")

    if submitted:
      if not category or amount <= 0:
        st.error(
            "Please provide a valid category and an amount greater than zero."
        )
      else:
        # Normalize type for P&L grouping
        db_type = (
            "Revenue"
            if trans_type == "Revenue"
            else ("COGS" if trans_type == "Cost of Goods Sold (COGS)" else "Expense")
        )

        query = """
                INSERT INTO transactions (date, type, category, amount, description, entered_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """
        run_query(
            query,
            (
                str(trans_date),
                db_type,
                category,
                amount,
                description,
                username,
            ),
            fetch=False,
        )
        st.success(
            f"Successfully recorded ${amount:.2f} under {trans_type}!"
        )

# --- 2. DASHBOARD & MONTHLY P&L ---
elif menu == "Dashboard & P&L":
  st.header("📊 Financial Dashboard & Monthly P&L")

  df = run_query("SELECT * FROM transactions")

  if df.empty:
    st.info(
        "No transactions recorded yet. Use the 'Add Transaction' tab to get"
        " started."
    )
  else:
    # Extract Month-Year for aggregation
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M").astype(str)

    # Summary Metrics
    total_rev = df[df["type"] == "Revenue"]["amount"].sum()
    total_cogs = df[df["type"] == "COGS"]["amount"].sum()
    total_exp = df[df["type"] == "Expense"]["amount"].sum()
    gross_profit = total_rev - total_cogs
    net_profit = gross_profit - total_exp

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_rev:,.2f}")
    col2.metric("Gross Profit", f"${gross_profit:,.2f}")
    col3.metric("Total Expenses", f"${total_exp:,.2f}")
    col4.metric(
        "Net Profit",
        f"${net_profit:,.2f}",
        delta=f"${net_profit:,.2f}",
        delta_color="normal",
    )

    st.markdown("---")
    st.subheader("📅 Monthly P&L Summary Matrix")

    # Pivot table for Monthly P&L
    pivot_df = df.pivot_table(
        index=["type", "category"],
        columns="Month",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    )
    st.dataframe(pivot_df, use_container_width=True)

    # High-level monthly breakdown table
    st.subheader("📈 Monthly Performance Overview")
    monthly_summary = (
        df.groupby(["Month", "type"])["amount"].sum().unstack(fill_value=0)
    )

    if "Revenue" not in monthly_summary:
      monthly_summary["Revenue"] = 0
    if "COGS" not in monthly_summary:
      monthly_summary["COGS"] = 0
    if "Expense" not in monthly_summary:
      monthly_summary["Expense"] = 0

    monthly_summary["Gross Profit"] = (
        monthly_summary["Revenue"] - monthly_summary["COGS"]
    )
    monthly_summary["Net Profit"] = (
        monthly_summary["Gross Profit"] - monthly_summary["Expense"]
    )

    st.dataframe(
        monthly_summary[
            ["Revenue", "COGS", "Gross Profit", "Expense", "Net Profit"]
        ],
        use_container_width=True,
    )

# --- 3. MANAGE DATA ---
elif menu == "Manage Data":
  st.header("⚙️ Transaction History & Management")

  df = run_query("SELECT * FROM transactions ORDER BY date DESC")

  if df.empty:
    st.info("No records found.")
  else:
    st.dataframe(df, use_container_width=True)

    st.markdown("### Delete a Transaction")
    del_id = st.number_input("Enter Transaction ID to Delete", min_value=1, step=1)
    if st.button("Delete Record"):
      run_query("DELETE FROM transactions WHERE id = ?", (del_id,), fetch=False)
      st.success(f"Transaction ID {del_id} deleted successfully.")
      st.rerun()