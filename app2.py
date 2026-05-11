# =============================================================================
# CS160 Database Systems | Foodpanda: Cloud Kitchen & Rider Fleet Logistics
# Streamlit Frontend — app.py (Lookmaxxed Edition ✨)
# Run: streamlit run app.py
# =============================================================================

import sqlite3
import os
import streamlit as st
import pandas as pd
from datetime import datetime

# ─── Constants & Branding ─────────────────────────────────────────────────────
DB_PATH = "foodpanda.db"
FP_PINK = "#D70F64"

# Custom CSS Injector for maximum aesthetic polish
CUSTOM_CSS = """
<style>
    /* Clean up standard container padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }
    /* Gorgeous styled metric cards with Foodpanda pink accents */
    div[data-testid="stMetric"] {
        background-color: rgba(215, 15, 100, 0.04);
        border-left: 5px solid #D70F64;
        padding: 1rem 1.25rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        transition: transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
    }
    /* Refined form containers */
    div[data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(215, 15, 100, 0.15);
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    /* Subtle custom header gradients */
    .glow-title {
        background: linear-gradient(90deg, #D70F64 0%, #FF5A92 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0px;
    }
</style>
"""

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

# ─── Database Helpers ─────────────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_connection()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.executescript(SEED_SQL)
            conn.commit()
        except Exception as e:
            st.error(f"Database setup error: {e}")
        finally:
            conn.close()

def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        st.error(f"Execution Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def run_write(sql: str, params: tuple = ()):
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        st.error(f"Constraint Conflict: {e}")
        return None
    except Exception as e:
        st.error(f"Write Error: {e}")
        return None
    finally:
        conn.close()

# ─── Beautiful Component Helpers ──────────────────────────────────────────────

def status_badge(status: str) -> str:
    colours = {
        "active": "🟢 Active", "inactive": "🔴 Inactive", "on_break": "🟡 On Break",
        "open": "🟢 Open", "closed": "🔴 Closed", "busy": "🟡 Busy",
        "pending": "⏳ Pending", "preparing": "🍳 Preparing", "on_the_way": "🛵 On The Way",
        "delivered": "✅ Delivered", "cancelled": "❌ Cancelled",
    }
    return colours.get(status, f"⚪ {status.title()}")

def section_header(title: str, subtitle: str):
    st.markdown(f"<h2 class='glow-title'>{title}</h2>", unsafe_allow_html=True)
    st.caption(subtitle)
    st.write("") # Smooth spacing

# ─── Page: Customers ──────────────────────────────────────────────────────────

def page_customers():
    section_header("Customer Management", "Manage user balance, contact profiles, and saved delivery zones.")
    
    # Core Overview Deck
    summary = run_query("SELECT COUNT(*) as c, SUM(Wallet_Balance) as w FROM Customer")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Active Customers", f"{summary.iloc[0]['c']}")
    c2.metric("Total Ecosystem Wallet", f"PKR {summary.iloc[0]['w']:,.2f}")
    c3.metric("Avg Balance / User", f"PKR {summary.iloc[0]['w'] / max(1, summary.iloc[0]['c']):,.2f}")
    
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📋 Customer Directory", "➕ Provision Account", "📍 Address Books"])

    with tab1:
        df = run_query("""
            SELECT c.Customer_ID, c.Full_Name, c.Email,
                   printf('PKR %.2f', c.Wallet_Balance) AS Wallet_Balance,
                   GROUP_CONCAT(cc.Phone_Number || ' (' || cc.Contact_Type || ')', ' | ') AS Contacts
            FROM Customer c
            LEFT JOIN Customer_Contact cc ON c.Customer_ID = cc.Customer_ID
            GROUP BY c.Customer_ID
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        with st.form("add_customer_form"):
            st.subheader("Register Customer Profile")
            col1, col2 = st.columns(2)
            name   = col1.text_input("Full Name*", placeholder="e.g. Ali Reza")
            email  = col2.text_input("Email Address*", placeholder="name@domain.pk")
            wallet = col1.number_input("Starting Wallet Load (PKR)", min_value=0.0, step=500.0)
            phone1 = col2.text_input("Primary Direct Dial*", placeholder="03xx-xxxxxxx")
            phone2 = st.text_input("Secondary Phone (Optional)", placeholder="Backup contact")
            
            submitted = st.form_submit_button("Launch Account", type="primary")

        if submitted:
            if not name or not email or not phone1:
                st.warning("⚠️ Full Name, Email, and Primary Dial are mandatory.")
            else:
                cid = run_write("INSERT INTO Customer (Full_Name, Email, Wallet_Balance) VALUES (?,?,?)", (name, email, wallet))
                if cid:
                    run_write("INSERT INTO Customer_Contact (Customer_ID, Phone_Number, Contact_Type) VALUES (?,?,'primary')", (cid, phone1))
                    if phone2:
                        run_write("INSERT INTO Customer_Contact (Customer_ID, Phone_Number, Contact_Type) VALUES (?,?,'secondary')", (cid, phone2))
                    st.success(f"🚀 Customer '{name}' online! ID: #{cid}")

    with tab3:
        customers = run_query("SELECT Customer_ID, Full_Name FROM Customer")
        if not customers.empty:
            c_sel = st.selectbox("Filter by Account Owner", customers["Customer_ID"], format_func=lambda i: customers.loc[customers["Customer_ID"]==i,"Full_Name"].values[0])
            addrs = run_query("SELECT Address_Label, Street, City, Zip, Delivery_Instructions FROM Saved_Address WHERE Customer_ID=?", (c_sel,))
            
            if not addrs.empty:
                st.dataframe(addrs, use_container_width=True, hide_index=True)
            else:
                st.info("No addresses stored for this profile.")
                
            st.write("")
            with st.form("add_address_form"):
                st.subheader("Map New Hub")
                col1, col2 = st.columns(2)
                label  = col1.text_input("Label*", placeholder="Home, Office, Lab")
                street = col2.text_input("Street Address*", placeholder="House/Apt, Block, Sector")
                city   = col1.text_input("City*", placeholder="Islamabad")
                zip_   = col2.text_input("Postal/Zip*", placeholder="44000")
                instr  = st.text_input("Rider Navigation Guidelines", placeholder="e.g., Leave with guard")
                sub2   = st.form_submit_button("Commit Address", type="primary")

            if sub2:
                if not label or not street or not city or not zip_:
                    st.warning("⚠️ All primary address tags are required.")
                else:
                    res = run_write("INSERT INTO Saved_Address VALUES (?,?,?,?,?,?)", (c_sel, label, street, city, zip_, instr or None))
                    if res is not None:
                        st.success(f"📍 Address '{label}' secured.")

# ─── Page: Riders ─────────────────────────────────────────────────────────────

def page_riders():
    section_header("Rider Fleet Command", "Monitor active shift tracking, dispatch telemetry, and vehicle assignments.")

    # High-impact Fleet Overview
    stats = run_query("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN Shift_Status='active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN Shift_Status='on_break' THEN 1 ELSE 0 END) as on_break
        FROM Rider
    """)
    r1, r2, r3 = st.columns(3)
    r1.metric("Registered Couriers", f"{stats.iloc[0]['total']}")
    r2.metric("🟢 Active On-Grid", f"{stats.iloc[0]['active']}")
    r3.metric("🟡 Currently Resting", f"{stats.iloc[0]['on_break']}")
    
    st.divider()

    tab1, tab2 = st.tabs(["🛵 Grid Deployment", "➕ Commission Rider"])

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

        st.subheader("Shift Dispatching Override")
        r_raw = run_query("SELECT Rider_ID, Full_Name, Shift_Status FROM Rider")
        if not r_raw.empty:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                c_id = col1.selectbox("Select Target Courier", r_raw["Rider_ID"], format_func=lambda i: r_raw.loc[r_raw["Rider_ID"]==i,"Full_Name"].values[0])
                n_stat = col2.selectbox("Dispatch Status Command", ["active", "inactive", "on_break"])
                st.write("") # Alignment push
                if col3.button("Execute Override", type="primary", use_container_width=True):
                    run_write("UPDATE Rider SET Shift_Status=? WHERE Rider_ID=?", (n_stat, c_id))
                    st.success("⚡ Telemetry Updated successfully.")
                    st.rerun()

    with tab2:
        with st.form("add_rider_form"):
            st.subheader("Courier Fleet Enlistment")
            col1, col2 = st.columns(2)
            name    = col1.text_input("Full Legal Name*")
            veh     = col2.text_input("License Plate / Reg*", placeholder="e.g. LHR-7721")
            status  = col1.selectbox("Initial State", ["active", "inactive", "on_break"])
            phone1  = col2.text_input("Direct Mobile Link*")
            phone2  = st.text_input("Alternative Hotline")
            sub     = st.form_submit_button("Deploy Courier", type="primary")

        if sub:
            if not name or not veh or not phone1:
                st.warning("⚠️ Enter Name, Registration Plate, and Main Dial.")
            else:
                rid = run_write("INSERT INTO Rider (Full_Name, Vehicle_Reg, Shift_Status) VALUES (?,?,?)", (name, veh, status))
                if rid:
                    run_write("INSERT INTO Rider_Contact (Rider_ID, Phone_Number, Contact_Type) VALUES (?,?,'primary')", (rid, phone1))
                    if phone2:
                        run_write("INSERT INTO Rider_Contact (Rider_ID, Phone_Number, Contact_Type) VALUES (?,?,'secondary')", (rid, phone2))
                    st.success(f"🛵 Courier '{name}' attached to node #{rid}.")

# ─── Page: Restaurants & Menu ─────────────────────────────────────────────────

def page_restaurants():
    section_header("Vendor & SKU Database", "Cloud kitchen operations, live order throttling, and price catalogs.")

    tab1, tab2, tab3 = st.tabs(["🏪 Operational Kitchens", "➕ Setup Virtual Kitchen", "🍱 Product Categories"])

    with tab1:
        df = run_query("SELECT * FROM Restaurant ORDER BY Rating DESC")
        if not df.empty:
            df["Operating_Status"] = df["Operating_Status"].apply(status_badge)
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        with st.form("add_rest_form"):
            st.subheader("New Merchant Onboarding")
            col1, col2 = st.columns(2)
            rname   = col1.text_input("Vendor Brand Identity*")
            rstatus = col2.selectbox("Default Access Node", ["open", "busy", "closed"])
            rating  = st.slider("Preliminary Review Baseline", 0.0, 5.0, 4.5, 0.1)
            sub     = st.form_submit_button("Register Kitchen", type="primary")

        if sub and rname:
            rid = run_write("INSERT INTO Restaurant (Rest_Name, Operating_Status, Rating) VALUES (?,?,?)", (rname, rstatus, rating))
            if rid: st.success(f"🏪 Merchant '{rname}' secured at index #{rid}.")

    with tab3:
        rests = run_query("SELECT Restaurant_ID, Rest_Name FROM Restaurant")
        if not rests.empty:
            sel_rest = st.selectbox("Filter Vendor Engine", rests["Restaurant_ID"], format_func=lambda i: rests.loc[rests["Restaurant_ID"]==i,"Rest_Name"].values[0])
            menu_df = run_query("SELECT Item_ID, Item_Name, Category, printf('PKR %.2f', Price) AS Price FROM Menu_Item WHERE Restaurant_ID=?", (sel_rest,))
            st.dataframe(menu_df, use_container_width=True, hide_index=True)

            with st.form("add_item_form"):
                st.subheader("Inject Item into Catalog")
                col1, col2 = st.columns(2)
                iname    = col1.text_input("SKU Nomenclature*")
                category = col2.text_input("Menu Domain*", placeholder="Starter, Fast Food, Dessert")
                price    = st.number_input("Retail Price (PKR)*", min_value=1.0, step=50.0)
                sub2     = st.form_submit_button("Append SKU", type="primary")

            if sub2 and iname and category:
                run_write("INSERT INTO Menu_Item (Restaurant_ID, Item_Name, Price, Category) VALUES (?,?,?,?)", (sel_rest, iname, price, category))
                st.success(f"🍱 Added '{iname}' to active array.")

# ─── Page: Orders ─────────────────────────────────────────────────────────────

def page_orders():
    section_header("Live Processing Pipeline", "Dispatch center, real-time routing, and state transition monitoring.")

    tab1, tab2 = st.tabs(["📦 Full System Ledger", "🛒 Order Sandbox Engine"])

    with tab1:
        df = run_query("""
            SELECT o.Order_ID, c.Full_Name AS Customer, r.Full_Name AS Rider,
                   o.Order_Status, printf('PKR %.2f', o.Total_Amount) AS Total, o.Order_Time
            FROM Order_Record o
            JOIN Customer c ON o.Customer_ID = c.Customer_ID
            JOIN Rider r ON o.Rider_ID = r.Rider_ID
            ORDER BY o.Order_ID DESC
        """)
        if not df.empty:
            df["Order_Status"] = df["Order_Status"].apply(status_badge)
            st.dataframe(df, use_container_width=True, hide_index=True)