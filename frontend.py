import streamlit as st
import pandas as pd
from db_driver import DatabaseDriver
import threading
import webbrowser
import time
import os
import logging
import subprocess
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_moving_requests():
    """Retrieve all moving requests from the database."""
    try:
        logger.info("Attempting to connect to database...")
        db = DatabaseDriver()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM moving_requests")
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
            
            # Convert boolean values
            df['Flexible Date'] = df['Flexible Date'].map({1: 'Yes', 0: 'No'})
            df['Car Transport'] = df['Car Transport'].map({1: 'Yes', 0: 'No'})
            
            logger.info(f"Successfully created DataFrame with {len(df)} rows")
            return df
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}")
        st.error(f"Error retrieving data from database: {str(e)}")
        return pd.DataFrame()

def run_streamlit():
    """Run the Streamlit app."""
    st.set_page_config(
        page_title="Moving Requests Dashboard",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("Moving Requests Dashboard")
    
    # Add auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Refresh data every 30 seconds
    if time.time() - st.session_state.last_refresh > 30:
        st.session_state.last_refresh = time.time()
        st.experimental_rerun()
    
    # Get and display data
    df = get_all_moving_requests()
    
    if df.empty:
        st.info("No moving requests found in the database.")
    else:
        # Display total count
        st.subheader(f"Total Moving Requests: {len(df)}")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search by name or request ID")
        with col2:
            building_type = st.selectbox(
                "Filter by building type",
                ["All"] + list(df['Building Type'].unique())
            )
        
        # Apply filters
        if search_term:
            df = df[
                df['Customer Name'].str.contains(search_term, case=False) |
                df['Request ID'].str.contains(search_term, case=False)
            ]
        
        if building_type != "All":
            df = df[df['Building Type'] == building_type]
        
        # Display the table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Add download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="moving_requests.csv",
            mime="text/csv"
        )

def open_browser():
    """Open the browser to the Streamlit app."""
    time.sleep(2)  # Wait for Streamlit to start
    webbrowser.open('http://localhost:8501')

def start_frontend():
    """Start the Streamlit frontend in a separate thread."""
    try:
        logger.info("Starting frontend...")
        # Get the absolute path of the frontend.py file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(current_dir, 'frontend.py')
        logger.info(f"Running Streamlit with path: {frontend_path}")
        
        # Start browser in a separate thread
        threading.Thread(target=open_browser).start()
        
        # Run Streamlit using subprocess
        python_executable = sys.executable
        streamlit_cmd = [
            python_executable,
            "-m",
            "streamlit",
            "run",
            frontend_path,
            "--server.port=8501",
            "--server.address=localhost"
        ]
        
        logger.info(f"Running command: {' '.join(streamlit_cmd)}")
        subprocess.run(streamlit_cmd, check=True)
        
    except Exception as e:
        logger.error(f"Error starting frontend: {str(e)}")
        raise

if __name__ == "__main__":
    run_streamlit() 