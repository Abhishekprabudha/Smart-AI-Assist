import streamlit as st
import json

# Page configuration
st.set_page_config(page_title="AI Advisory", layout="wide")

# Remove top padding for tighter layout
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>📦 AI Advisory - Harmonized Code & Duty Validator</h1>", unsafe_allow_html=True)

# Load data
with open("hs_lookup_expanded.json", "r") as f:
    full_data = json.load(f)

with open("form_dependencies.json", "r") as f:
    form_data = json.load(f)

product_names = form_data["product_names"]
product_to_countries = form_data["product_to_countries"]
product_country_to_descriptions = form_data["product_country_to_descriptions"]

# Streamlit form-based layout
col1, col2 = st.columns([1, 1])

# === LEFT PANEL: FORM ===
with col1:
    st.markdown("### 🧾 UPS Shipment Details Form")

    selected_product = st.selectbox("1. Product Name", product_names)

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
            # Find matching record
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
