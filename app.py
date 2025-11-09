import streamlit as st
import json
import os
import re
from datetime import datetime
from pathlib import Path
import pandas as pd
from etsy_tracker import EtsyShopTracker

# Page configuration
st.set_page_config(
    page_title="Etsy Sales Tracker",
    page_icon="🛍️",
    layout="wide"
)

# Initialize session state
if 'refresh' not in st.session_state:
    st.session_state.refresh = 0


def load_stores_config():
    """Load stores configuration from JSON file."""
    try:
        with open('stores.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'stores': []}


def save_stores_config(config):
    """Save stores configuration to JSON file."""
    with open('stores.json', 'w') as f:
        json.dump(config, f, indent=2)


def extract_shop_name(url):
    """Extract shop name from Etsy URL."""
    # Match patterns like https://www.etsy.com/shop/ShopName
    match = re.search(r'etsy\.com/shop/([^/?]+)', url)
    if match:
        return match.group(1)
    return None


def get_latest_shop_data(shop_name):
    """Get the most recent data for a shop."""
    data_dir = Path('data')

    if not data_dir.exists():
        return None

    # Check for today's file first
    today_file = data_dir / f"{shop_name}_{datetime.now().strftime('%Y%m%d')}.json"

    if today_file.exists():
        with open(today_file, 'r') as f:
            return json.load(f)

    # Otherwise, look for the most recent file
    pattern = f"{shop_name}_*.json"
    files = sorted(data_dir.glob(pattern), reverse=True)

    for file in files:
        if file.stem.endswith('_history'):
            continue
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            continue

    return None


def get_all_stores_data():
    """Get latest data for all stores."""
    config = load_stores_config()
    stores_data = []

    for store in config['stores']:
        shop_name = store['shop_name']
        data = get_latest_shop_data(shop_name)

        stores_data.append({
            'name': store['name'],
            'shop_name': shop_name,
            'url': store['url'],
            'enabled': store.get('enabled', True),
            'data': data
        })

    return stores_data


# App title
st.title("🛍️ Etsy Sales Tracker")
st.markdown("Track and analyze Etsy store sales and products")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📝 Manage Stores", "📊 Sales Overview", "🏆 Top Products"])

# ============================================================================
# TAB 1: Add/Manage Etsy Stores
# ============================================================================
with tab1:
    st.header("Manage Etsy Stores")

    # Add new store section
    st.subheader("Add New Store")

    col1, col2 = st.columns([3, 1])

    with col1:
        store_url = st.text_input(
            "Etsy Store URL",
            placeholder="https://www.etsy.com/shop/StoreName",
            help="Enter the full URL of the Etsy store you want to track"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        add_button = st.button("➕ Add Store", use_container_width=True)

    if add_button and store_url:
        shop_name = extract_shop_name(store_url)

        if shop_name:
            config = load_stores_config()

            # Check if store already exists
            existing = [s for s in config['stores'] if s['shop_name'] == shop_name]

            if existing:
                st.warning(f"Store '{shop_name}' is already being tracked!")
            else:
                # Add new store
                new_store = {
                    'name': shop_name,
                    'shop_name': shop_name,
                    'url': store_url,
                    'enabled': True
                }

                config['stores'].append(new_store)
                save_stores_config(config)

                st.success(f"✅ Successfully added '{shop_name}' to tracking!")
                st.session_state.refresh += 1
                st.rerun()
        else:
            st.error("Invalid Etsy store URL. Please use format: https://www.etsy.com/shop/StoreName")

    # Display current stores
    st.subheader("Current Stores")

    config = load_stores_config()

    if not config['stores']:
        st.info("No stores are currently being tracked. Add one above to get started!")
    else:
        for i, store in enumerate(config['stores']):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

            with col1:
                st.write(f"**{store['name']}**")

            with col2:
                st.write(f"[{store['shop_name']}]({store['url']})")

            with col3:
                # Toggle enabled/disabled
                enabled = st.checkbox(
                    "Enabled",
                    value=store.get('enabled', True),
                    key=f"enable_{i}",
                    label_visibility="collapsed"
                )

                if enabled != store.get('enabled', True):
                    config['stores'][i]['enabled'] = enabled
                    save_stores_config(config)
                    st.rerun()

            with col4:
                if st.button("🗑️", key=f"delete_{i}", help="Delete store"):
                    config['stores'].pop(i)
                    save_stores_config(config)
                    st.success(f"Deleted {store['name']}")
                    st.rerun()

        st.divider()

        # Bulk actions
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Refresh Data Now", use_container_width=True):
                with st.spinner("Tracking stores... This may take a few minutes."):
                    tracker = EtsyShopTracker()
                    tracker.track_all_stores(track_products=True)
                    st.success("✅ Data refresh complete!")
                    st.rerun()

# ============================================================================
# TAB 2: Sales Overview
# ============================================================================
with tab2:
    st.header("Sales Overview")

    stores_data = get_all_stores_data()

    if not stores_data:
        st.info("No stores configured. Add stores in the 'Manage Stores' tab.")
    else:
        # Prepare data for table
        table_data = []

        for store in stores_data:
            data = store['data']

            if data:
                timestamp = datetime.fromisoformat(data['timestamp'])

                table_data.append({
                    'Store Name': store['name'],
                    'Shop Name': store['shop_name'],
                    'Total Sales': data.get('total_sales') or 'N/A',
                    'Products Tracked': len(data.get('products', [])),
                    'Last Updated': timestamp.strftime('%Y-%m-%d %H:%M'),
                    'Status': '✅ Active' if store['enabled'] else '⏸️ Paused',
                    'URL': store['url']
                })
            else:
                table_data.append({
                    'Store Name': store['name'],
                    'Shop Name': store['shop_name'],
                    'Total Sales': 'No data',
                    'Products Tracked': 0,
                    'Last Updated': 'Never',
                    'Status': '✅ Active' if store['enabled'] else '⏸️ Paused',
                    'URL': store['url']
                })

        # Create DataFrame
        df = pd.DataFrame(table_data)

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Stores", len(stores_data))

        with col2:
            active_stores = sum(1 for s in stores_data if s['enabled'])
            st.metric("Active Stores", active_stores)

        with col3:
            total_sales = sum(
                s['data'].get('total_sales', 0) or 0
                for s in stores_data
                if s['data'] and s['data'].get('total_sales')
            )
            st.metric("Total Sales", f"{total_sales:,}" if total_sales > 0 else "N/A")

        with col4:
            total_products = sum(
                len(s['data'].get('products', []))
                for s in stores_data
                if s['data']
            )
            st.metric("Products Tracked", total_products)

        st.divider()

        # Display table
        st.subheader("Store Details")

        # Make the table interactive
        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("Store URL"),
                "Total Sales": st.column_config.NumberColumn(
                    "Total Sales",
                    format="%d"
                )
            },
            hide_index=True,
            use_container_width=True
        )

        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"etsy_sales_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ============================================================================
# TAB 3: Top Products by Store
# ============================================================================
with tab3:
    st.header("Top Products by Store")

    stores_data = get_all_stores_data()

    if not stores_data:
        st.info("No stores configured. Add stores in the 'Manage Stores' tab.")
    else:
        for store in stores_data:
            data = store['data']

            if not data or not data.get('products'):
                st.warning(f"**{store['name']}**: No product data available")
                st.divider()
                continue

            # Get top product
            products = data['products']
            top_product = max(products, key=lambda p: p.get('sales', 0) or 0)

            # Display store section
            st.subheader(f"🏪 {store['name']}")

            col1, col2 = st.columns([2, 1])

            with col1:
                # Top product info
                st.markdown("**Top Product:**")

                product_title = top_product.get('title', 'Unknown Product')
                product_sales = top_product.get('sales', 0) or 0
                product_price = top_product.get('price', 'N/A')
                product_url = top_product.get('url', '')

                st.markdown(f"### {product_title}")

                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Sales", f"{product_sales:,}")
                with metric_col2:
                    st.metric("Price", product_price)

                if product_url:
                    st.markdown(f"[View on Etsy →]({product_url})")

            with col2:
                # Store summary
                st.markdown("**Store Summary:**")
                total_sales = data.get('total_sales', 'N/A')
                if isinstance(total_sales, int):
                    st.metric("Total Store Sales", f"{total_sales:,}")
                else:
                    st.metric("Total Store Sales", total_sales)

                st.metric("Products Listed", len(products))

                if products:
                    avg_sales = sum(p.get('sales', 0) or 0 for p in products) / len(products)
                    st.metric("Avg Product Sales", f"{avg_sales:.0f}")

            # Show top 5 products
            with st.expander(f"View Top 5 Products for {store['name']}"):
                sorted_products = sorted(
                    products,
                    key=lambda p: p.get('sales', 0) or 0,
                    reverse=True
                )[:5]

                for i, product in enumerate(sorted_products, 1):
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        title = product.get('title', 'Unknown')
                        if len(title) > 60:
                            title = title[:57] + "..."
                        st.write(f"**{i}.** {title}")

                    with col2:
                        sales = product.get('sales', 0) or 0
                        st.write(f"{sales:,} sales")

                    with col3:
                        price = product.get('price', 'N/A')
                        st.write(price)

            st.divider()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    📊 Etsy Sales Tracker | Data is updated daily via GitHub Actions
    </div>
    """,
    unsafe_allow_html=True
)
