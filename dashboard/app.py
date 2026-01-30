"""Streamlit dashboard for NPC E-commerce Sandbox."""

from datetime import datetime

import httpx
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="NPC E-commerce Sandbox",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API base URL
API_BASE_URL = "http://localhost:8000"


def get_api_data(endpoint: str) -> dict:
    """Fetch data from API."""
    try:
        response = httpx.get(f"{API_BASE_URL}{endpoint}", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data from {endpoint}: {str(e)}")
        return {}


def post_api_data(endpoint: str, data: dict) -> dict:
    """Post data to API."""
    try:
        response = httpx.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error posting to {endpoint}: {str(e)}")
        return {}


# Title and header
st.title("🛒 NPC E-commerce Sandbox")
st.markdown("**Multi-Agent Autonomous E-commerce Platform**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")

    # Simulation controls
    st.subheader("Simulation")

    scenario = st.selectbox(
        "Scenario",
        ["normal_operations", "flash_sale", "supply_shortage", "seasonal_peak"],
    )

    duration = st.slider("Duration (minutes)", 1, 120, 60)
    order_rate = st.slider("Order Rate (per minute)", 1, 60, 10)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Start", use_container_width=True):
            result = post_api_data(
                "/simulation/start",
                {
                    "scenario": scenario,
                    "duration_minutes": duration,
                    "order_rate": order_rate,
                },
            )
            if result:
                st.success("Simulation started!")

    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            result = post_api_data("/simulation/stop", {})
            if result:
                st.info("Simulation stopped")

    st.markdown("---")

    # Agent controls
    st.subheader("Agents")

    if st.button("🔍 Check Inventory", use_container_width=True):
        with st.spinner("Running inventory check..."):
            result = post_api_data("/agents/inventory/check", {"threshold": 20})
            if result:
                st.success("Inventory check complete!")

    if st.button("💰 Analyze Pricing", use_container_width=True):
        with st.spinner("Analyzing pricing..."):
            st.info("Pricing analysis not yet implemented")

    st.markdown("---")

    # Refresh
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Dashboard", "📦 Products", "📋 Orders", "🤖 Agents", "⚙️ Simulation"]
)

# Tab 1: Dashboard
with tab1:
    st.header("Dashboard Overview")

    # Fetch dashboard stats
    stats = get_api_data("/ecommerce/dashboard/stats")

    if stats:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Products",
                stats.get("total_products", 0),
                delta=None,
            )

        with col2:
            st.metric(
                "Total Orders",
                stats.get("total_orders", 0),
                delta=stats.get("orders_today", 0),
                delta_color="normal",
            )

        with col3:
            st.metric(
                "Total Revenue",
                f"${stats.get('total_revenue', 0):,.2f}",
                delta=f"${stats.get('revenue_today', 0):,.2f}",
                delta_color="normal",
            )

        with col4:
            st.metric(
                "Low Stock Items",
                stats.get("low_stock_count", 0),
                delta=None,
                delta_color="inverse",
            )

        st.markdown("---")

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Order Status Distribution")
            if "order_status_distribution" in stats:
                status_df = pd.DataFrame(
                    list(stats["order_status_distribution"].items()), columns=["Status", "Count"]
                )
                st.bar_chart(status_df.set_index("Status"))
            else:
                st.info("No order data available")

        with col2:
            st.subheader("Top Products by Revenue")
            if "top_products" in stats:
                products_df = pd.DataFrame(stats["top_products"])
                st.dataframe(products_df, use_container_width=True, hide_index=True)
            else:
                st.info("No product data available")

# Tab 2: Products
with tab2:
    st.header("Products & Inventory")

    products = get_api_data("/ecommerce/products")

    if products:
        products_df = pd.DataFrame(products)

        # Add inventory data
        inventory = get_api_data("/ecommerce/inventory")
        if inventory:
            inventory_df = pd.DataFrame(inventory)
            products_df = products_df.merge(
                inventory_df[["product_id", "quantity", "available_quantity"]],
                left_on="id",
                right_on="product_id",
                how="left",
            )

        # Display filters
        col1, col2 = st.columns(2)
        with col1:
            category_filter = st.multiselect(
                "Filter by Category",
                options=products_df["category"].unique() if "category" in products_df else [],
                default=None,
            )

        with col2:
            stock_filter = st.selectbox(
                "Stock Status",
                ["All", "In Stock", "Low Stock", "Out of Stock"],
            )

        # Apply filters
        filtered_df = products_df.copy()

        if category_filter:
            filtered_df = filtered_df[filtered_df["category"].isin(category_filter)]

        if stock_filter != "All" and "quantity" in filtered_df:
            if stock_filter == "In Stock":
                filtered_df = filtered_df[filtered_df["quantity"] > 20]
            elif stock_filter == "Low Stock":
                filtered_df = filtered_df[filtered_df["quantity"] <= 20]
            elif stock_filter == "Out of Stock":
                filtered_df = filtered_df[filtered_df["quantity"] == 0]

        # Display products
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "current_price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "base_price": st.column_config.NumberColumn("Base Price", format="$%.2f"),
                "quantity": st.column_config.NumberColumn("Stock"),
            },
        )
    else:
        st.info("No products available. Please seed the database first.")

# Tab 3: Orders
with tab3:
    st.header("Orders")

    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        ["all", "pending", "confirmed", "processing", "shipped", "delivered", "cancelled"],
    )

    # Fetch orders
    endpoint = "/ecommerce/orders"
    if status_filter != "all":
        endpoint += f"?status={status_filter}"

    orders = get_api_data(endpoint)

    if orders:
        orders_df = pd.DataFrame(orders)

        st.dataframe(
            orders_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "total": st.column_config.NumberColumn("Total", format="$%.2f"),
                "created_at": st.column_config.DatetimeColumn("Created"),
            },
        )
    else:
        st.info("No orders found")

# Tab 4: Agents
with tab4:
    st.header("Agent Activity")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🤖 Inventory Agent")
        st.markdown("**Status:** Active")
        st.markdown("**Last Action:** Checking inventory levels")

        if st.button("Run Inventory Check"):
            with st.spinner("Running inventory check..."):
                result = post_api_data("/agents/inventory/check", {"threshold": 20})
                if result:
                    st.success("Inventory check complete!")
                    st.json(result)

    with col2:
        st.subheader("💰 Pricing Agent")
        st.markdown("**Status:** Active")
        st.markdown("**Last Action:** Monitoring prices")

        st.info("Pricing agent controls coming soon")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Order Agent")
        st.markdown("**Status:** Active")
        st.markdown("**Last Action:** Processing orders")

        st.info("Order agent controls coming soon")

    with col2:
        st.subheader("💬 Support Agent")
        st.markdown("**Status:** Active")
        st.markdown("**Last Action:** Handling customer queries")

        customer_message = st.text_input("Test Support Agent")
        if st.button("Send Message"):
            if customer_message:
                with st.spinner("Processing..."):
                    result = post_api_data(
                        "/agents/support/message",
                        {"message": customer_message, "customer_id": "CUST-001"},
                    )
                    if result:
                        st.success("Response received!")
                        st.write(result.get("response", "No response"))

# Tab 5: Simulation
with tab5:
    st.header("Simulation Status")

    status = get_api_data("/simulation/status")

    if status:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Status", "Running" if status.get("is_running") else "Stopped")

        with col2:
            st.metric("Scenario", status.get("scenario", "N/A"))

        with col3:
            st.metric("Orders Generated", status.get("orders_generated", 0))

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Elapsed Time", f"{status.get('elapsed_minutes', 0):.1f} min")

        with col2:
            st.metric("Order Rate", f"{status.get('order_rate', 0)} /min")

        st.markdown("---")

        st.subheader("Recent Events")

        events = status.get("recent_events", [])
        if events:
            events_df = pd.DataFrame(events)
            st.dataframe(events_df, use_container_width=True, hide_index=True)
        else:
            st.info("No events yet")
    else:
        st.warning("Could not fetch simulation status. Is the API running?")

# Footer
st.markdown("---")
st.caption("NPC E-commerce Sandbox v0.1.0 | Multi-Agent Autonomous E-commerce Platform")
