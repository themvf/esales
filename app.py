"""
Etsy Sales Tracker - Streamlit Dashboard
Interactive analytics dashboard for Etsy sales tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

from database import Database
from scraper import EtsyScraper
from scheduler import ScraperScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title="Etsy Sales Tracker",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
# Note: Don't cache Database with SQLite - connections are not thread-safe
def get_database():
    """Get database instance - creates a new connection each time"""
    return Database()

# Get a fresh database connection for this run
db = get_database()

# Sidebar navigation
st.sidebar.title("📊 Etsy Sales Tracker")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Shop Tracker", "Product Analysis", "Keyword Intelligence", "Settings"]
)

# ============ HELPER FUNCTIONS ============

def format_number(num):
    """Format large numbers with K, M suffix"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def get_listings_with_metrics():
    """Get all listings with calculated metrics"""
    listings = db.get_all_listings()

    data = []
    for listing in listings:
        # Get latest snapshot
        snapshot = db.get_latest_snapshot(listing['listing_id'])

        # Get 7-day sales
        seven_day_sales = db.get_seven_day_sales(listing['listing_id'])

        data.append({
            'Listing ID': listing['listing_id'],
            'Shop': listing['shop_name'],
            'Title': listing['title'],
            'Price': listing['price'],
            'Currency': listing['currency'],
            'Tags': ', '.join(listing['tags']) if listing['tags'] else '',
            'Total Sales': snapshot['sales_count'] if snapshot else 0,
            '7-Day Sales': seven_day_sales if seven_day_sales is not None else 0,
            'Views': snapshot['views'] if snapshot else 0,
            'Favorites': snapshot['favorites'] if snapshot else 0,
            'Last Updated': listing['last_updated']
        })

    return pd.DataFrame(data)

# ============ DASHBOARD PAGE ============

if page == "Dashboard":
    st.title("📊 Dashboard")
    st.write("Overview of your Etsy sales tracking")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Get statistics
    all_shops = db.get_all_shops()
    all_listings = db.get_all_listings()

    total_shops = len(all_shops)
    total_listings = len(all_listings)

    # Calculate total sales
    total_sales = sum(shop['total_sales'] for shop in all_shops if shop['total_sales'])

    # Get top performing listings
    top_listings = db.get_top_performing_listings(limit=10)

    with col1:
        st.metric("Tracked Shops", total_shops)

    with col2:
        st.metric("Total Listings", total_listings)

    with col3:
        st.metric("Total Sales", format_number(total_sales))

    with col4:
        if top_listings:
            avg_7day = sum(l['seven_day_sales'] for l in top_listings) / len(top_listings)
            st.metric("Avg 7-Day Sales (Top 10)", f"{avg_7day:.1f}")
        else:
            st.metric("Avg 7-Day Sales (Top 10)", "N/A")

    # Charts row
    st.subheader("📈 Top Performing Listings")

    if top_listings:
        # Convert to DataFrame
        top_df = pd.DataFrame(top_listings)

        # Create bar chart
        fig = px.bar(
            top_df,
            x='title',
            y='seven_day_sales',
            color='shop_name',
            title='Top 10 Listings by 7-Day Sales',
            labels={'title': 'Product Title', 'seven_day_sales': '7-Day Sales', 'shop_name': 'Shop'}
        )
        fig.update_layout(xaxis_tickangle=-45, height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Display table
        st.dataframe(
            top_df[['title', 'shop_name', 'current_sales', 'seven_day_sales', 'price']],
            use_container_width=True
        )
    else:
        st.info("No data available. Start tracking shops to see analytics!")

    # Shops overview
    st.subheader("🏪 Tracked Shops")

    if all_shops:
        shops_df = pd.DataFrame(all_shops)
        st.dataframe(
            shops_df[['shop_name', 'total_sales', 'num_listings', 'location', 'last_updated']],
            use_container_width=True
        )
    else:
        st.info("No shops tracked yet. Add shops in the Shop Tracker page.")

# ============ SHOP TRACKER PAGE ============

elif page == "Shop Tracker":
    st.title("🏪 Shop Tracker")
    st.write("Search and monitor Etsy shops")

    # Add shop section
    st.subheader("➕ Add New Shop")

    col1, col2 = st.columns([3, 1])

    with col1:
        new_shop = st.text_input("Enter shop name to track", placeholder="ExampleShopName")

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Add Shop", type="primary"):
            if new_shop:
                with st.spinner(f"Adding and scraping shop: {new_shop}..."):
                    try:
                        scheduler = ScraperScheduler()
                        scheduler.add_shop_to_tracking(new_shop)
                        st.success(f"Successfully added {new_shop}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding shop: {e}")
            else:
                st.warning("Please enter a shop name")

    st.divider()

    # List tracked shops
    st.subheader("📋 Tracked Shops")

    all_shops = db.get_all_shops()

    if all_shops:
        for shop in all_shops:
            with st.expander(f"🏪 {shop['shop_name']} - {format_number(shop['total_sales'] or 0)} sales"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Sales", format_number(shop['total_sales'] or 0))

                with col2:
                    st.metric("Listings", shop['num_listings'] or 0)

                with col3:
                    st.metric("Location", shop['location'] or "Unknown")

                st.write(f"**First Tracked:** {shop['first_seen']}")
                st.write(f"**Last Updated:** {shop['last_updated']}")

                if shop['shop_url']:
                    st.write(f"[View Shop on Etsy]({shop['shop_url']})")

                # Get shop stats
                stats = db.get_shop_stats(shop['shop_name'])
                if stats:
                    st.write(f"**Database Stats:** {stats['num_listings']} listings, {format_number(stats['total_sales'])} total sales")

                # Scrape now button
                if st.button(f"Scrape Now", key=f"scrape_{shop['shop_name']}"):
                    with st.spinner(f"Scraping {shop['shop_name']}..."):
                        try:
                            scheduler = ScraperScheduler()
                            scheduler.scrape_shop_job(shop['shop_name'])
                            st.success(f"Successfully scraped {shop['shop_name']}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error scraping shop: {e}")

                # Delete button
                if st.button(f"Delete Shop", key=f"delete_{shop['shop_name']}", type="secondary"):
                    if st.session_state.get(f'confirm_delete_{shop["shop_name"]}', False):
                        db.delete_shop(shop['shop_name'])
                        st.success(f"Deleted {shop['shop_name']}")
                        st.rerun()
                    else:
                        st.session_state[f'confirm_delete_{shop["shop_name"]}'] = True
                        st.warning("Click again to confirm deletion")
    else:
        st.info("No shops tracked yet. Add a shop above to get started!")

# ============ PRODUCT ANALYSIS PAGE ============

elif page == "Product Analysis":
    st.title("📦 Product Analysis")
    st.write("Analyze listings and sales performance")

    # Get listings with metrics
    try:
        df = get_listings_with_metrics()

        if not df.empty:
            # Filters
            st.subheader("🔍 Filters")

            col1, col2, col3 = st.columns(3)

            with col1:
                selected_shops = st.multiselect(
                    "Filter by Shop",
                    options=df['Shop'].unique().tolist(),
                    default=[]
                )

            with col2:
                min_sales = st.number_input("Min 7-Day Sales", min_value=0, value=0)

            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["7-Day Sales", "Total Sales", "Views", "Favorites", "Price"]
                )

            # Apply filters
            filtered_df = df.copy()

            if selected_shops:
                filtered_df = filtered_df[filtered_df['Shop'].isin(selected_shops)]

            filtered_df = filtered_df[filtered_df['7-Day Sales'] >= min_sales]

            # Sort
            filtered_df = filtered_df.sort_values(by=sort_by, ascending=False)

            # Display metrics
            st.subheader("📊 Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Listings", len(filtered_df))

            with col2:
                total_7day = filtered_df['7-Day Sales'].sum()
                st.metric("Total 7-Day Sales", format_number(int(total_7day)))

            with col3:
                avg_price = filtered_df['Price'].mean()
                st.metric("Avg Price", f"${avg_price:.2f}" if not pd.isna(avg_price) else "N/A")

            with col4:
                total_views = filtered_df['Views'].sum()
                st.metric("Total Views", format_number(int(total_views)))

            # Charts
            st.subheader("📈 Visualizations")

            tab1, tab2, tab3 = st.tabs(["Sales Trends", "Price Analysis", "Performance"])

            with tab1:
                # Top products by 7-day sales
                top_n = st.slider("Show top N products", 5, 50, 20)
                top_products = filtered_df.nlargest(top_n, '7-Day Sales')

                fig = px.bar(
                    top_products,
                    x='Title',
                    y='7-Day Sales',
                    color='Shop',
                    title=f'Top {top_n} Products by 7-Day Sales',
                    hover_data=['Total Sales', 'Price']
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                # Price vs Sales scatter plot
                fig = px.scatter(
                    filtered_df,
                    x='Price',
                    y='7-Day Sales',
                    color='Shop',
                    size='Views',
                    hover_data=['Title'],
                    title='Price vs 7-Day Sales',
                    labels={'Price': 'Price ($)', '7-Day Sales': '7-Day Sales'}
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                # Sales velocity
                filtered_df['Sales Velocity'] = filtered_df.apply(
                    lambda row: row['7-Day Sales'] / row['Total Sales'] * 100 if row['Total Sales'] > 0 else 0,
                    axis=1
                )

                top_velocity = filtered_df.nlargest(20, 'Sales Velocity')

                fig = px.bar(
                    top_velocity,
                    x='Title',
                    y='Sales Velocity',
                    color='Shop',
                    title='Top 20 Products by Sales Velocity (7-day % of total)',
                    labels={'Sales Velocity': 'Sales Velocity (%)'}
                )
                fig.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.subheader("📋 Listings Data")

            # Display dataframe with column configuration
            st.dataframe(
                filtered_df[[
                    'Title', 'Shop', 'Price', 'Total Sales',
                    '7-Day Sales', 'Views', 'Favorites', 'Tags'
                ]],
                use_container_width=True,
                height=400
            )

            # Export button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"etsy_listings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        else:
            st.info("No listings data available. Start tracking shops to see products!")

    except Exception as e:
        st.error(f"Error loading data: {e}")

# ============ KEYWORD INTELLIGENCE PAGE ============

elif page == "Keyword Intelligence":
    st.title("🔍 Keyword Intelligence")
    st.write("Analyze trending tags and keywords")

    # Get trending tags
    trending_tags = db.get_trending_tags(limit=50)

    if trending_tags:
        st.subheader("📈 Most Popular Tags")

        # Convert to DataFrame
        tags_df = pd.DataFrame(trending_tags, columns=['Tag', 'Count'])

        # Create two columns
        col1, col2 = st.columns([2, 1])

        with col1:
            # Bar chart
            fig = px.bar(
                tags_df.head(20),
                x='Tag',
                y='Count',
                title='Top 20 Tags by Usage',
                labels={'Tag': 'Tag', 'Count': 'Number of Listings'}
            )
            fig.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top tags list
            st.write("**Top 20 Tags**")
            for i, (tag, count) in enumerate(trending_tags[:20], 1):
                st.write(f"{i}. **{tag}** ({count} listings)")

        # Word cloud style display (using metrics)
        st.subheader("☁️ Tag Cloud")

        # Display tags in a grid
        cols = st.columns(5)
        for i, (tag, count) in enumerate(trending_tags[:25]):
            with cols[i % 5]:
                st.metric(tag, count)

        # Full tags table
        st.subheader("📋 All Tags")
        st.dataframe(tags_df, use_container_width=True, height=400)

        # Export tags
        csv = tags_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Tags CSV",
            data=csv,
            file_name=f"etsy_tags_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No tag data available. Start tracking shops to see keyword insights!")

    # Tag search and analysis
    st.divider()
    st.subheader("🔎 Search Listings by Tag")

    search_tag = st.text_input("Enter a tag to search for listings")

    if search_tag:
        # Get all listings
        all_listings = db.get_all_listings()

        # Filter by tag
        matching_listings = [
            l for l in all_listings
            if l['tags'] and search_tag.lower() in [t.lower() for t in l['tags']]
        ]

        if matching_listings:
            st.write(f"Found **{len(matching_listings)}** listings with tag '{search_tag}'")

            # Create DataFrame
            data = []
            for listing in matching_listings:
                snapshot = db.get_latest_snapshot(listing['listing_id'])
                data.append({
                    'Title': listing['title'],
                    'Shop': listing['shop_name'],
                    'Price': listing['price'],
                    'Sales': snapshot['sales_count'] if snapshot else 0
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"No listings found with tag '{search_tag}'")

# ============ SETTINGS PAGE ============

elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("Configure scraper and scheduler settings")

    st.subheader("🤖 Scheduler Status")

    try:
        scheduler = ScraperScheduler()
        status = scheduler.get_status()

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Status", "Running" if status['running'] else "Stopped")

        with col2:
            st.metric("Scheduled Jobs", status['num_jobs'])

        if status['jobs']:
            st.write("**Upcoming Jobs:**")
            for job in status['jobs']:
                st.write(f"- {job['id']}: Next run at {job['next_run_time'] or 'Not scheduled'}")

    except Exception as e:
        st.warning(f"Scheduler not running: {e}")

    st.divider()

    st.subheader("🗄️ Database Info")

    col1, col2, col3 = st.columns(3)

    with col1:
        shops_count = len(db.get_all_shops())
        st.metric("Shops", shops_count)

    with col2:
        listings_count = len(db.get_all_listings())
        st.metric("Listings", listings_count)

    with col3:
        # Count snapshots (this would require a new DB method, simplified here)
        st.metric("Database", "Active")

    st.divider()

    st.subheader("📖 About")

    st.markdown("""
    **Etsy Sales Tracker** is a comprehensive analytics platform for tracking Etsy shops and products.

    **Features:**
    - 🏪 Track multiple Etsy shops
    - 📊 Monitor sales trends and performance
    - 🔍 Analyze keywords and tags
    - 📈 Visualize data with interactive charts
    - 🤖 Automated scheduled scraping
    - 💾 Historical data tracking

    **Technology Stack:**
    - Python with BeautifulSoup for web scraping
    - SQLite for data storage
    - Streamlit for the dashboard
    - Plotly for visualizations
    - APScheduler for automation

    **Version:** 1.0.0
    """)

# Footer
st.sidebar.divider()
st.sidebar.info("💡 Tip: Use the scheduler to automate data collection and track trends over time!")
