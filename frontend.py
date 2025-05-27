import streamlit as st
import pandas as pd
from db_driver import DatabaseDriver
import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Moving Requests Dashboard",
    page_icon="🏠",
    layout="wide"
)

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
            df = pd.DataFrame(rows, columns=[
                'Request ID', 'Customer Name', 'Email', 'Phone Number', 'Phone Type',
                'From Address', 'Building Type', 'Bedrooms', 'To Address',
                'Move Date', 'Flexible Date', 'Car Transport', 'Car Year',
                'Car Make', 'Car Model'
            ])
            
            # Convert boolean values for display
            df['Flexible Date'] = df['Flexible Date'].map({True: 'Yes', False: 'No', 1: 'Yes', 0: 'No'})
            df['Car Transport'] = df['Car Transport'].map({True: 'Yes', False: 'No', 1: 'Yes', 0: 'No'})
            
            # Fill NaN values for car details
            df['Car Year'] = df['Car Year'].fillna('-')
            df['Car Make'] = df['Car Make'].fillna('-')
            df['Car Model'] = df['Car Model'].fillna('-')
            
            logger.info(f"Successfully created DataFrame with {len(df)} rows")
            return df
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}")
        st.error(f"Error retrieving data from database: {str(e)}")
        return pd.DataFrame()

def main():
    """Main Streamlit application."""
    st.title("🏠 Moving Requests Dashboard")
    
    # Add refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
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
        st.info(f"Next refresh in: {remaining} seconds")
    
    # Get and display data
    df = get_all_moving_requests()
    
    if df.empty:
        st.info("📋 No moving requests found in the database.")
        st.markdown("---")
        st.markdown("### Database Connection Status")
        try:
            db = DatabaseDriver()
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                st.success("✅ Database connection successful")
        except Exception as e:
            st.error(f"❌ Database connection failed: {str(e)}")
    else:
        # Display summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", len(df))
        with col2:
            car_transport_count = len(df[df['Car Transport'] == 'Yes'])
            st.metric("With Car Transport", car_transport_count)
        with col3:
            flexible_count = len(df[df['Flexible Date'] == 'Yes'])
            st.metric("Flexible Dates", flexible_count)
        with col4:
            house_count = len(df[df['Building Type'] == 'house'])
            st.metric("House Moves", house_count)
        
        st.markdown("---")
        
        # Add filters
        st.subheader("🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search by name or request ID")
        with col2:
            building_type = st.selectbox(
                "Filter by building type",
                ["All"] + sorted(list(df['Building Type'].unique()))
            )
        with col3:
            car_transport = st.selectbox(
                "Filter by car transport",
                ["All", "Yes", "No"]
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df['Customer Name'].str.contains(search_term, case=False, na=False) |
                filtered_df['Request ID'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if building_type != "All":
            filtered_df = filtered_df[filtered_df['Building Type'] == building_type]
        
        if car_transport != "All":
            filtered_df = filtered_df[filtered_df['Car Transport'] == car_transport]
        
        # Display filtered results count
        if len(filtered_df) != len(df):
            st.info(f"Showing {len(filtered_df)} of {len(df)} requests")
        
        # Display the table
        st.subheader("📊 Moving Requests")
        
        if not filtered_df.empty:
            # Make the dataframe more readable
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Request ID": st.column_config.TextColumn("Request ID", width="small"),
                    "Customer Name": st.column_config.TextColumn("Customer Name", width="medium"),
                    "Email": st.column_config.TextColumn("Email", width="medium"),
                    "Phone Number": st.column_config.TextColumn("Phone", width="small"),
                    "From Address": st.column_config.TextColumn("From Address", width="large"),
                    "To Address": st.column_config.TextColumn("To Address", width="large"),
                    "Move Date": st.column_config.TextColumn("Move Date", width="small"),
                    "Bedrooms": st.column_config.NumberColumn("Bedrooms", width="small"),
                }
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
                    mime="text/csv"
                )
            with col2:
                st.info("💡 Click on any column header to sort the data")
        else:
            st.warning("No requests match the current filters.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Moving Requests Dashboard | Real-time data from PostgreSQL"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()