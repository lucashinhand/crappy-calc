import streamlit as st
import pandas as pd
import json
import os
from st_aggrid import AgGrid

# --- Page Configuration ---
st.set_page_config(
    page_title="Price Calculator",
    page_icon="💰",
    layout="wide"
)

# --- Helper Functions ---
def load_config():
    """Loads the configuration file."""
    config_path = os.path.join("data", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return None

def load_data(csv_path):
    """Loads the data from the CSV file."""
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

def generate_gh_markdown_table(df):
    """Generates a GitHub-flavored markdown table from a DataFrame, using :small[value] for each cell."""
    if df.empty:
        return ""
    columns = df.columns.tolist()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(f":small[{x}]" if pd.notna(x) else "" for x in row) + " |"
        for row in df.to_numpy()
    ]
    return "\n".join([header, separator] + rows)


# --- Main App Logic ---
config = load_config()

if not config:
    st.warning("Calculator not configured yet!")
    st.info("Please go to the 'Configure Calculator' page first to upload your data and set up the tool.")
    st.stop()

df = load_data(config["csv_path"])

if df is None:
    st.error("Data file not found! Please re-configure the calculator.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")
st.sidebar.markdown("Use the options below to find a price.")

filters = {}
buckets = config["buckets"]
input_cols = buckets["inputs"]
answer_cols = buckets["answer"]
detail_cols = buckets["details"]
admin_cols = buckets.get("admin", [])

for col in input_cols:
    options = sorted(df[col].dropna().unique().tolist())
    
    if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() > 10:
        selected_val = st.sidebar.select_slider(f"Select {col}", options=options, value=options[0])
        filters[col] = selected_val
    else:
        options_with_all = ["All"] + options
        selected_val = st.sidebar.selectbox(f"Select {col}", options=options_with_all, index=0)
        if selected_val != "All":
            filters[col] = selected_val

# --- Filtering Logic ---
filtered_df = df.copy()
for key, value in filters.items():
    filtered_df = filtered_df[filtered_df[key] == value]

# --- Display Results ---
st.header("Available Options")

if filtered_df.empty:
    st.warning("No options found for the selected criteria. Please adjust your filters.")
else:
    st.markdown(f"Found **{len(filtered_df)}** matching options.")
    # styled_df = filtered_df.copy()[display_cols].map(lambda x: f":small[{x}]" if pd.notna(x) else "")

    # implement this https://arnaudmiribel.github.io/streamlit-extras/extras/grid/
    # st.markdown(generate_gh_markdown_table(styled_df))    

    # gb.configure_pagination(paginationAutoPageSize=True)
    # gb.configure_side_bar()
    # # Enable text wrapping for all columns
    # for col in grid_df.columns:
    #     gb.configure_column(col, wrapText=True, autoHeight=True)
    grid_df = filtered_df[input_cols + answer_cols + detail_cols].copy()
    grid_df = grid_df.reset_index()
    grid_options = {
        "columnDefs": [
            {
                "field": "Inputs",
                "children": [
                    {
                        "field": col,
                    }
                    for col in input_cols
                ],
            },
            {
                "field": "Details",
                "children": [
                    {
                        "field": col,
                        "hide": True if grid_df[col].isnull().all() else False,  # Hide column if all values are NaN
                    }
                    for col in detail_cols
                ],
            },
            {
                "field": "Answers",
                "children": [
                    {
                        "field": col,
                        "pinned": "right",
                        "resizable": False,
                        "headerClass": "bold-header",
                        "cellStyle": {
                            "textAlign": "center",
                            "fontWeight": "bold",
                        },
                    }
                    for col in answer_cols
                ],
                "headerClass": "bold-header",
                "resizable": False,
                
            },
            
        ],
        "defaultColDef": {
            "cellStyle": {"textAlign": "left"},
            "suppressMenu": True,
            "sortable": False,
        },
        # "headerHeight": 50,
        "suppressContextMenu": True,
        "suppressMovableColumns" : True,
        # 'suppressColumnVirtualisation': True,
        "autoSizeStrategy": {
            "type": "fitCellContents"
        },
        "pagination": True,  # <-- Enable pagination
        "paginationAutoPageSize": True,
        "domLayout": grid_df.shape[0] > 5 and "normal" or "autoHeight",  # Use autoHeight if less than 10 rows
    }

    custom_css = {
        ".bold-header > div": {
            "font-weight": "bold",
            "margin": "0 auto"
        },
        ".bold-header span": {
            "font-weight": "bold",
            "margin": "0 auto"
        }
    }

    AgGrid(
        grid_df,
        gridOptions=grid_options,
        # fit_columns_on_grid_load=True,
        theme="alpine",
        custom_css=custom_css,
        height=500,  # Set grid height in pixels

    )


    

