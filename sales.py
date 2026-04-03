import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# ------------------------------ 
st.set_page_config(
    page_title="Sales Intelligence Hub",
    page_icon="📊",
    layout="wide"
)

# ------------------------------ 
st.markdown("""
<style>
.main { background-color: #FFC0CB; }
h1, h2, h3 { color: #9CA3AF; }

.stMetric {
    background-color: yellow;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}

.block-container { padding-top: 2rem; }

div.stButton > button {
    border-radius: 8px;
    background-color: #EF4444;
    color: white;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #10B981;
}

.card {
    padding: 20px;
    border-radius: 12px;
    background-color: white;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
for key in ['logged_in', 'Role', 'username', 'Branch_Id', 'show_query', 'page']:
    if key not in st.session_state:
        st.session_state[key] = None

# ------------------------------ 
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="K@rth!1990",
        database="sales_intelligence_hub"
    )

# ------------------------------ FETCH SALES
def fetch_sales(start_date=None, end_date=None, product=None, branch=None):
    conn = get_db_connection()
    query = """
        SELECT cs.Sale_Id, cs.Branch_Id, b.Branch_Name, cs.Name, cs.Mobile_Number,
               cs.Product_Name, cs.Gross_Sales, cs.Received_Amount,
               (cs.Gross_Sales - cs.Received_Amount) AS Pending_Amount,
               cs.Status, cs.Date
        FROM sales cs
        JOIN branches b ON cs.Branch_Id = b.Branch_Id
        WHERE 1=1
    """
    params = []
    if st.session_state['Role'] != 'Super Admin':
        query += " AND cs.Branch_Id=%s"
        params.append(st.session_state['Branch_Id'])
    if branch:
        query += " AND cs.Branch_Id=%s"
        params.append(branch)
    if start_date and end_date:
        query += " AND cs.Date >= %s AND cs.Date <= %s"
        params.append(str(start_date) + " 00:00:00")
        params.append(str(end_date) + " 23:59:59")
    if product and product != "All":
        query += " AND cs.Product_Name=%s"
        params.append(product)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    if not df.empty:
        df['Status'] = df['Pending_Amount'].apply(lambda x: 'Close' if x == 0 else 'Open')
    return df

# ------------------------------ 
def run_selected_query(query_name):
    conn = get_db_connection()
    queries = {
        # Basic Queries
        "All Customer Sales": "SELECT * FROM sales",
        "All Branches": "SELECT * FROM branches",
        "All Payments": "SELECT * FROM payment_splits",
        "Open Sales": "SELECT * FROM sales WHERE Status='Open'",
        "Chennai Branch Sales": """
            SELECT s.* FROM sales s
            JOIN branches b ON s.Branch_Id=b.Branch_Id
            WHERE b.Branch_Name='Chennai'
        """,
        # Aggregation Queries
        "Total Gross Sales": "SELECT SUM(Gross_Sales) AS Total_Gross FROM sales",
        "Total Received": "SELECT SUM(Received_Amount) AS Total_Received FROM sales",
        "Total Pending": "SELECT SUM(Gross_Sales - Received_Amount) AS Total_Pending FROM sales",
        "Sales Count Per Branch": """
            SELECT b.Branch_Name, COUNT(*) AS Total_Sales
            FROM sales s JOIN branches b ON s.Branch_Id=b.Branch_Id
            GROUP BY b.Branch_Name
        """,
        "Average Sales": "SELECT AVG(Gross_Sales) AS Avg_Sales FROM sales",
        # Join-Based Queries
        "Sales with Branch Name": """
            SELECT s.*, b.Branch_Name
            FROM sales s JOIN branches b ON s.Branch_Id=b.Branch_Id
        """,
        "Sales with Payments": """
            SELECT s.Sale_Id, s.Name, SUM(p.Amount_Paid) AS Total_Paid
            FROM sales s LEFT JOIN payment_splits p ON s.Sale_Id=p.Sale_Id
            GROUP BY s.Sale_Id
        """,
        "Branch-wise Sales": """
            SELECT b.Branch_Name, SUM(s.Gross_Sales) AS Total_Sales
            FROM sales s JOIN branches b ON s.Branch_Id=b.Branch_Id
            GROUP BY b.Branch_Name
        """,
        "Sales with Payment Method": """
            SELECT s.Sale_Id, s.Name, p.Payment_Method
            FROM sales s JOIN payment_splits p ON s.Sale_Id=p.Sale_Id
        """,
        "Sales with Admin": """
            SELECT s.Sale_Id, s.Name, u.username AS Admin
            FROM sales s JOIN users u ON s.Branch_Id=u.Branch_Id
        """,
        # Financial Tracking
        "High Pending Sales": """
            SELECT *, (Gross_Sales - Received_Amount) AS Pending
            FROM sales WHERE (Gross_Sales - Received_Amount) > 5000
        """,
        "Top 3 Sales": "SELECT * FROM sales ORDER BY Gross_Sales DESC LIMIT 3",
        "Top Branch": """
            SELECT b.Branch_Name, SUM(s.Gross_Sales) AS Total
            FROM sales s JOIN branches b ON s.Branch_Id=b.Branch_Id
            GROUP BY b.Branch_Name ORDER BY Total DESC LIMIT 1
        """,
        "Monthly Summary": """
            SELECT YEAR(Date) AS Year, MONTH(Date) AS Month,
                   SUM(Gross_Sales) AS Total_Sales
            FROM sales GROUP BY Year, Month
        """,
        "Payment Method Summary": """
            SELECT Payment_Method, SUM(Amount_Paid) AS Total
            FROM payment_splits GROUP BY Payment_Method
        """
    }
    df = pd.read_sql(queries[query_name], conn)
    conn.close()
    return df

# ------------------------------
def login():
    st.title("🔐 Sales Intelligence Hub")
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")
    if st.button("Login"):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and password == user['password']:
            st.session_state['logged_in'] = True
            st.session_state['Role'] = user.get('Role', 'Admin')
            st.session_state['username'] = user['username']
            st.session_state['Branch_Id'] = user.get('Branch_Id')
            st.session_state['page'] = "📊 Dashboard"  # default page
        else:
            st.error("Invalid credentials")

# ------------------------------
def dashboard():
    st.title("📊 Dashboard")
    st.caption(f"Welcome, {st.session_state['username']} ({st.session_state['Role']})")

    # 🔘 QUERY BUTTON
    if st.button("📊 Query"):
        st.session_state['show_query'] = not st.session_state['show_query']

    # 🔽 QUERY PANEL
    if st.session_state['show_query']:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📌 Query Panel")
        query_options = {
            "🔹 Basic Queries": [
                "All Customer Sales","All Branches","All Payments","Open Sales","Chennai Branch Sales"
            ],
            "🔹 Aggregation Queries": [
                "Total Gross Sales","Total Received","Total Pending","Sales Count Per Branch","Average Sales"
            ],
            "🔹 Join-Based Queries": [
                "Sales with Branch Name","Sales with Payments","Branch-wise Sales",
                "Sales with Payment Method","Sales with Admin"
            ],
            "🔹 Financial Tracking": [
                "High Pending Sales","Top 3 Sales","Top Branch","Monthly Summary","Payment Method Summary"
            ]
        }
        category = st.selectbox("Select Category", list(query_options.keys()))
        query_name = st.selectbox("Select Query", query_options[category])
        if st.button("▶ Execute Query"):
            df_query = run_selected_query(query_name)
            st.success("Query Executed ✅")
            st.dataframe(df_query, use_container_width=True)
            st.download_button("⬇ Download CSV", df_query.to_csv(index=False), "query_result.csv")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----------------
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        start_date = col1.date_input("Start Date", value=date(2020,1,1))
        end_date = col2.date_input("End Date", value=date.today())
        product_filter = col3.selectbox("Product", ["All",'DS','DA','BA','FSD','BI','SQL','ML','AI'])
        st.markdown("</div>", unsafe_allow_html=True)

    df_sales = fetch_sales(start_date, end_date, product_filter)
    if df_sales.empty:
        st.warning("No data found")
        return

    # ---------------- 
    c1, c2, c3 = st.columns(3)
    total_sales = df_sales['Gross_Sales'].sum()
    total_received = df_sales['Received_Amount'].sum()
    total_pending = df_sales['Pending_Amount'].sum()
    c1.metric("💰 Total Sales", f"₹ {total_sales:,.0f}")
    c2.metric("✅ Received", f"₹ {total_received:,.0f}")
    c3.metric("⏳ Pending", f"₹ {total_pending:,.0f}")

    # ---------------- 
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Branch-wise Sales")
        st.bar_chart(df_sales.groupby("Branch_Name")["Gross_Sales"].sum())
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Pending Amount")
        st.bar_chart(df_sales.groupby("Branch_Name")["Pending_Amount"].sum())
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- 
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Recent Sales")
    st.dataframe(df_sales.sort_values(by="Sale_Id", ascending=False).head(10), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------ 
def add_sales():
    st.title("➕ Add Sales")
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if st.session_state['Role'] == 'Super Admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Branch_Id, Branch_Name FROM branches")
        branches = cursor.fetchall()
        conn.close()
        branch_options = {b[1]: b[0] for b in branches}
        selected_branch = st.selectbox("Select Branch", list(branch_options.keys()))
        Branch_Id = branch_options[selected_branch]
    else:
        Branch_Id = st.session_state['Branch_Id']

    name = st.text_input("Customer Name")
    mobile = st.text_input("Mobile Number")
    product = st.selectbox("Product Type", ['DS','DA','BA','FSD','BI','SQL','ML','AI'])
    amount = st.number_input("Gross Sales", min_value=0.0)

    if st.button("Add Sale"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sales (Branch_Id, Name, Mobile_Number, Product_Name, Gross_Sales, Date, Received_Amount, Status) VALUES (%s,%s,%s,%s,%s,NOW(),0,'Open')",
            (Branch_Id, name, mobile, product, amount)
        )
        conn.commit()
        conn.close()
        st.success("Sale Added 🎉")
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------ 
def add_payment():
    st.title("💰 Add Payment")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if st.session_state['Role'] == 'Super Admin':
        cursor.execute("SELECT Sale_Id, Name, Product_Name FROM sales")
    else:
        cursor.execute("SELECT Sale_Id, Name, Product_Name FROM sales WHERE Branch_Id=%s",
                       (st.session_state['Branch_Id'],))

    sales = cursor.fetchall()
    conn.close()

    if not sales:
        st.warning("No sales available")
        return

    options = {f"{s['Sale_Id']} - {s['Name']}": s for s in sales}
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    selected_key = st.selectbox("Select Sale", list(options.keys()))
    selected_sale = options[selected_key]

    st.text_input("Product Name", value=selected_sale['Product_Name'], disabled=True)
    payment = st.number_input("Payment Amount", min_value=0.0)
    method = st.selectbox("Payment Method", ["Cash", "UPI", "Card"])

    if st.button("Add Payment"):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert payment record
        cursor.execute(
            "INSERT INTO payment_splits (Sale_Id, Payment_Date, Amount_Paid, Payment_Method) VALUES (%s,NOW(),%s,%s)",
            (selected_sale['Sale_Id'], payment, method)
        )

        # Update sale received amount and status
        cursor.execute(
            "UPDATE sales SET Received_Amount = Received_Amount + %s WHERE Sale_Id=%s",
            (payment, selected_sale['Sale_Id'])
        )
        cursor.execute(
            "UPDATE sales SET Status = CASE WHEN Gross_Sales = Received_Amount THEN 'Close' ELSE 'Open' END WHERE Sale_Id=%s",
            (selected_sale['Sale_Id'],)
        )

        conn.commit()
        conn.close()

        st.success(f"Payment of ₹{payment:,.2f} added via {method} ✅")

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------ 
def main():
    st.sidebar.markdown("## 🧭 Navigation")
    st.sidebar.markdown("---")

    if st.session_state['logged_in']:
        if st.sidebar.button("🚪 Logout"):
            for key in ['logged_in', 'Role', 'username', 'Branch_Id', 'show_query', 'page']:
                st.session_state[key] = None

        # Navigation radio
        nav_option = st.sidebar.radio(
            "Go to",
            ["📊 Dashboard", "➕ Add Sales", "💰 Add Payment"],
            index=0
        )
        st.session_state['page'] = nav_option

        if st.session_state['page'] == "📊 Dashboard":
            dashboard()
        elif st.session_state['page'] == "➕ Add Sales":
            add_sales()
        elif st.session_state['page'] == "💰 Add Payment":
            add_payment()
    else:
        login()

# ------------------------------ RUN
if __name__ == "__main__":
    main()