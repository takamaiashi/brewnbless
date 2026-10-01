from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

# --- APP CONFIG ---
st.set_page_config(
    page_title="Cafe Revenue & COGS Tracker", page_icon="☕", layout="wide"
)

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


# --- STYLING (Extra Large Menu Fonts & Forms) ---
st.markdown("""
    <style>
        /* Global font increase */
        html, body, [class*="css"] {
            font-size: 18px !important;
        }
        
        /* --- EXTRA LARGE NAVIGATION MENU BUTTONS --- */
        div.row-widget.stRadio > div {
            flex-direction: row;
            justify-content: center;
            gap: 20px;
        }
        div.row-widget.stRadio > div > label {
            background-color: #f0f2f6;
            padding: 22px 35px;
            border-radius: 14px;
            border: 3px solid #cbd5e1;
            font-weight: 800 !important;
            font-size: 22px !important;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        div.row-widget.stRadio > div > label:hover {
            background-color: #e2e8f0;
            border-color: #94a3b8;
        }
        div.row-widget.stRadio input {
            display: none;
        }
        
        /* --- EXTRA LARGE FONTS FOR RECORDING FORMS --- */
        div[data-testid="stForm"] label p {
            font-size: 20px !important;
            font-weight: 700 !important;
            color: #1f2937 !important;
        }
        div[data-testid="stForm"] input, 
        div[data-testid="stForm"] textarea,
        div[data-testid="stForm"] div[data-baseweb="select"] {
            font-size: 20px !important;
        }
        div[data-testid="stForm"] button {
            font-size: 22px !important;
            font-weight: bold !important;
            padding: 15px 20px !important;
            background-color: #2e7d32 !important;
            color: white !important;
            border-radius: 10px !important;
        }
        
        h1 { font-size: 2.6rem !important; }
        h2 { font-size: 2.0rem !important; }
        h3 { font-size: 1.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN GATEKEEPER SYSTEM ---
# Change your team password here:
CAFE_PASSWORD = "cafe123"

if "authenticated" not in st.session_state:
  st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
  st.title("☕ Cafe Revenue & COGS Tracker")
  st.markdown("### Please log in to access the system.")

  with st.form("login_form"):
    pwd_input = st.text_input("Enter Cafe Passcode", type="password")
    login_btn = st.form_submit_button("🔓 Login to App", use_container_width=True)

    if login_btn:
      if pwd_input == CAFE_PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
      else:
        st.error("Incorrect passcode. Please try again.")
  st.stop()  # Halt execution until authenticated

# --- MAIN APP INTERFACE (Post-Login) ---
st.title("☕ Cafe Revenue & COGS Tracker")

# --- MAIN PAGE STAFF PROFILE & AUTOMATIC DETECTION ---
logged_in_user = None
try:
  if hasattr(st, "user") and st.user.get("email"):
    logged_in_user = st.user.get("name") or st.user.get("email")
except Exception:
  pass

st.markdown("### 👤 Active Staff Profile")
col_prof1, col_prof2 = st.columns([2, 2])

with col_prof1:
  if logged_in_user:
    username = logged_in_user
    st.success(f"✅ **Cloud Authenticated as:** {username}")
  else:
    username = st.text_input(
        "Enter Your Name / Initials",
        value="Staff",
        help="Your name will be saved with every transaction you log below.",
    )

with col_prof2:
  st.markdown("###")
  if st.button("🔒 Lock / Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

st.markdown("---")

# --- EXTRA LARGE BUTTON NAVIGATION ---
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
      f"Logging transactions under: **{username if username else 'Staff'}**"
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
      f"Logging transactions under: **{username if username else 'Staff'}**"
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
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M").astype(str)

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