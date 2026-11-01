import streamlit as st

# Set up your web page configuration
st.set_page_config(
    page_title="NOVA",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application Title
st.title("⚡ NOVA Dashboard")
st.write("Welcome to your web-hosted NOVA application!")

# Sidebar navigation (acting as your web menu)
st.sidebar.title("NOVA Navigation")
choice = st.sidebar.radio("Go to", ["Dashboard", "System Monitor", "Notes & Tasks", "Settings"])

if choice == "Dashboard":
    st.header("Home Dashboard")
    st.info("Your app is successfully running on the web!")

elif choice == "System Monitor":
    import psutil
    st.header("Live System Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="CPU Usage", value=f"{psutil.cpu_percent(interval=1)}%")
    with col2:
        st.metric(label="Memory Usage", value=f"{psutil.virtual_memory().percent}%")

elif choice == "Notes & Tasks":
    st.header("Notes & Tasks Module")
    st.write("You can import and call your core logic here (e.g., from core.notes_database import ...)")

elif choice == "Settings":
    st.header("Settings")
    st.text("App configurations and preferences.")