cat > /home/claude/app.py << 'PYEOF'
# =============================================================================
# CS160 Database Systems | Foodpanda: Cloud Kitchen & Rider Fleet Logistics
# Streamlit Frontend — app.py
# Run: streamlit run app.py
# =============================================================================

import sqlite3
import os
import streamlit as st
import pandas as pd
from datetime import datetime

# ─── Constants ────────────────────────────────────────────────────────────────
DB_PATH = "foodpanda.db"

SCHEMA_SQL = """
DROP TABLE IF EXISTS Order_Details;
DROP TABLE IF EXISTS Live_Tracking;
DROP TABLE IF EXISTS Order_Record;
DROP TABLE IF EXISTS Saved_Address;
DROP TABLE IF EXISTS Menu_Item;
DROP TABLE IF EXISTS Rider_Contact;
DROP TABLE IF EXISTS Customer_Contact;
DROP TABLE IF EXISTS Restaurant;
DROP TABLE IF EXISTS Rider;
DROP TABLE IF EXISTS Customer;

CREATE TABLE Customer (
    Customer_ID     INTEGER PRIMARY KEY AUTOINCREMENT,
    Full_Name       TEXT    NOT NULL,
    Email           TEXT    NOT NULL UNIQUE,
    Wallet_Balance  REAL    NOT NULL DEFAULT 0.00 CHECK (Wallet_Balance >= 0)
);

CREATE TABLE Customer_Contact (
    Contact_ID      INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID     INTEGER NOT NULL,
    Phone_Number    TEXT    NOT NULL,
    Contact_Type    TEXT    NOT NULL DEFAULT 'primary'
                    CHECK (Contact_Type IN ('primary', 'secondary')),
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID) ON DELETE CASCADE
);

CREATE TABLE Rider (
    Rider_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Full_Name       TEXT    NOT NULL,
    Vehicle_Reg     TEXT    NOT NULL UNIQUE,
    Shift_Status    TEXT    NOT NULL DEFAULT 'inactive'
                    CHECK (Shift_Status IN ('active', 'inactive', 'on_break'))
);

CREATE TABLE Rider_Contact (
    Contact_ID      INTEGER PRIMARY KEY AUTOINCREMENT,
    Rider_ID        INTEGER NOT NULL,
    Phone_Number    TEXT    NOT NULL,
    Contact_Type    TEXT    NOT NULL DEFAULT 'primary'
                    CHECK (Contact_Type IN ('primary', 'secondary')),
    FOREIGN KEY (Rider_ID) REFERENCES Rider(Rider_ID) ON DELETE CASCADE
);

CREATE TABLE Saved_Address (
    Customer_ID             INTEGER NOT NULL,
    Address_Label           TEXT    NOT NULL,
    Street                  TEXT    NOT NULL,
    City                    TEXT    NOT NULL,
    Zip                     TEXT    NOT NULL,
    Delivery_Instructions   TEXT,
    PRIMARY KEY (Customer_ID, Address_Label),
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID) ON DELETE CASCADE
);

CREATE TABLE Restaurant (
    Restaurant_ID       INTEGER PRIMARY KEY AUTOINCREMENT,
    Rest_Name           TEXT    NOT NULL,
    Operating_Status    TEXT    NOT NULL DEFAULT 'open'
                        CHECK (Operating_Status IN ('open', 'closed', 'busy')),
    Rating              REAL    NOT NULL DEFAULT 0.0
                        CHECK (Rating BETWEEN 0.0 AND 5.0)
);

CREATE TABLE Menu_Item (
    Item_ID         INTEGER PRIMARY KEY AUTOINCREMENT,
    Restaurant_ID   INTEGER NOT NULL,
    Item_Name       TEXT    NOT NULL,
    Price           REAL    NOT NULL CHECK (Price > 0),
    Category        TEXT    NOT NULL,
    FOREIGN KEY (Restaurant_ID) REFERENCES Restaurant(Restaurant_ID) ON DELETE CASCADE
);

CREATE TABLE Order_Record (
    Order_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_ID     INTEGER NOT NULL,
    Rider_ID        INTEGER NOT NULL,
    Total_Amount    REAL    NOT NULL CHECK (Total_Amount >= 0),
    Order_Status    TEXT    NOT NULL DEFAULT 'pending'
                    CHECK (Order_Status IN ('pending','preparing','on_the_way','delivered','cancelled')),
    Order_Time      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID),
    FOREIGN KEY (Rider_ID)    REFERENCES Rider(Rider_ID)
);

CREATE TABLE Live_Tracking (
    Tracking_ID         INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_ID            INTEGER NOT NULL UNIQUE,
    Estimated_Arrival   TEXT    NOT NULL,
    Ping_Status         TEXT    NOT NULL DEFAULT 'active'
                        CHECK (Ping_Status IN ('active', 'idle', 'completed')),
    FOREIGN KEY (Order_ID) REFERENCES Order_Record(Order_ID) ON DELETE CASCADE
);

CREATE TABLE Order_Details (
    Order_ID    INTEGER NOT NULL,
    Item_ID     INTEGER NOT NULL,
    Quantity    INTEGER NOT NULL CHECK (Quantity > 0),
    PRIMARY KEY (Order_ID, Item_ID),
    FOREIGN KEY (Order_ID) REFERENCES Order_Record(Order_ID) ON DELETE CASCADE,
    FOREIGN KEY (Item_ID)  REFERENCES Menu_Item(Item_ID)     ON DELETE CASCADE
);
"""

SEED_SQL = """
INSERT INTO Customer (Full_Name, Email, Wallet_Balance) VALUES
    ('Ayesha Khan',   'ayesha.khan@gmail.com',  1500.00),
    ('Bilal Ahmed',   'bilal.ahmed@hotmail.com',  750.50),
    ('Sara Malik',    'sara.malik@yahoo.com',    2200.00),
    ('Usman Tariq',   'usman.tariq@gmail.com',    300.00),
    ('Hina Chaudhry', 'hina.ch@outlook.com',      950.75);

INSERT INTO Customer_Contact (Customer_ID, Phone_Number, Contact_Type) VALUES
    (1,'0300-1234567','primary'),(1,'0321-9876543','secondary'),
    (2,'0333-4567890','primary'),(3,'0345-6789012','primary'),
    (3,'0311-1122334','secondary'),(4,'0322-9988776','primary'),
    (5,'0301-5544332','primary');

INSERT INTO Saved_Address (Customer_ID, Address_Label, Street, City, Zip, Delivery_Instructions) VALUES
    (1,'Home','12-A Gulshan Block 3','Karachi','75300','Ring bell twice'),
    (1,'Office','4th Floor Plaza 21 I-8','Islamabad','44000','Lobby reception'),
    (2,'Home','23 Johar Town Phase 2','Lahore','54782','Gate code: 1234'),
    (3,'Home','7-B DHA Phase 5','Lahore','54810',NULL),
    (4,'Hostel','Block C FAST University','Islamabad','44020','Call on arrival'),
    (5,'Home','88 Satellite Town G-3','Rawalpindi','46000',NULL);

INSERT INTO Rider (Full_Name, Vehicle_Reg, Shift_Status) VALUES
    ('Kamran Ali',      'LHR-2345', 'active'),
    ('Zain Hussain',    'ISB-8871', 'active'),
    ('Farhan Siddiqui', 'KHI-6630', 'on_break'),
    ('Asad Mehmood',    'RWP-1192', 'inactive'),
    ('Omer Butt',       'LHR-5509', 'active');

INSERT INTO Rider_Contact (Rider_ID, Phone_Number, Contact_Type) VALUES
    (1,'0302-1112233','primary'),(2,'0315-4445566','primary'),
    (2,'0300-9998877','secondary'),(3,'0344-7778899','primary'),
    (4,'0321-6665544','primary'),(5,'0303-3332211','primary');

INSERT INTO Restaurant (Rest_Name, Operating_Status, Rating) VALUES
    ('Monal Grill','open',4.7),('Howdy BBQ','open',4.5),
    ('Savour Foods','busy',4.3),('Meat the Cheese','open',4.6),
    ('The Burning Brownie','closed',4.8);

INSERT INTO Menu_Item (Restaurant_ID, Item_Name, Price, Category) VALUES
    (1,'Chicken Karahi',850.00,'Main Course'),(1,'Mutton Namkeen',1100.00,'Main Course'),
    (1,'Garlic Naan',60.00,'Bread'),(1,'Raita',80.00,'Side'),
    (2,'BBQ Platter (Full)',1400.00,'Main Course'),(2,'Seekh Kebab (6 pcs)',450.00,'Starter'),
    (2,'Chapli Kebab',350.00,'Starter'),(2,'Cold Drink',80.00,'Beverage'),
    (3,'Paya',650.00,'Main Course'),(3,'Nihari',750.00,'Main Course'),
    (3,'Kulcha',50.00,'Bread'),
    (4,'Classic Burger',550.00,'Burger'),(4,'Double Smash Burger',850.00,'Burger'),
    (4,'Loaded Fries',350.00,'Side'),(4,'Milkshake',300.00,'Beverage'),
    (5,'Lava Brownie',350.00,'Dessert'),(5,'Nutella Waffle',420.00,'Dessert'),
    (5,'Cold Coffee',280.00,'Beverage');

INSERT INTO Order_Record (Customer_ID, Rider_ID, Total_Amount, Order_Status, Order_Time) VALUES
    (1,1,1910.00,'delivered','2025-06-01 12:30:00'),
    (2,2,1480.00,'on_the_way','2025-06-02 13:15:00'),
    (3,5,1150.00,'delivered','2025-06-02 19:00:00'),
    (4,1,700.00,'pending','2025-06-03 09:45:00'),
    (5,3,1200.00,'preparing','2025-06-03 20:10:00'),
    (1,2,2500.00,'delivered','2025-06-04 14:00:00'),
    (3,5,900.00,'cancelled','2025-06-04 18:30:00'),
    (2,1,1730.00,'delivered','2025-06-05 12:00:00');

INSERT INTO Live_Tracking (Order_ID, Estimated_Arrival, Ping_Status) VALUES
    (2,'2025-06-02 13:45:00','active'),(4,'2025-06-03 10:15:00','active'),
    (5,'2025-06-03 20:40:00','idle'),(1,'2025-06-01 13:00:00','completed'),
    (3,'2025-06-02 19:30:00','completed'),(6,'2025-06-04 14:30:00','completed'),
    (8,'2025-06-05 12:25:00','completed');

INSERT INTO Order_Details (Order_ID, Item_ID, Quantity) VALUES
    (1,1,1),(1,3,3),(1,4,2),
    (2,5,1),(2,8,2),
    (3,13,1),(3,14,1),(3,15,1),
    (4,10,1),(4,11,2),
    (5,12,2),(5,14,1),
    (6,2,2),(6,3,3),
    (7,9,1),(7,11,2),
    (8,6,2),(8,7,1),(8,8,3);
"""


# ─── Database helpers ─────────────────────────────────────────────────────────

def get_connection():
    """Return a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed data if the database does not yet exist."""
    if not os.path.exists(DB_PATH):
        conn = get_connection()
        try:
            # Execute schema statements one by one (executescript auto-commits)
            conn.executescript(SCHEMA_SQL)
            conn.executescript(SEED_SQL)
            conn.commit()
        except Exception as e:
            st.error(f"Database initialisation failed: {e}")
        finally:
            conn.close()


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SELECT and return a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def run_write(sql: str, params: tuple = ()):
    """Execute an INSERT/UPDATE/DELETE and commit. Returns last row id."""
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        st.error(f"Integrity error: {e}")
        return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        conn.close()


# ─── Utility helpers ──────────────────────────────────────────────────────────

def status_badge(status: str) -> str:
    colours = {
        "active": "🟢", "inactive": "🔴", "on_break": "🟡",
        "open": "🟢", "closed": "🔴", "busy": "🟡",
        "pending": "🔵", "preparing": "🟡", "on_the_way": "🟠",
        "delivered": "🟢", "cancelled": "🔴",
    }
    return f"{colours.get(status, '⚪')} {status}"


def section_header(icon: str, title: str):
    st.markdown(f"## {icon} {title}")
    st.divider()


# ─── Page: Customers ──────────────────────────────────────────────────────────

def page_customers():
    section_header("👤", "Customer Management")

    tab1, tab2, tab3 = st.tabs(["📋 View Customers", "➕ Add Customer", "📍 Saved Addresses"])

    # ── View ──
    with tab1:
        df = run_query("""
            SELECT c.Customer_ID, c.Full_Name, c.Email,
                   printf('PKR %.2f', c.Wallet_Balance) AS Wallet_Balance,
                   GROUP_CONCAT(cc.Phone_Number || ' (' || cc.Contact_Type || ')', ' | ') AS Contacts
            FROM Customer c
            LEFT JOIN Customer_Contact cc ON c.Customer_ID = cc.Customer_ID
            GROUP BY c.Customer_ID
        """)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No customers found.")

    # ── Add Customer ──
    with tab2:
        with st.form("add_customer_form"):
            st.subheader("New Customer")
            col1, col2 = st.columns(2)
            name   = col1.text_input("Full Name*")
            email  = col2.text_input("Email*")
            wallet = st.number_input("Initial Wallet Balance (PKR)", min_value=0.0, step=50.0)
            phone1 = st.text_input("Primary Phone*")
            phone2 = st.text_input("Secondary Phone (optional)")
            submitted = st.form_submit_button("Add Customer", type="primary")

        if submitted:
            if not name or not email or not phone1:
                st.warning("Name, email, and primary phone are required.")
            else:
                cid = run_write(
                    "INSERT INTO Customer (Full_Name, Email, Wallet_Balance) VALUES (?,?,?)",
                    (name, email, wallet)
                )
                if cid:
                    run_write(
                        "INSERT INTO Customer_Contact (Customer_ID, Phone_Number, Contact_Type) VALUES (?,?,'primary')",
                        (cid, phone1)
                    )
                    if phone2:
                        run_write(
                            "INSERT INTO Customer_Contact (Customer_ID, Phone_Number, Contact_Type) VALUES (?,?,'secondary')",
                            (cid, phone2)
                        )
                    st.success(f"✅ Customer '{name}' added with ID {cid}.")

    # ── Saved Addresses ──
    with tab3:
        customers = run_query("SELECT Customer_ID, Full_Name FROM Customer")
        if customers.empty:
            st.info("Add a customer first.")
        else:
            selected_cid = st.selectbox(
                "Select Customer",
                customers["Customer_ID"],
                format_func=lambda i: customers.loc[customers["Customer_ID"]==i,"Full_Name"].values[0]
            )
            addrs = run_query(
                "SELECT Address_Label, Street, City, Zip, Delivery_Instructions FROM Saved_Address WHERE Customer_ID=?",
                (selected_cid,)
            )
            if not addrs.empty:
                st.dataframe(addrs, use_container_width=True, hide_index=True)
            else:
                st.info("No saved addresses for this customer.")

            st.subheader("Add New Address")
            with st.form("add_address_form"):
                col1, col2 = st.columns(2)
                label  = col1.text_input("Address Label*  (e.g. Home)")
                street = col2.text_input("Street*")
                city   = col1.text_input("City*")
                zip_   = col2.text_input("ZIP Code*")
                instr  = st.text_input("Delivery Instructions (optional)")
                sub2   = st.form_submit_button("Save Address", type="primary")

            if sub2:
                if not label or not street or not city or not zip_:
                    st.warning("Label, street, city, and ZIP are required.")
                else:
                    result = run_write(
                        "INSERT INTO Saved_Address VALUES (?,?,?,?,?,?)",
                        (selected_cid, label, street, city, zip_, instr or None)
                    )
                    if result is not None:
                        st.success(f"✅ Address '{label}' saved.")


# ─── Page: Riders ─────────────────────────────────────────────────────────────

def page_riders():
    section_header("🛵", "Rider Fleet Management")

    tab1, tab2 = st.tabs(["📋 View Riders", "➕ Add Rider"])

    with tab1:
        df = run_query("""
            SELECT r.Rider_ID, r.Full_Name, r.Vehicle_Reg, r.Shift_Status,
                   GROUP_CONCAT(rc.Phone_Number || ' (' || rc.Contact_Type || ')', ' | ') AS Contacts
            FROM Rider r
            LEFT JOIN Rider_Contact rc ON r.Rider_ID = rc.Rider_ID
            GROUP BY r.Rider_ID
        """)
        if not df.empty:
            df["Shift_Status"] = df["Shift_Status"].apply(status_badge)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No riders found.")

        # Quick status update
        st.subheader("Update Shift Status")
        riders_raw = run_query("SELECT Rider_ID, Full_Name, Shift_Status FROM Rider")
        if not riders_raw.empty:
            col1, col2, col3 = st.columns(3)
            chosen_id = col1.selectbox(
                "Rider",
                riders_raw["Rider_ID"],
                format_func=lambda i: riders_raw.loc[riders_raw["Rider_ID"]==i,"Full_Name"].values[0]
            )
            new_status = col2.selectbox("New Status", ["active", "inactive", "on_break"])
            if col3.button("Update", type="primary"):
                run_write("UPDATE Rider SET Shift_Status=? WHERE Rider_ID=?", (new_status, chosen_id))
                st.success("✅ Status updated.")
                st.rerun()

    with tab2:
        with st.form("add_rider_form"):
            st.subheader("New Rider")
            col1, col2 = st.columns(2)
            name    = col1.text_input("Full Name*")
            veh     = col2.text_input("Vehicle Registration*  (e.g. LHR-1234)")
            status  = col1.selectbox("Shift Status", ["active", "inactive", "on_break"])
            phone1  = col2.text_input("Primary Phone*")
            phone2  = st.text_input("Secondary Phone (optional)")
            sub     = st.form_submit_button("Add Rider", type="primary")

        if sub:
            if not name or not veh or not phone1:
                st.warning("Name, vehicle reg, and primary phone are required.")
            else:
                rid = run_write(
                    "INSERT INTO Rider (Full_Name, Vehicle_Reg, Shift_Status) VALUES (?,?,?)",
                    (name, veh, status)
                )
                if rid:
                    run_write(
                        "INSERT INTO Rider_Contact (Rider_ID, Phone_Number, Contact_Type) VALUES (?,?,'primary')",
                        (rid, phone1)
                    )
                    if phone2:
                        run_write(
                            "INSERT INTO Rider_Contact (Rider_ID, Phone_Number, Contact_Type) VALUES (?,?,'secondary')",
                            (rid, phone2)
                        )
                    st.success(f"✅ Rider '{name}' added with ID {rid}.")


# ─── Page: Restaurants & Menu ─────────────────────────────────────────────────

def page_restaurants():
    section_header("🍽️", "Restaurant & Menu Management")

    tab1, tab2, tab3 = st.tabs(["📋 Restaurants", "➕ Add Restaurant", "🍱 Menu Items"])

    with tab1:
        df = run_query("SELECT * FROM Restaurant ORDER BY Restaurant_ID")
        if not df.empty:
            df["Operating_Status"] = df["Operating_Status"].apply(status_badge)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No restaurants found.")

    with tab2:
        with st.form("add_rest_form"):
            col1, col2 = st.columns(2)
            rname   = col1.text_input("Restaurant Name*")
            rstatus = col2.selectbox("Operating Status", ["open", "busy", "closed"])
            rating  = st.slider("Rating", 0.0, 5.0, 4.0, 0.1)
            sub     = st.form_submit_button("Add Restaurant", type="primary")

        if sub:
            if not rname:
                st.warning("Restaurant name is required.")
            else:
                rid = run_write(
                    "INSERT INTO Restaurant (Rest_Name, Operating_Status, Rating) VALUES (?,?,?)",
                    (rname, rstatus, rating)
                )
                if rid:
                    st.success(f"✅ Restaurant '{rname}' added with ID {rid}.")

    with tab3:
        rests = run_query("SELECT Restaurant_ID, Rest_Name FROM Restaurant")
        if rests.empty:
            st.info("Add a restaurant first.")
            return

        sel_rest = st.selectbox(
            "Select Restaurant",
            rests["Restaurant_ID"],
            format_func=lambda i: rests.loc[rests["Restaurant_ID"]==i,"Rest_Name"].values[0]
        )
        menu_df = run_query(
            "SELECT Item_ID, Item_Name, Category, printf('PKR %.2f', Price) AS Price FROM Menu_Item WHERE Restaurant_ID=?",
            (sel_rest,)
        )
        if not menu_df.empty:
            st.dataframe(menu_df, use_container_width=True, hide_index=True)
        else:
            st.info("No menu items yet.")

        st.subheader("Add Menu Item")
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            iname    = col1.text_input("Item Name*")
            category = col2.text_input("Category*  (e.g. Main Course, Burger)")
            price    = st.number_input("Price (PKR)*", min_value=1.0, step=10.0)
            sub2     = st.form_submit_button("Add Item", type="primary")

        if sub2:
            if not iname or not category:
                st.warning("Item name and category are required.")
            else:
                iid = run_write(
                    "INSERT INTO Menu_Item (Restaurant_ID, Item_Name, Price, Category) VALUES (?,?,?,?)",
                    (sel_rest, iname, price, category)
                )
                if iid:
                    st.success(f"✅ '{iname}' added to menu.")


# ─── Page: Orders ─────────────────────────────────────────────────────────────

def page_orders():
    section_header("📦", "Order Management")

    tab1, tab2 = st.tabs(["📋 All Orders", "🛒 Place New Order"])

    with tab1:
        df = run_query("""
            SELECT o.Order_ID,
                   c.Full_Name      AS Customer,
                   r.Full_Name      AS Rider,
                   o.Order_Status,
                   printf('PKR %.2f', o.Total_Amount) AS Total,
                   o.Order_Time
            FROM Order_Record o
            JOIN Customer c ON o.Customer_ID = c.Customer_ID
            JOIN Rider    r ON o.Rider_ID    = r.Rider_ID
            ORDER BY o.Order_ID DESC
        """)
        if not df.empty:
            df["Order_Status"] = df["Order_Status"].apply(status_badge)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No orders found.")

        # Update order status
        st.subheader("Update Order Status")
        orders_raw = run_query("SELECT Order_ID, Order_Status FROM Order_Record")
        if not orders_raw.empty:
            col1, col2, col3 = st.columns(3)
            oid        = col1.selectbox("Order ID", orders_raw["Order_ID"])
            new_ostatus = col2.selectbox(
                "New Status",
                ["pending","preparing","on_the_way","delivered","cancelled"]
            )
            if col3.button("Update Order", type="primary"):
                run_write("UPDATE Order_Record SET Order_Status=? WHERE Order_ID=?", (new_ostatus, oid))
                st.success("✅ Order status updated.")
                st.rerun()

    with tab2:
        st.subheader("Place a New Order")
        customers = run_query("SELECT Customer_ID, Full_Name FROM Customer")
        active_riders = run_query("SELECT Rider_ID, Full_Name FROM Rider WHERE Shift_Status='active'")
        restaurants = run_query("SELECT Restaurant_ID, Rest_Name FROM Restaurant WHERE Operating_Status != 'closed'")

        if customers.empty or active_riders.empty or restaurants.empty:
            st.warning("Need at least one customer, one active rider, and one open restaurant.")
            return

        col1, col2 = st.columns(2)
        sel_cust = col1.selectbox(
            "Customer*",
            customers["Customer_ID"],
            format_func=lambda i: customers.loc[customers["Customer_ID"]==i,"Full_Name"].values[0]
        )
        sel_rider = col2.selectbox(
            "Rider*",
            active_riders["Rider_ID"],
            format_func=lambda i: active_riders.loc[active_riders["Rider_ID"]==i,"Full_Name"].values[0]
        )
        sel_rest = st.selectbox(
            "Restaurant*",
            restaurants["Restaurant_ID"],
            format_func=lambda i: restaurants.loc[restaurants["Restaurant_ID"]==i,"Rest_Name"].values[0]
        )

        menu = run_query(
            "SELECT Item_ID, Item_Name, Price, Category FROM Menu_Item WHERE Restaurant_ID=?",
            (sel_rest,)
        )

        if menu.empty:
            st.info("This restaurant has no menu items yet.")
            return

        st.markdown("**Select Items & Quantities**")
        order_items = {}
        cols = st.columns(3)
        for idx, row in menu.iterrows():
            with cols[idx % 3]:
                qty = st.number_input(
                    f"{row['Item_Name']}\n PKR {row['Price']:.0f}",
                    min_value=0, max_value=20, step=1,
                    key=f"item_{row['Item_ID']}"
                )
                if qty > 0:
                    order_items[row["Item_ID"]] = (qty, row["Price"])

        # Compute total
        total = sum(q * p for (q, p) in order_items.values())
        st.metric("Order Total", f"PKR {total:.2f}")

        if st.button("🛒 Confirm Order", type="primary", disabled=(total == 0)):
            oid = run_write(
                "INSERT INTO Order_Record (Customer_ID, Rider_ID, Total_Amount, Order_Status) VALUES (?,?,?,'pending')",
                (sel_cust, sel_rider, total)
            )
            if oid:
                for item_id, (qty, _) in order_items.items():
                    run_write(
                        "INSERT INTO Order_Details (Order_ID, Item_ID, Quantity) VALUES (?,?,?)",
                        (oid, item_id, qty)
                    )
                # Create a tracking entry automatically
                eta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                run_write(
                    "INSERT INTO Live_Tracking (Order_ID, Estimated_Arrival, Ping_Status) VALUES (?,?,'active')",
                    (oid, eta)
                )
                st.success(f"✅ Order #{oid} placed! Total: PKR {total:.2f}")
                st.balloons()


# ─── Page: Rubric Queries & Analytics ────────────────────────────────────────

def page_analytics():
    section_header("📊", "Rubric Queries & Analytics")

    st.markdown("""
    > This dashboard executes the **three required queries** from the CS160 rubric
    > directly against the live SQLite database and displays results in interactive tables.
    """)

    # ── Query 1: Basic SELECT ──────────────────────────────────────────────────
    st.subheader("🔍 Query 1 — Basic SELECT: Active Riders")
    st.code("""
SELECT Rider_ID, Full_Name, Vehicle_Reg, Shift_Status
FROM   Rider
WHERE  Shift_Status = 'active'
ORDER  BY Rider_ID;
    """, language="sql")

    df1 = run_query(
        "SELECT Rider_ID, Full_Name, Vehicle_Reg, Shift_Status FROM Rider WHERE Shift_Status='active' ORDER BY Rider_ID"
    )
    if not df1.empty:
        st.dataframe(df1, use_container_width=True, hide_index=True)
        st.success(f"✅ {len(df1)} active rider(s) found.")
    else:
        st.warning("No active riders at the moment.")

    st.divider()

    # ── Query 2: JOIN ──────────────────────────────────────────────────────────
    st.subheader("🔗 Query 2 — JOIN: Full Order Receipt")
    st.code("""
SELECT o.Order_ID, c.Full_Name AS Customer_Name, r.Full_Name AS Rider_Name,
       o.Order_Status, o.Total_Amount, o.Order_Time
FROM       Order_Record o
INNER JOIN Customer     c ON o.Customer_ID = c.Customer_ID
INNER JOIN Rider        r ON o.Rider_ID    = r.Rider_ID
WHERE o.Order_ID = :id;
    """, language="sql")

    orders_list = run_query("SELECT Order_ID FROM Order_Record ORDER BY Order_ID")
    if orders_list.empty:
        st.info("No orders in the database yet.")
    else:
        sel_oid = st.selectbox("Select Order ID to view receipt", orders_list["Order_ID"])
        df2 = run_query("""
            SELECT o.Order_ID,
                   c.Full_Name      AS Customer_Name,
                   r.Full_Name      AS Rider_Name,
                   o.Order_Status,
                   o.Total_Amount,
                   o.Order_Time
            FROM       Order_Record o
            INNER JOIN Customer      c ON o.Customer_ID = c.Customer_ID
            INNER JOIN Rider         r ON o.Rider_ID    = r.Rider_ID
            WHERE o.Order_ID = ?
        """, (sel_oid,))
        if not df2.empty:
            # Display as a pretty "receipt"
            row = df2.iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("Customer", row["Customer_Name"])
            col2.metric("Rider", row["Rider_Name"])
            col3.metric("Total", f"PKR {row['Total_Amount']:.2f}")
            col1.metric("Status", row["Order_Status"].replace("_", " ").title())
            col2.metric("Order Time", row["Order_Time"])

            # Show line items
            items_df = run_query("""
                SELECT mi.Item_Name, mi.Category,
                       od.Quantity,
                       printf('PKR %.2f', mi.Price) AS Unit_Price,
                       printf('PKR %.2f', od.Quantity * mi.Price) AS Line_Total
                FROM   Order_Details od
                JOIN   Menu_Item mi ON od.Item_ID = mi.Item_ID
                WHERE  od.Order_ID = ?
            """, (sel_oid,))
            if not items_df.empty:
                st.markdown("**Order Line Items:**")
                st.dataframe(items_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Query 3: AGGREGATE ────────────────────────────────────────────────────
    st.subheader("💰 Query 3 — AGGREGATE: Restaurant Revenue")
    st.code("""
SELECT rst.Restaurant_ID, rst.Rest_Name,
       SUM(od.Quantity * mi.Price)  AS Total_Revenue,
       COUNT(DISTINCT o.Order_ID)   AS Orders_Fulfilled
FROM       Restaurant   rst
INNER JOIN Menu_Item    mi  ON rst.Restaurant_ID = mi.Restaurant_ID
INNER JOIN Order_Details od ON mi.Item_ID        = od.Item_ID
INNER JOIN Order_Record  o  ON od.Order_ID       = o.Order_ID
WHERE o.Order_Status = 'delivered'
GROUP BY rst.Restaurant_ID, rst.Rest_Name
ORDER BY Total_Revenue DESC;
    """, language="sql")

    df3 = run_query("""
        SELECT rst.Restaurant_ID,
               rst.Rest_Name,
               SUM(od.Quantity * mi.Price)  AS Total_Revenue,
               COUNT(DISTINCT o.Order_ID)   AS Orders_Fulfilled
        FROM       Restaurant   rst
        INNER JOIN Menu_Item    mi  ON rst.Restaurant_ID = mi.Restaurant_ID
        INNER JOIN Order_Details od ON mi.Item_ID        = od.Item_ID
        INNER JOIN Order_Record  o  ON od.Order_ID       = o.Order_ID
        WHERE o.Order_Status = 'delivered'
        GROUP BY rst.Restaurant_ID, rst.Rest_Name
        ORDER BY Total_Revenue DESC
    """)
    if not df3.empty:
        # Bar chart
        st.bar_chart(df3.set_index("Rest_Name")["Total_Revenue"])
        df3["Total_Revenue"] = df3["Total_Revenue"].apply(lambda x: f"PKR {x:,.2f}")
        st.dataframe(df3, use_container_width=True, hide_index=True)
    else:
        st.info("No delivered orders to calculate revenue from yet.")


# ─── Main App Shell ───────────────────────────────────────────────────────────

def main():
    # Page config
    st.set_page_config(
        page_title="FoodPanda DB — CS160",
        page_icon="🍕",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialise database on first run
    init_db()

    # Sidebar navigation
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/a/a7/Foodpanda_logo.png",
            width=160
        )
        st.markdown("### CS160 — Database Systems")
        st.markdown("**Foodpanda: Cloud Kitchen &  Rider Fleet Logistics**")
        st.divider()

        page = st.radio(
            "Navigate",
            ["👤 Customers", "🛵 Riders", "🍽️ Restaurants", "📦 Orders", "📊 Analytics"],
            label_visibility="collapsed"
        )
        st.divider()
        st.caption("SQLite · Streamlit · Python")

        # DB reset (dev convenience)
        with st.expander("⚙️ Dev Tools"):
            if st.button("🔄 Reset & Reseed Database", type="secondary"):
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                init_db()
                st.success("Database reset.")
                st.rerun()

    # Route to correct page
    if page == "👤 Customers":
        page_customers()
    elif page == "🛵 Riders":
        page_riders()
    elif page == "🍽️ Restaurants":
        page_restaurants()
    elif page == "📦 Orders":
        page_orders()
    elif page == "📊 Analytics":
        page_analytics()


if __name__ == "__main__":
    main()
PYEOF
echo "Done"