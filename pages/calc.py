import streamlit as st
import pandas as pd
import json
import os
from st_aggrid import AgGrid

ADMIN_ENABLED = os.getenv("ADMIN_ENABLED", "false").lower() == "true"

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
input_cols = buckets.get("inputs", [])
answer_cols = buckets.get("answer", [])
detail_cols = buckets.get("details", [])
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

    cols_to_view = input_cols + answer_cols + detail_cols
    if ADMIN_ENABLED:
        cols_to_view += admin_cols
  
    grid_df = filtered_df[cols_to_view].copy()
    grid_df = grid_df.reset_index()
    column_defs = [
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
        ]
    
    if ADMIN_ENABLED:
        column_defs.append(
            {
                "field": "Admin Info",
                "children": [
                    {
                        "field": col,
                        "hide": True if grid_df[col].isnull().all() else False,  # Hide column if all values are NaN
                    }
                    for col in admin_cols
                ],
            }
        )

    column_defs.append(
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
                
            }
    )

    grid_options = {
        "columnDefs": column_defs,
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