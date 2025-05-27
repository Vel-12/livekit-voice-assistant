import streamlit as st
import pandas as pd
from db_driver import DatabaseDriver
import time
import logging
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Moving Requests Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_all_moving_requests():
    """Retrieve all moving requests from the database."""
    try:
        logger.info("Attempting to connect to database...")
        db = DatabaseDriver()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM moving_requests ORDER BY request_id DESC")
            rows = cursor.fetchall()
            
            logger.info(f"Retrieved {len(rows)} rows from database")
            
            if not rows:
                logger.info("No rows found in database")
                return pd.DataFrame()
            
            # Convert rows to DataFrame
            df = pd.DataFrame(rows)
            
            # Rename columns for better display
            column_mapping = {
                'request_id': 'Request ID',
                'customer_name': 'Customer Name',
                'email': 'Email',
                'phone_number': 'Phone Number',
                'phone_type': 'Phone Type',
                'from_address': 'From Address',
                'building_type': 'Building Type',
                'bedrooms': 'Bedrooms',
                'to_address': 'To Address',
                'move_date': 'Move Date',
                'flexible_date': 'Flexible Date',
                'car_transport': 'Car Transport',
                'car_year': 'Car Year',
                'car_make': 'Car Make',
                'car_model': 'Car Model'
            }
            
            # Only rename columns that exist
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=existing_columns)
            
            # Convert boolean values for display
            if 'Flexible Date' in df.columns:
                df['Flexible Date'] = df['Flexible Date'].map({True: 'Yes', False: 'No', 1: 'Yes', 0: 'No'})
            if 'Car Transport' in df.columns:
                df['Car Transport'] = df['Car Transport'].map({True: 'Yes', False: 'No', 1: 'Yes', 0: 'No'})
            
            # Fill NaN values for car details
            car_columns = ['Car Year', 'Car Make', 'Car Model']
            for col in car_columns:
                if col in df.columns:
                    df[col] = df[col].fillna('-')
            
            logger.info(f"Successfully created DataFrame with {len(df)} rows and columns: {list(df.columns)}")
            return df
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}")
        st.error(f"Error retrieving data from database: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_database_info():
    """Get database table and column information."""
    try:
        db = DatabaseDriver()
        tables = db.get_table_info()
        table_info = {}
        for table in tables:
            columns = db.get_column_info(table)
            table_info[table] = columns
        return table_info
    except Exception as e:
        logger.error(f"Error getting database info: {str(e)}")
        return {}

def create_charts(df):
    """Create visualization charts."""
    if df.empty:
        return None, None, None
    
    charts = {}
    
    # Building type distribution
    if 'Building Type' in df.columns:
        building_counts = df['Building Type'].value_counts()
        fig_building = px.pie(
            values=building_counts.values,
            names=building_counts.index,
            title="Distribution by Building Type",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        charts['building_type'] = fig_building
    
    # Car transport distribution
    if 'Car Transport' in df.columns:
        car_counts = df['Car Transport'].value_counts()
        fig_car = px.bar(
            x=car_counts.index,
            y=car_counts.values,
            title="Car Transport Requests",
            color=car_counts.index,
            color_discrete_sequence=['#ff7f7f', '#7fbf7f']
        )
        fig_car.update_layout(showlegend=False)
        charts['car_transport'] = fig_car
    
    # Bedrooms distribution
    if 'Bedrooms' in df.columns:
        bedroom_counts = df['Bedrooms'].value_counts().sort_index()
        fig_bedrooms = px.bar(
            x=bedroom_counts.index,
            y=bedroom_counts.values,
            title="Distribution by Number of Bedrooms",
            color_discrete_sequence=['#87ceeb']
        )
        fig_bedrooms.update_layout(showlegend=False)
        charts['bedrooms'] = fig_bedrooms
    
    return charts

def display_metrics(df):
    """Display key metrics."""
    if df.empty:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Requests", len(df))
    
    with col2:
        if 'Car Transport' in df.columns:
            car_transport_count = len(df[df['Car Transport'] == 'Yes'])
            st.metric("🚗 With Car Transport", car_transport_count)
        else:
            st.metric("🚗 With Car Transport", "N/A")
    
    with col3:
        if 'Flexible Date' in df.columns:
            flexible_count = len(df[df['Flexible Date'] == 'Yes'])
            st.metric("📅 Flexible Dates", flexible_count)
        else:
            st.metric("📅 Flexible Dates", "N/A")
    
    with col4:
        if 'Building Type' in df.columns:
            house_count = len(df[df['Building Type'].str.lower() == 'house'])
            st.metric("🏠 House Moves", house_count)
        else:
            st.metric("🏠 House Moves", "N/A")

def main():
    """Main Streamlit application."""
    st.title("🏠 Moving Requests Dashboard")
    st.markdown("Real-time data from PostgreSQL database")
    
    # Sidebar for controls and info
    with st.sidebar:
        st.header("🔧 Controls")
        
        # Refresh controls
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        
        # Database info
        st.header("📊 Database Info")
        if st.button("Show Database Schema", use_container_width=True):
            st.session_state.show_schema = True
        
        # Connection test
        if st.button("Test Connection", use_container_width=True):
            with st.spinner("Testing connection..."):
                db = DatabaseDriver()
                success, message = db.test_connection()
                if success:
                    st.success("✅ " + message)
                else:
                    st.error("❌ " + message)
    
    # Auto-refresh functionality
    if auto_refresh:
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        # Check if 30 seconds have passed
        if time.time() - st.session_state.last_refresh > 30:
            st.session_state.last_refresh = time.time()
            st.cache_data.clear()
            st.rerun()
        
        # Show countdown
        remaining = 30 - int(time.time() - st.session_state.last_refresh)
        st.info(f"⏱️ Next refresh in: {remaining} seconds")
    
    # Show database schema if requested
    if st.session_state.get('show_schema', False):
        st.subheader("🗄️ Database Schema")
        with st.spinner("Loading database schema..."):
            db_info = get_database_info()
            if db_info:
                for table_name, columns in db_info.items():
                    with st.expander(f"Table: {table_name}"):
                        col_df = pd.DataFrame(columns)
                        st.dataframe(col_df, use_container_width=True)
            else:
                st.warning("Could not retrieve database schema information")
        
        if st.button("Hide Schema"):
            st.session_state.show_schema = False
            st.rerun()
    
    # Get and display data
    with st.spinner("Loading data from database..."):
        df = get_all_moving_requests()
    
    if df.empty:
        st.warning("📋 No moving requests found in the database.")
        st.markdown("---")
        st.markdown("### 🔌 Database Connection Status")
        try:
            db = DatabaseDriver()
            success, message = db.test_connection()
            if success:
                st.success("✅ Database connection successful")
                # Show available tables
                tables = db.get_table_info()
                if tables:
                    st.info(f"📊 Available tables: {', '.join(tables)}")
                else:
                    st.warning("No tables found in database")
            else:
                st.error(f"❌ Database connection failed: {message}")
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
    else:
        # Display metrics
        display_metrics(df)
        st.markdown("---")
        
        # Create and display charts
        st.subheader("📈 Data Visualizations")
        charts = create_charts(df)
        
        if charts:
            chart_cols = st.columns(len(charts))
            for i, (chart_name, chart) in enumerate(charts.items()):
                with chart_cols[i % len(chart_cols)]:
                    st.plotly_chart(chart, use_container_width=True)
        
        st.markdown("---")
        
        # Add filters
        st.subheader("🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔎 Search by name or request ID")
        
        with col2:
            if 'Building Type' in df.columns:
                building_types = ["All"] + sorted(list(df['Building Type'].dropna().unique()))
                building_type = st.selectbox("🏢 Filter by building type", building_types)
            else:
                building_type = "All"
        
        with col3:
            if 'Car Transport' in df.columns:
                car_transport = st.selectbox("🚗 Filter by car transport", ["All", "Yes", "No"])
            else:
                car_transport = "All"
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = pd.Series(False, index=filtered_df.index)
            if 'Customer Name' in filtered_df.columns:
                mask |= filtered_df['Customer Name'].str.contains(search_term, case=False, na=False)
            if 'Request ID' in filtered_df.columns:
                mask |= filtered_df['Request ID'].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = filtered_df[mask]
        
        if building_type != "All" and 'Building Type' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Building Type'] == building_type]
        
        if car_transport != "All" and 'Car Transport' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Car Transport'] == car_transport]
        
        # Display filtered results count
        if len(filtered_df) != len(df):
            st.info(f"📊 Showing {len(filtered_df)} of {len(df)} requests")
        
        # Display the table
        st.subheader("📋 Moving Requests Data")
        
        if not filtered_df.empty:
            # Configure column display
            column_config = {}
            for col in filtered_df.columns:
                if 'ID' in col:
                    column_config[col] = st.column_config.TextColumn(col, width="small")
                elif col in ['Customer Name', 'Email']:
                    column_config[col] = st.column_config.TextColumn(col, width="medium")
                elif 'Address' in col:
                    column_config[col] = st.column_config.TextColumn(col, width="large")
                elif col in ['Phone Number', 'Move Date', 'Bedrooms']:
                    column_config[col] = st.column_config.TextColumn(col, width="small")
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )
            
            # Add download functionality
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"moving_requests_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                st.info("💡 Click on any column header to sort the data. Use the sidebar to refresh data or test the connection.")
        else:
            st.warning("⚠️ No requests match the current filters.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 14px;'>"
        f"Moving Requests Dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "Powered by PostgreSQL & Streamlit"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()