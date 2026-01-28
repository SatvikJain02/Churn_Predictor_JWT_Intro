import streamlit as st
import requests

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"  # Ensure your FastAPI is running here

# --- Session State Management ---
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# --- Helper Functions ---
def login(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/login", 
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state['token'] = data['access_token']
            st.session_state['username'] = username
            st.success(f"Welcome back, {username}! 🔓")
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again. 🚫")
    except Exception as e:
        st.error(f"Connection error: {e}")

def register(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/register", 
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            st.success("Registration successful! You can now login. ✅")
        else:
            st.error(f"Error: {response.json().get('detail', 'Registration failed')}")
    except Exception as e:
        st.error(f"Connection error: {e}")

def predict_churn(data):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    # Nesting data under 'customer' key as required by AuthenticatePredictionRequest
    payload = {"customer": data}
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/auth", 
            json=payload, 
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Session expired. Please login again.")
            st.session_state['token'] = None
            st.rerun()
        else:
            st.error(f"Prediction failed: {response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")

# --- UI Layout ---
st.set_page_config(page_title="Churn Predictor", page_icon="🔮")

st.title("🔮 Customer Churn Prediction")

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["Login", "Register", "Prediction"])

# --- LOGIN PAGE ---
if menu == "Login":
    st.subheader("Login to your account")
    if st.session_state['token']:
        st.info(f"You are already logged in as **{st.session_state['username']}**.")
        if st.button("Logout"):
            st.session_state['token'] = None
            st.session_state['username'] = None
            st.rerun()
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)

# --- REGISTER PAGE ---
elif menu == "Register":
    st.subheader("Create a new account")
    new_user = st.text_input("Choose a Username")
    new_pass = st.text_input("Choose a Password", type="password")
    if st.button("Register"):
        register(new_user, new_pass)

# --- PREDICTION PAGE ---
elif menu == "Prediction":
    if not st.session_state['token']:
        st.warning("🔒 Please **Login** to access the prediction tool.")
    else:
        st.subheader("Enter Customer Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female"])
            age = st.number_input("Age", min_value=18, max_value=100, value=45)
            tenure = st.number_input("Tenure (Months)", min_value=0, max_value=100, value=12)
            services = st.number_input("Services Subscribed", min_value=0, max_value=10, value=3)
            contract = st.selectbox("Contract Type", ["Month-to-month", "One year", "Two year"])

        with col2:
            monthly_charges = st.number_input("Monthly Charges ($)", min_value=0.1, value=70.5)
            total_charges = st.number_input("Total Charges ($)", min_value=0.0, value=500.5)
            tech_support = st.selectbox("Tech Support", ["Yes", "No"])
            online_security = st.selectbox("Online Security", ["Yes", "No"])
            internet_service = st.selectbox("Internet Service", ["Fiber optic", "DSL", "No"])

        if st.button("Predict Churn 🚀"):
            # Construct dictionary matching CustomerData schema exactly
            customer_data = {
                "Gender": gender,
                "Age": age,
                "Tenure": tenure,
                "Services_Subscribed": services,
                "Contract_Type": contract,
                "MonthlyCharges": monthly_charges,
                "TotalCharges": total_charges,
                "TechSupport": tech_support,
                "OnlineSecurity": online_security,
                "InternetService": internet_service
            }
            
            result = predict_churn(customer_data)
            
            if result:
                st.divider()
                st.subheader("Prediction Result")
                if result['churn_prediction'] == 1:
                    st.error(f"⚠️ **Churn Detected** (Probability: {result['churn_probability']:.2f})")
                else:
                    st.success(f"✅ **No Churn** (Probability: {result['churn_probability']:.2f})")