import streamlit as st
import pandas as pd
import json
import os
from gcp import save_data_to_gcp_bucket

def save_config(config):
    if os.environ["GCP_BUCKET_NAME"]:
        # Save to GCP bucket
        file_path = "config.json"
        save_data_to_gcp_bucket(config, file_path, content_type='application/json')
    else:
        # Save to local file
        if not os.path.exists("data"):
            os.makedirs("data")
        file_path = os.path.join("data", "config.json")
        with open(file_path, "w") as f:
            json.dump(config, f, indent=4)

    return file_path

def save_csv_data(df):
    if os.environ["GCP_BUCKET_NAME"]:
        date_time = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"data_{date_time}.csv"
        save_data_to_gcp_bucket(df.to_csv(index=False), file_path, content_type='text/csv')
    else:
        # Save to local file
        if not os.path.exists("data"):
            os.makedirs("data")
        file_path = os.path.join("data", "data.csv")
        df.to_csv(file_path, index=False)

    return file_path

# --- Page Configuration ---
st.set_page_config(
    page_title="Configure Calculator",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Step 1: Configure Your Calculator")
st.markdown("""
Upload your pricing spreadsheet (in CSV or XLSX format) and assign columns to the different "buckets" to build your calculator.
As you assign a column to a bucket, it will become unavailable in the other buckets.
""")

# --- Directory Setup ---
if not os.path.exists("data"):
    os.makedirs("data")

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Upload your CSV or Excel spreadsheet",
    type=['csv', 'xlsx'],
    help="Upload the spreadsheet containing your pricing data. For Excel files, only the first sheet will be used."
)

if uploaded_file is not None:
    try:
        # --- Read file based on its extension ---
        file_extension = os.path.splitext(uploaded_file.name)[1]
        if file_extension == '.csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension == '.xlsx':
            df = pd.read_excel(uploaded_file, sheet_name=0)
        else:
            st.error("Unsupported file type. Please upload a CSV or XLSX file.")
            st.stop()

        st.success("File uploaded successfully! Here's a preview of your data:")
        st.dataframe(df.head())

        # --- Initialize Session State ---
        if 'all_columns' not in st.session_state or st.session_state.get('file_name') != uploaded_file.name:
            st.session_state.all_columns = df.columns.tolist()
            st.session_state.user_inputs = []
            st.session_state.the_answer = []
            st.session_state.additional_details = []
            st.session_state.admin_info = [] # New bucket
            st.session_state.file_name = uploaded_file.name

        st.divider()
        st.header("Assign Columns to Buckets")
        st.markdown("Select which columns from your spreadsheet should be used for each category.")

        # --- Calculate available options dynamically ---
        all_selected = (st.session_state.user_inputs + 
                        st.session_state.the_answer + 
                        st.session_state.additional_details +
                        st.session_state.admin_info)
        available_options = [col for col in st.session_state.all_columns if col not in all_selected]

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        # --- Bucket Selection Widgets ---
        with col1:
            st.info("These are the options a user will select.")
            options_for_input = sorted(available_options + st.session_state.user_inputs)
            st.session_state.user_inputs = st.multiselect(
                "**User Inputs (Selectors)**",
                options=options_for_input,
                default=st.session_state.user_inputs,
                key="ms_user_inputs",
                help="Select the columns that will be used as filters or inputs in the calculator."
            )

        with col2:
            st.info("This is the main result of the calculation.")
            options_for_answer = sorted(available_options + st.session_state.the_answer)
            st.session_state.the_answer = st.multiselect(
                "**The 'Answer' (e.g., Price)**",
                options=options_for_answer,
                default=st.session_state.the_answer,
                key="ms_the_answer",
                help="Select the column(s) that represent the final calculated value, like price."
            )

        with col3:
            st.info("These are extra details shown with the result.")
            options_for_details = sorted(available_options + st.session_state.additional_details)
            st.session_state.additional_details = st.multiselect(
                "**Additional Details (Informational)**",
                options=options_for_details,
                default=st.session_state.additional_details,
                key="ms_additional_details",
                help="Select columns that provide extra context or information about the result."
            )
        
        with col4:
            st.info("This is for internal use and won't be a filter.")
            options_for_admin = sorted(available_options + st.session_state.admin_info)
            st.session_state.admin_info = st.multiselect(
                "**Admin Information**",
                options=options_for_admin,
                default=st.session_state.admin_info,
                key="ms_admin_info",
                help="Select columns for internal admin reference. They will appear in the results table."
            )

        st.divider()

        # --- Generate and Save Configuration ---
        if st.button("Generate and Save Configuration", type="primary", use_container_width=True):
            if not st.session_state.user_inputs:
                st.error("Please select at least one column for 'User Inputs'.")
            elif not st.session_state.the_answer:
                st.error("Please select at least one column for 'The Answer'.")
            else:
                csv_file_path = save_csv_data(df)

                config = {
                    "csv_path": csv_file_path,
                    "buckets": {
                        "inputs": st.session_state.user_inputs,
                        "answer": st.session_state.the_answer,
                        "details": st.session_state.additional_details,
                        "admin": st.session_state.admin_info # New bucket in config
                    }
                }

                config_path = os.path.join("data", "config.json")
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)

                st.success(f"Configuration saved successfully to `{config_path}`!")
                st.info("You can now navigate to the 'Price Calculator' page to use your new tool.")
                st.balloons()

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.warning("Please ensure you uploaded a valid CSV or XLSX file.")

else:
    st.info("Please upload a CSV or Excel file to begin the configuration process.")
