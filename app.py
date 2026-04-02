############################
### Import Packages 
############################
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Internal files
import pull_data
from config import _item_list


############################
### Load in the Data
############################
def load_data(start, end, item='All items'):

    logger.info(f"Loading data: start={start}, end={end}, item={item}")

    # Pull down data
    all_cpi_df = pull_data.pull_cpi_data(start, end, item)

    # normalize date column to pandas datetime to avoid Timestamp vs date comparison issues
    all_cpi_df['date'] = pd.to_datetime(all_cpi_df['date'])

    return (all_cpi_df)


############################
### Ctreamlit Setup
############################
st.set_page_config(page_title="Inflation Dashboard", layout="wide")
st.title("Consumer Price Index (CPI) Dashboard")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", value=date(2020, 1, 1))
end_date = st.sidebar.date_input("End Date", value=date.today().replace(day=1) - relativedelta(months=1))

# --- Item Choises ---
item_choice = st.sidebar.selectbox("Item", _item_list(), index=2)
logger.info('Itemd:', item_choice)


# Data load (include selected item)
all_cpi_df = load_data(start = start_date, 
                       end = end_date, 
                       item = item_choice)

# --- Main Dashboard ---
# show latest year in header for clarity
latest_year = all_cpi_df['date'].max().year if not all_cpi_df.empty else None

# Center the main chart header
st.markdown(
    f"<h3 style='text-align:center; margin-bottom: 0.5rem;'> {item_choice}: CPI Percentage Change Over Time</h3>",
    unsafe_allow_html=True,
)

# Chart type selector: CPI % change or slope (monthly change)
chart_type = st.sidebar.selectbox("Chart Type", ["CPI % Change", "CPI", 'Slope (3 month % change)'])

# Conversion controls placed below chart type in the sidebar — use Start/End dates from Filters
st.sidebar.markdown("---")
st.sidebar.header("Conversions")
# use arrows and desired casing in labels
direction = st.sidebar.radio("Conversion direction", ("Start date → End Date", "Start date ← End Date"))
conv_amount = st.sidebar.number_input("Amount ($):", min_value=0.0, value=100.0, format="%.2f")

plot_df = all_cpi_df.copy()
print('test:', plot_df['date'].max())
if chart_type == "Slope (3 month % change)":
    # slope = month-over-month change in cpi_pct (percentage points per month)
    plot_df['slope_3m'] = (plot_df['cpi_pct'] - plot_df['cpi_pct'].shift(3)) / plot_df['cpi_pct']
    y_col = 'slope_3m'
    y_label = '3-month running slope (fraction)'
elif chart_type == "CPI":
    y_col = 'cpi_value'
    y_label = 'CPI Value'
else:
    y_col = 'cpi_pct'
    y_label = 'CPI Percentage Change (%)'

# Create Plotly chart with axis labels
fig = px.line(plot_df, x='date', y=y_col,
              labels={y_col: y_label, 'date': 'Date'},
              markers=False)
fig.update_traces(line=dict(width=3))

# Add a small vertical buffer so the line doesn't touch the top of the chart
y_vals = plot_df[y_col].dropna()
if len(y_vals) > 0:
    y_min = float(y_vals.min())
    y_max = float(y_vals.max() * 1.05)
    # use 5% buffer of the range, with a small minimum buffer
    buffer = max((y_max - y_min) * 0.05, 0.5)
    fig.update_yaxes(range=[y_min - buffer, y_max + buffer])

# Improve readability: larger, bold axis titles and bigger tick labels
# ensure x-axis range includes the full data range so latest date appears
# add a small right-side padding so the last label is visible
fig.update_xaxes(title=dict(text='<b>Date</b>', font=dict(size=16, family='Arial', color='black')),
                 tickfont=dict(size=12),
                 tickformat="%b %Y")

#Add or remove % suffix on y-axis based on chart type
if chart_type != "CPI":
    fig.update_yaxes(title=dict(text=f'<b>{y_label}</b>', font=dict(size=16, family='Arial', color='black')),
                    tickfont=dict(size=12),
                    ticksuffix="%")
else:
    fig.update_yaxes(title=dict(text=f'<b>{y_label}</b>', font=dict(size=16, family='Arial', color='black')),
                tickfont=dict(size=12))

# Add a top margin to the layout for extra space, increase default font size, and set chart height
fig.update_layout(hovermode='x unified', margin=dict(t=50), font=dict(size=12), height=520)
st.plotly_chart(fig, use_container_width=True)

# --- Cost Calculator ---
# (Conversion controls moved to the sidebar)
# Use the sidebar inputs `comp_date`, `direction`, and `conv_amount` to perform conversion here
# Use Start Date and End Date from the Filters for conversion

# Conversion calculator header
st.header("Conversion calculator")

start_row = all_cpi_df[all_cpi_df['date'] <= pd.to_datetime(start_date)]
end_row = all_cpi_df[all_cpi_df['date'] <= pd.to_datetime(end_date)]

if start_row.empty or end_row.empty:
    st.error("CPI data not available for the selected Start/End dates.")
else:
    start_row_sorted = start_row.sort_values('date').dropna(subset=['cpi_value'])
    end_row_sorted = end_row.sort_values('date').dropna(subset=['cpi_value'])
    
    start_cpi = start_row_sorted.iloc[-1]['cpi_value']
    start_cpi_date = start_row_sorted.iloc[-1]['date'].date()
    
    end_cpi = end_row_sorted.iloc[-1]['cpi_value']
    end_cpi_date = end_row_sorted.iloc[-1]['date'].date()

    if direction.startswith("End date"):
        converted = conv_amount * (end_cpi / start_cpi)
        st.write(f"{conv_amount:,.2f} USD on {start_cpi_date.strftime('%B %d, %Y')} is equivalent to **{converted:,.2f} USD** on {end_cpi_date.strftime('%B %d, %Y')}.")
    else:
        converted = conv_amount * (start_cpi / end_cpi)
        st.write(f"{conv_amount:,.2f} USD of {item_choice} on {end_cpi_date.strftime('%B %d, %Y')} would buy **{converted:,.2f} USD** on {start_cpi_date.strftime('%B %d, %Y')}.")