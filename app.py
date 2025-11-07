import streamlit as st
import json
from datetime import date, timedelta

# ---------------------------
# Page configuration & styles
# ---------------------------
st.set_page_config(page_title="Smart AI Assistant", layout="wide")
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        .metric-row { display: flex; gap: 1rem; flex-wrap: wrap; }
        .metric-card {
            border: 1px solid #eee; border-radius: 10px; padding: 0.8rem 1rem;
            background: #fafafa; flex: 1; min-width: 220px;
        }
    </style>
""", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>📦 Smart AI Assistant</h1>", unsafe_allow_html=True)

# ---------------------------
# Load data for HS/Duty tab
# ---------------------------
with open("hs_lookup_extended.json", "r") as f:
    full_data = json.load(f)

with open("form_dependencies.json", "r") as f:
    form_data = json.load(f)

product_names = form_data["product_names"]
product_to_countries = form_data["product_to_countries"]
product_country_to_descriptions = form_data["product_country_to_descriptions"]

# ------------------------------------------
# Helpers for the Indonesia Shipment simulator
# ------------------------------------------
# Fixed 4 products to choose from
SIM_PRODUCTS = ["mobile phone", "laptop computer", "men cotton shirt", "plastic chair"]

# Fixed origin and 4 destination options
ORIGIN = "Jakarta"
DESTS = ["Surabaya", "Bandung", "Medan", "Makassar"]

# Status by destination index: 0 -> picked up, 1 -> in transit, 2 & 3 -> at destination station
STATUS_BY_INDEX = {
    0: "Picked up",
    1: "In transit",
    2: "At destination station",
    3: "At destination station",
}

# Simple ETA map (business-like heuristic, in days)
ETA_DAYS = {
    "Surabaya": 2,
    "Bandung": 1,
    "Medan": 3,
    "Makassar": 4,
}

# Base RTO by lane + small product risk add-on (kept conservative, 0–25% clamp)
RTO_BASE_CITY = {
    "Surabaya": 7,
    "Bandung": 5,
    "Medan": 9,
    "Makassar": 11,
}
RTO_PRODUCT_RISK = {
    "mobile phone": 6,
    "laptop computer": 4,
    "men cotton shirt": 2,
    "plastic chair": 1,
}

def compute_eta_days(dest: str) -> int:
    return ETA_DAYS.get(dest, 3)

def compute_rto_percent(product: str, dest: str) -> int:
    base = RTO_BASE_CITY.get(dest, 8)
    risk = RTO_PRODUCT_RISK.get(product, 2)
    pct = base + risk
    return max(0, min(25, pct))  # clamp to 0–25%

# ---------------
# Tabs
# ---------------
tab1, tab2 = st.tabs(["Shipment Advisory (Indonesia)", "🧾 HS Code & Duty"])

# ============================================================================
# TAB 1: Indonesia shipment simulator (as per your new requirement)
# ============================================================================
with tab1:
    colL, colR = st.columns([1, 1])

    with colL:
        st.markdown("### 🚚 Shipment Details (Indonesia)")
        sel_product = st.selectbox("1) Product", SIM_PRODUCTS, index=0)
        st.text_input("2) Origin City", ORIGIN, disabled=True)
        sel_dest = st.selectbox("3) Destination City", DESTS, index=0)

        if st.button("Get ETA & RTO"):
            # Derive status from which destination index is chosen
            dest_index = DESTS.index(sel_dest)
            status = STATUS_BY_INDEX.get(dest_index, "In transit")

            eta_days = compute_eta_days(sel_dest)
            eta_date = date.today() + timedelta(days=eta_days)
            rto_pct = compute_rto_percent(sel_product, sel_dest)

            with colR:
                st.markdown("### 📊 Shipment Advisory")
                st.write(f"**Route:** {ORIGIN} → {sel_dest}")
                st.write(f"**Product:** {sel_product}")

                st.markdown('<div class="metric-row">', unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div><b>ETA (days)</b></div>
                        <div style="font-size:1.6rem;">{eta_days} days</div>
                        <div>Expected by: {eta_date.strftime('%d %b %Y')}</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div><b>RTO Probability</b></div>
                        <div style="font-size:1.6rem;">{rto_pct}%</div>
                        <div>({sel_product} to {sel_dest})</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="metric-card">
                        <div><b>Status</b></div>
                        <div style="font-size:1.6rem;">{status}</div>
                        <div>Auto-set by destination selection</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with colR:
                st.info("Fill the form on the left and click **Get ETA & RTO** to see results.")

# ============================================================================
# TAB 2: Original HS Code & Duty flow (preserved)
# ============================================================================
with tab2:
    col1, col2 = st.columns([1, 1])

    # === LEFT PANEL: FORM ===
    with col1:
        st.markdown("### 🧾 Shipment Details Form")

        selected_product = st.selectbox("1. Product Name", product_names, index=product_names.index("mobile phone") if "mobile phone" in product_names else 0)

        countries = product_to_countries.get(selected_product, [])
        selected_country = st.selectbox("2. Destination Country", countries)

        description_key = f"{selected_product}|{selected_country}"
        descriptions = product_country_to_descriptions.get(description_key, [])
        selected_description = st.selectbox("3. Product Description", descriptions)

        invoice_value = st.number_input("4. Invoice Value (USD)", min_value=0.0, step=10.0, value=1000.0)

        submitted = st.button("Calculate Duty")

    # === RIGHT PANEL: RESULTS ===
    with col2:
        st.markdown(
            "<h3 style='margin-top: 0.2rem; margin-bottom: 0.4rem;'>📊 Duty Calculation</h3>",
            unsafe_allow_html=True
        )
        result_container = st.container(height=500)

        with result_container:
            if submitted:
                match = next(
                    (
                        item for item in full_data
                        if item["product"] == selected_product and
                           item["destination"] == selected_country and
                           item["description"] == selected_description
                    ),
                    None
                )

                if match:
                    duty_percent = match["tariff_percent"]
                    estimated_duty = (duty_percent / 100.0) * invoice_value

                    st.success("✅ Match found!")
                    st.markdown(f"**HS Code:** `{match['hs_code']}`")
                    st.markdown(f"**Product:** {match['product']}")
                    st.markdown(f"**Description:** {match['description']}")
                    st.markdown(f"**Destination:** {match['destination']}")
                    st.markdown(f"**Tariff Rate:** `{duty_percent}%`")
                    st.markdown(f"**Invoice Value:** `${invoice_value:,.2f}`")
                    st.markdown(f"**Estimated Duty:** `${estimated_duty:,.2f}`")
                else:
                    st.error("❌ No matching record found. Please check your selection.")
            else:
                st.info("Fill the form and click 'Calculate Duty' to see results.")
