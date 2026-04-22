import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import re

# --------------------------------------------------
# Page setup
# --------------------------------------------------
st.set_page_config(
    page_title="Compressors Constraint Dashboard",
    layout="wide"
)

st.title("Compressors – Constraints vs Date")

# --------------------------------------------------
# Excel file
# --------------------------------------------------
excel_path = "Excel.xlsm"

# --------------------------------------------------
# Read Compressors sheet (no headers)
# --------------------------------------------------
raw = pd.read_excel(
    excel_path,
    sheet_name="Compressors",
    header=None
)

# --------------------------------------------------
# Header rows
# Row 0 -> Constraint / Variable type (forward-filled)
# Row 1 -> Tags (compressor, DS-min, DS-max)
# --------------------------------------------------
constraint_row = raw.iloc[0].ffill()
tag_row = raw.iloc[1]

# --------------------------------------------------
# Data rows start from row 4
# --------------------------------------------------
data = raw.iloc[4:].copy()

data.iloc[:, 0] = pd.to_datetime(data.iloc[:, 0], errors="coerce")
data = data.dropna(subset=[data.columns[0]])
dates = data.iloc[:, 0]

# --------------------------------------------------
# Build mappings
# --------------------------------------------------
normal_constraints = {}     # constraint -> { tag -> col_idx }
mw_constraints = {}         # MW block -> { tag -> col_idx }

for col_idx in range(1, raw.shape[1]):

    constraint = constraint_row[col_idx]
    tag = tag_row[col_idx]

    if pd.isna(constraint) or pd.isna(tag):
        continue

    constraint = str(constraint)
    tag = str(tag)

    if constraint.startswith("Molecular weight"):
        mw_constraints.setdefault(constraint, {})[tag] = col_idx
    else:
        normal_constraints.setdefault(constraint, {})[tag] = col_idx

# --------------------------------------------------
# Sidebar: constraint selection
# --------------------------------------------------
st.sidebar.header("Controls")

selected_constraints = st.sidebar.multiselect(
    "Select constraint / variable type:",
    list(normal_constraints.keys()),
    default=list(normal_constraints.keys())
)

# --------------------------------------------------
# NORMAL CONSTRAINT PLOTS
# --------------------------------------------------
for constraint in selected_constraints:

    tag_dict = normal_constraints[constraint]
    tags = list(tag_dict.keys())

    st.markdown(f"### {constraint}")

    # Clean key to avoid Streamlit state issues
    safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", constraint)

    # ✅ MULTI-SELECT DROPDOWN (default = base tag only)
    selected_tags = st.multiselect(
        "Select tags:",
        options=tags,
        default=[tags[0]],
        key=f"tags_{safe_key}"
    )

    fig, ax = plt.subplots(figsize=(12, 4))

    for tag in selected_tags:
        ax.plot(
            dates,
            data.iloc[:, tag_dict[tag]],
            label=tag,
            linewidth=1.3
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.set_title(f"{constraint} vs Date")
    ax.grid(True)

    if "Constraint" in constraint:
        ax.axhline(100, color="red", linestyle="--")

    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

# --------------------------------------------------
# MOLECULAR WEIGHT (ONE PLOT PER COMPRESSOR BLOCK)
# --------------------------------------------------
if mw_constraints:

    st.markdown("## Molecular Weight")

    for mw_block, tag_dict in mw_constraints.items():

        tags = list(tag_dict.keys())
        st.markdown(f"### {mw_block}")

        safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", mw_block)

        # ✅ MULTI-SELECT DROPDOWN (base + DS-min/max optional)
        selected_tags = st.multiselect(
            "Select tags:",
            options=tags,
            default=[tags[0]],
            key=f"mw_tags_{safe_key}"
        )

        fig, ax = plt.subplots(figsize=(12, 4))

        for tag in selected_tags:
            ax.plot(
                dates,
                data.iloc[:, tag_dict[tag]],
                label=tag,
                linewidth=1.5
            )

        ax.set_xlabel("Date")
        ax.set_ylabel("Molecular weight")
        ax.set_title(f"{mw_block} vs Date")
        ax.grid(True)

        ax.legend()
        st.pyplot(fig)
        plt.close(fig)
