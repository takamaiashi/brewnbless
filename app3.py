from datetime import date
import sqlite3
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
            type TEXT NOT NULL,          -- 'Revenue' or 'COGS'
            category TEXT NOT NULL,      -- e.g., 'Coffee Sales', 'Milk & Beans'
            amount REAL NOT NULL,
            description TEXT,
            entered_by TEXT NOT NULL     -- Staff member who logged it
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


# --- APP CONFIG & LARGER FONT STYLING ---
st.set_page_config(
    page_title="Cafe Revenue & COGS Tracker", page_icon="☕", layout="wide"
)

st.markdown("""
    <style>
        /* Increase global font sizes for better readability */
        html, body, [class*="css"] {
            font-size: 18px !important;
        }
        
        /* Make big button navigation tabs larger and easier to tap */
        div.row-widget.stRadio > div {
            flex-direction: row;
            justify-content: center;
            gap: 15px;
        }
        div.row-widget.stRadio > div > label {
            background-color: #f0f2f6;
            padding: 18px 30px;
            border-radius: 12px;
            border: 2px solid #d0d7de;
            font-weight: bold;
            font-size: 18px !important;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        div.row-widget.stRadio > div > label:hover {
            background-color: #e3e8ef;
            border-color: #a0aec0;
        }
        /* Hide radio selection circle */
        div.row-widget.stRadio input {
            display: none;
        }
        
        /* Enlarge headers */
        h1 { font-size: 2.4rem !important; }
        h2 { font-size: 1.8rem !important; }
        h3 { font-size: 1.4rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("☕ Cafe Revenue & COGS Tracker")

# Sidebar for User Identification
st.sidebar.header("👤 Staff Profile")
username = st.sidebar.text_input(
    "Your Name / Initials",
    value="Staff",
    help="Enter your name so the team knows who logged the transaction.",
)
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Tip:** Use the large buttons at the top of the screen to navigate."
)

# --- BIG BUTTON NAVIGATION ---
menu = st.radio(
    "Navigation",
    ["📊 Dashboard & P&L", "💵 Record Revenue", "📦 Record COGS", "⚙️ Manage Data"],
    label_visibility="collapsed",
)

st.markdown("---")

# --- 1. RECORD REVENUE ---
if menu == "💵 Record Revenue":
  st.header("💵 Record Cafe Revenue")
  st.markdown(
      f"Logging as: **{username if username else 'Anonymous Staff'}**"
  )

  with st.form("revenue_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      category = st.text_input(
          "Revenue Category",
          placeholder="e.g., Coffee Sales, Pastry Sales, Merch",
      )
      amount = st.number_input(
          "Amount ($)", min_value=0.0, format="%.2f", step=1.0
      )

    with col2:
      trans_date = st.date_input("Date", value=date.today())
      description = st.text_area(
          "Description / Notes (Optional)",
          placeholder="e.g., Morning rush, special event...",
      )

    submitted = st.form_submit_button(
        "✅ Save Revenue Entry", use_container_width=True
    )

    if submitted:
      active_user = username if username else "Staff"
      if not category or amount <= 0:
        st.error(
            "Please provide a valid revenue category and an amount greater than"
            " zero."
        )
      else:
        query = """
                INSERT INTO transactions (date, type, category, amount, description, entered_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """
        run_query(
            query,
            (
                str(trans_date),
                "Revenue",
                category,
                amount,
                description,
                active_user,
            ),
            fetch=False,
        )
        st.success(
            f"Successfully recorded Revenue of ${amount:.2f} ({category}) by"
            f" {active_user}!"
        )

# --- 2. RECORD COGS ---
elif menu == "📦 Record COGS":
  st.header("📦 Record Cost of Goods Sold (COGS)")
  st.markdown(
      f"Logging as: **{username if username else 'Anonymous Staff'}**"
  )

  with st.form("cogs_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      category = st.text_input(
          "COGS Category",
          placeholder="e.g., Coffee Beans, Milk & Dairy, Pastry Stock, Cups",
      )
      amount = st.number_input(
          "Amount ($)", min_value=0.0, format="%.2f", step=1.0
      )

    with col2:
      trans_date = st.date_input("Date", value=date.today())
      description = st.text_area(
          "Description / Notes (Optional)",
          placeholder="e.g., Supplier invoice #1234...",
      )

    submitted = st.form_submit_button(
        "✅ Save COGS Entry", use_container_width=True
    )

    if submitted:
      active_user = username if username else "Staff"
      if not category or amount <= 0:
        st.error("Please provide a valid COGS category and amount.")
      else:
        query = """
                INSERT INTO transactions (date, type, category, amount, description, entered_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """
        run_query(
            query,
            (
                str(trans_date),
                "COGS",
                category,
                amount,
                description,
                active_user,
            ),
            fetch=False,
        )
        st.success(
            f"Successfully recorded COGS of ${amount:.2f} ({category}) by"
            f" {active_user}!"
        )

# --- 3. DASHBOARD & P&L ---
elif menu == "📊 Dashboard & P&L":
  st.header("📊 Financial Dashboard & Monthly P&L")

  df = run_query("SELECT * FROM transactions")

  if df.empty:
    st.info(
        "No transactions recorded yet. Use the 'Record Revenue' or 'Record"
        " COGS' tabs above to begin!"
    )
  else:
    # Extract Month-Year for aggregation
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M").astype(str)

    # Summary Metrics
    total_rev = df[df["type"] == "Revenue"]["amount"].sum()
    total_cogs = df[df["type"] == "COGS"]["amount"].sum()
    net_profit = total_rev - total_cogs
    margin = (net_profit / total_rev * 100) if total_rev > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_rev:,.2f}")
    col2.metric("Total COGS", f"${total_cogs:,.2f}")
    col3.metric("Net Profit", f"${net_profit:,.2f}")
    col4.metric("Net Profit Margin", f"{margin:.1f}%")

    st.markdown("---")
    st.subheader("📅 Detailed Category Breakdown by Month")

    pivot_df = df.pivot_table(
        index=["type", "category"],
        columns="Month",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    )
    st.dataframe(pivot_df, use_container_width=True)

    st.subheader("📈 Monthly Performance Overview")
    monthly_summary = (
        df.groupby(["Month", "type"])["amount"].sum().unstack(fill_value=0)
    )

    if "Revenue" not in monthly_summary:
      monthly_summary["Revenue"] = 0
    if "COGS" not in monthly_summary:
      monthly_summary["COGS"] = 0

    monthly_summary["Net Profit"] = (
        monthly_summary["Revenue"] - monthly_summary["COGS"]
    )

    st.dataframe(
        monthly_summary[["Revenue", "COGS", "Net Profit"]],
        use_container_width=True,
    )

# --- 4. MANAGE DATA ---
elif menu == "⚙️ Manage Data":
  st.header("⚙️ Transaction History & Audit Log")
  st.markdown(
      "Review all recorded entries, including **who logged each transaction**."
  )

  df = run_query("SELECT * FROM transactions ORDER BY date DESC")

  if df.empty:
    st.info("No records found.")
  else:
    st.dataframe(df, use_container_width=True)

    st.markdown("### 🗑️ Delete a Transaction Entry")
    col1, col2 = st.columns([2, 1])
    with col1:
      del_id = st.number_input(
          "Enter Transaction ID to Delete", min_value=1, step=1
      )
    with col2:
      st.markdown("###")
      if st.button("Delete Record", type="primary"):
        run_query("DELETE FROM transactions WHERE id = ?", (del_id,), fetch=False)
        st.success(f"Transaction ID {del_id} has been deleted.")
        st.rerun()