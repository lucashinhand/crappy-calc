import streamlit as st
import pandas as pd
import json
import os
from gcp import save_data_to_gcp_bucket

GCP_ENABLED = os.environ.get("GCP_BUCKET_NAME", None) is not None

def save_config(config):
    if GCP_ENABLED:
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
    if GCP_ENABLED:
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

st.title("Configure Your Calculator")
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


        # --- Wizard Step State ---
        if 'wizard_step' not in st.session_state:
            st.session_state.wizard_step = 0
            st.session_state.user_inputs = []
            st.session_state.the_answer = []
            st.session_state.additional_details = []
            st.session_state.admin_info = []

            # Initialize default options for the first step
            st.session_state.user_inputs_default = []
            st.session_state.the_answer_default = []
            st.session_state.additional_details_default = []
            st.session_state.admin_info_default = []

            st.session_state.current_default_options = []

        # --- Step Definitions ---
        steps = [
            {
                'label': "User Inputs (Selectors)",
                'key': 'ms_user_inputs',
                'help': "Select the columns that will be used as filters or inputs in the calculator.",
                'state_key': 'user_inputs',
            },
            {
                'label': "The 'Answer' (e.g., Price)",
                'key': 'ms_the_answer',
                'help': "Select the column(s) that represent the final calculated value, like price.",
                'state_key': 'the_answer',
            },
            {
                'label': "Additional Details (Informational)",
                'key': 'ms_additional_details',
                'help': "Select columns that provide extra context or information about the result.",
                'state_key': 'additional_details',
            },
            {
                'label': "Admin Information",
                'key': 'ms_admin_info',
                'help': "Select columns for internal admin reference. They will appear in the results table.",
                'state_key': 'admin_info',
            },
        ]

        step = st.session_state.wizard_step
        options = df.columns.tolist()

        def next_step():
            st.session_state[steps[step]['state_key'] + "_default"] = st.session_state[steps[step]['state_key']].copy()
            st.session_state.wizard_step += 1
            st.rerun()

        def previous_step():
            st.session_state[steps[step]['state_key'] + "_default"] = [] # reset default options for the current step
            st.session_state.wizard_step -= 1
            st.rerun()

        st.divider()
        st.header(f"Step {step + 1} of {len(steps)}: Assign Columns")

        def get_available_options(options, steps, step):
            selected = set()
            for i in range(step):
                selected.update(st.session_state.get(steps[i]['state_key'], []))
            return [col for col in options if col not in selected]

        for i, s in enumerate(steps):
            default_options = st.session_state.get(s['state_key'] + "_default", [])
            if i < step:
                st.multiselect(
                    f"**{s['label']}**",
                    options=options,
                    default=default_options,
                    key=s['key'],
                    help=s['help'],
                    disabled=True,
                )
            elif i == step:
                available_options = get_available_options(options, steps, step)
                st.session_state[s['state_key']] = st.multiselect(
                    f"**{s['label']}**",
                    options=available_options,
                    default=default_options,
                    key=s['key'],
                    help=s['help'],
                )

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if step > 0:
                if st.button("Go Back", use_container_width=True):
                    previous_step()
        with col_nav2:
            if step < len(steps)-1:
                if st.button("Next", use_container_width=True, type="primary"):
                    # Optionally, require at least one selection for first two steps
                    if step == 0 and not st.session_state.user_inputs:
                        st.error("Please select at least one column for 'User Inputs'.")
                    elif step == 1 and not st.session_state.the_answer:
                        st.error("Please select at least one column for 'The Answer'.")
                    else:
                        next_step()
            else:
                # Generate and Save button (full width, only on last step)
                if step == len(steps)-1:
                    if st.button("Generate and Save Configuration", type="primary", use_container_width=True):
                        if not st.session_state.user_inputs:
                            st.toast("Please select at least one column for 'User Inputs'.", icon="❌")
                        elif not st.session_state.the_answer:
                            st.toast("Please select at least one column for 'The Answer'.", icon="❌")
                        else:
                            csv_file_path = save_csv_data(df)
                            config = {
                                "csv_path": csv_file_path,
                                "buckets": {
                                    "inputs": st.session_state.user_inputs,
                                    "answer": st.session_state.the_answer,
                                    "details": st.session_state.additional_details,
                                    "admin": st.session_state.admin_info
                                }
                            }
                            save_config(config)
                            st.toast("You can now navigate to the 'Calculator' page to use your new tool.", icon="ℹ️")
                            st.toast(f"Configuration saved successfully!", icon="✅")
                            st.balloons()
                            
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.warning("Please ensure you uploaded a valid CSV or XLSX file.")

else:
    st.info("Please upload a CSV or Excel file to begin the configuration process.")
