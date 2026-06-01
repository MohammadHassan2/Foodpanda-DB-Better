import streamlit as st
import sqlite3
import pandas as pd

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# Simple, readable connection handling with safe foreign key pragmas.
# -----------------------------------------------------------------------------
def get_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect("foodpanda.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def run_select_query(query, params=()):
    """Runs a SELECT query and returns the results as a Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_insert(query, params=()):
    """Executes INSERT operations safely and commits changes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

# -----------------------------------------------------------------------------
# APP CONFIGURATION & SIDEBAR
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CS160 Foodpanda Logistics", layout="wide")

st.title("🍔 Foodpanda: Cloud Kitchen & Rider Logistics")
st.subheader("CS160 Database Systems Project")
st.write("---")

# Simple beginner-friendly sidebar controls
st.sidebar.header("Navigation")
menu = st.sidebar.radio(
    "Choose an Option:",
    ["View Raw Tables", "Run Rubric Queries", "Add Customer", "Place Order"]
)

# -----------------------------------------------------------------------------
# VIEW 1: INSPECT RAW DATABASE TABLES
# -----------------------------------------------------------------------------
if menu == "View Raw Tables":
    st.header("🗂️ Inspect Database Tables")
    
    table_choice = st.selectbox(
        "Select Table to View:",
        ["Customer", "Customer_Contact", "Rider", "Rider_Contact", 
         "Saved_Address", "Restaurant", "Menu_Item", "Order_Record", 
         "Live_Tracking", "Order_Details"]
    )
    
    # Executing direct query matching the selected table name
    query = f"SELECT * FROM {table_choice}"
    df_table = run_select_query(query)
    
    st.dataframe(df_table, use_container_width=True)
    st.caption(f"Showing raw records straight from the '{table_choice}' table.")

# -----------------------------------------------------------------------------
# VIEW 2: REQUIRED RUBRIC QUERIES
# -----------------------------------------------------------------------------
elif menu == "Run Rubric Queries":
    st.header("📊 Required Course Rubric Queries")
    
    # Query A: Basic SELECT
    st.subheader("A. Basic SELECT: Active Riders")
    query_a = """
        SELECT Rider_ID, Full_Name, Vehicle_Reg, Shift_Status 
        FROM Rider 
        WHERE Shift_Status = 'active';
    """
    df_a = run_select_query(query_a)
    st.code(query_a, language="sql")
    st.dataframe(df_a)
    
    st.write("---")
    
    # Query B: JOIN Query
    st.subheader("B. JOIN Query: Complete Order Receipt")
    order_ids_df = run_select_query("SELECT Order_ID FROM Order_Record")
    
    if not order_ids_df.empty:
        selected_order = st.selectbox("Select Order ID to inspect receipt:", order_ids_df['Order_ID'])
        
        query_b = """
            SELECT 
                o.Order_ID,
                c.Full_Name AS Customer_Name,
                r.Full_Name AS Rider_Name,
                o.Order_Status,
                o.Total_Amount,
                o.Order_Time
            FROM Order_Record o
            JOIN Customer c ON o.Customer_ID = c.Customer_ID
            JOIN Rider r ON o.Rider_ID = r.Rider_ID
            WHERE o.Order_ID = ?;
        """
        df_b = run_select_query(query_b, (selected_order,))
        st.code(query_b, language="sql")
        st.table(df_b)
    
    st.write("---")
    
    # Query C: AGGREGATE Query
    st.subheader("C. AGGREGATE Query: Total Restaurant Revenue")
    query_c = """
        SELECT 
            r.Restaurant_ID,
            r.Rest_Name,
            SUM(od.Quantity * m.Price) AS Total_Revenue
        FROM Restaurant r
        JOIN Menu_Item m ON r.Restaurant_ID = m.Restaurant_ID
        JOIN Order_Details od ON m.Item_ID = od.Item_ID
        GROUP BY r.Restaurant_ID, r.Rest_Name
        ORDER BY Total_Revenue DESC;
    """
    df_c = run_select_query(query_c)
    st.code(query_c, language="sql")
    st.dataframe(df_c)

# -----------------------------------------------------------------------------
# VIEW 3: SIMPLE FORM - ADD CUSTOMER
# -----------------------------------------------------------------------------
elif menu == "Add Customer":
    st.header("👤 Register New Customer")
    st.write("Inserts a customer and their primary contact number into separate tables (3NF).")
    
    with st.form("new_customer_form", clear_on_submit=True):
        name = st.text_input("Full Name*")
        email = st.text_input("Email Address*")
        phone = st.text_input("Primary Phone Number* (e.g. 0300-1234567)")
        balance = st.number_input("Starting Wallet Balance (PKR)", min_value=0.0, value=500.0, step=100.0)
        
        submitted = st.form_submit_button("Save Customer")
        
        if submitted:
            if name and email and phone:
                try:
                    # Insert into independent Customer table
                    cust_query = "INSERT INTO Customer (Full_Name, Email, Wallet_Balance) VALUES (?, ?, ?)"
                    new_cust_id = execute_insert(cust_query, (name, email, balance))
                    
                    # Insert into dependent Contact table to satisfy 3NF
                    contact_query = "INSERT INTO Customer_Contact (Customer_ID, Phone_Number, Contact_Type) VALUES (?, ?, 'primary')"
                    execute_insert(contact_query, (new_cust_id, phone))
                    
                    st.success(f"Customer registered successfully! Assigned Customer ID: {new_cust_id}")
                except sqlite3.IntegrityError:
                    st.error("Error: This email address is already registered.")
            else:
                st.warning("Please fill out all required fields marked with an asterisk (*).")
# -----------------------------------------------------------------------------
# VIEW 4: REACTIVE UI - PLACE DYNAMIC ORDER (WITH WALLET CONSTRAINT)
# -----------------------------------------------------------------------------
elif menu == "Place Order":
    st.header("🛵 Place a Basic Order")
    
    # Fetch base active data (Now grabbing Wallet_Balance as well)
    customers = run_select_query("SELECT Customer_ID, Full_Name, Wallet_Balance FROM Customer")
    restaurants = run_select_query("SELECT Restaurant_ID, Rest_Name FROM Restaurant WHERE Operating_Status = 'open'")
    
    if customers.empty or restaurants.empty:
        st.error("Cannot place orders. Ensure customers and open restaurants exist in the database.")
    else:
        # 1. Select Customer
        cust_options = dict(zip(customers['Customer_ID'], customers['Full_Name']))
        selected_cust = st.selectbox("Select Customer:", customers['Customer_ID'], format_func=lambda x: f"{x} - {cust_options[x]}")
        
        # Display current wallet balance for clarity
        current_balance = float(customers.loc[customers['Customer_ID'] == selected_cust, 'Wallet_Balance'].values[0])
        st.caption(f"**Current Wallet Balance:** PKR {current_balance:.2f}")
        
        # 2. Select Restaurant
        rest_options = dict(zip(restaurants['Restaurant_ID'], restaurants['Rest_Name']))
        selected_rest = st.selectbox("Select Restaurant:", restaurants['Restaurant_ID'], format_func=lambda x: f"{x} - {rest_options[x]}")
        
        # 3. Dynamically load items for the selected restaurant
        items_query = "SELECT Item_ID, Item_Name, Price FROM Menu_Item WHERE Restaurant_ID = ?"
        menu_items = run_select_query(items_query, (selected_rest,))
        
        if menu_items.empty:
            st.warning("This restaurant currently has no menu items listed.")
        else:
            # Create a display format showing Item Name + Price
            menu_items['Display'] = menu_items['Item_Name'] + " (PKR " + menu_items['Price'].astype(str) + ")"
            item_dict = dict(zip(menu_items['Display'], menu_items['Item_ID']))
            
            selected_item_display = st.selectbox("Select Item:", menu_items['Display'])
            selected_item_id = item_dict[selected_item_display]
            
            # Extract precise numerical price and calculate totals
            unit_price = float(menu_items.loc[menu_items['Display'] == selected_item_display, 'Price'].values[0])
            quantity = st.number_input("Quantity:", min_value=1, value=1, step=1)
            total_amount = unit_price * quantity
            
            st.info(f"**Total Amount Calculated:** PKR {total_amount:.2f}")
            
            # 4. Auto-assign a Rider
            active_riders = run_select_query("SELECT Rider_ID, Full_Name FROM Rider WHERE Shift_Status = 'active'")
            
            if active_riders.empty:
                st.error("Order cannot proceed. No active riders are currently available.")
            else:
                assigned_rider = active_riders.sample(1).iloc[0]
                selected_rider_id = int(assigned_rider['Rider_ID'])
                st.success(f"**System Auto-Assigned Rider:** {assigned_rider['Full_Name']}")
                
                # 5. Confirm Order Action with WALLET CONSTRAINT
                if st.button("Confirm Order"):
                    
                    # --- THE CONSTRAINT LOGIC ---
                    if total_amount > current_balance:
                        st.error(f"❌ **Order Cancelled:** Insufficient funds. Your balance is PKR {current_balance:.2f}, but the total is PKR {total_amount:.2f}.")
                    else:
                        # Deduct from Wallet First
                        wallet_update = "UPDATE Customer SET Wallet_Balance = Wallet_Balance - ? WHERE Customer_ID = ?"
                        execute_insert(wallet_update, (total_amount, selected_cust))
                        
                        # Insert into Order_Record
                        order_query = "INSERT INTO Order_Record (Customer_ID, Rider_ID, Total_Amount, Order_Status) VALUES (?, ?, ?, 'pending')"
                        new_ord_id = execute_insert(order_query, (selected_cust, selected_rider_id, total_amount))
                        
                        # Insert into Order_Details
                        details_query = "INSERT INTO Order_Details (Order_ID, Item_ID, Quantity) VALUES (?, ?, ?)"
                        execute_insert(details_query, (new_ord_id, selected_item_id, quantity))
                        
                        # Auto-generate tracking session
                        track_query = "INSERT INTO Live_Tracking (Order_ID, Estimated_Arrival, Ping_Status) VALUES (?, datetime('now', '+45 minutes'), 'active')"
                        execute_insert(track_query, (new_ord_id,))
                        
                        st.balloons()
                        st.success(f"✅ Order #{new_ord_id} created! PKR {total_amount:.2f} was deducted from your wallet.")