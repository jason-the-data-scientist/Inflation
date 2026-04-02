############################
### Import Packages 
############################
try:    
    import cpi
except:
    import subprocess
    subprocess.check_call(["python", "-m", "pip", "install", "cpi"])
    import cpi
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Updating cpi data
# cpi.update()

# Internal
from config import _item_list


############################
### Get Month Difference
############################
def diff_month(d1, d2):
    """
    Description:
        Calculates the total difference in months between two date objects.
    """

    logger.info(' Function: diff_month')
    
    # Get the different in months between two dates
    month_diff = (d2.year - d1.year) * 12 + d2.month - d1.month

    return (month_diff)


############################
### Fetch Item data
############################
def _fetch_item_data(start_date, end_date, item: str):
    """
    Helper to fetch data for a single item.
    """

    logger.info(' Function: _fetch_item_data')

    # Create an empty dataframe
    cpi_df = pd.DataFrame(columns=["date", "cpi_value"])

    # Loop through all months in range
    for month_i in range(0, diff_month(start_date, end_date) + 1):
        this_date = start_date + relativedelta(months=month_i)

        # Get one month's data
        try:
            cpi_this_month_value = cpi.get(this_date, items=item)

            # Create a dataframe for this month's data
            cpi_this_month = pd.DataFrame({
                "date": [this_date],
                "cpi_value": [cpi_this_month_value]
            })

            #Combine the data together
            cpi_df = pd.concat([cpi_df, cpi_this_month], axis = 0)
        except Exception as e:
            logger.info(f"Data not available for {this_date.strftime('%Y-%m-%d')}. Skipping. Error: {e}")

    return (cpi_df)


############################
### Get Month Difference
############################
def _calculations(cpi_df):

    logger.info(' Function: _calculations')
    # Annualize the CPI 
    cpi_df['cpi_annualized'] = ((1+ (cpi_df['cpi_value'] - cpi_df['cpi_value'].shift(1)) / cpi_df['cpi_value'].shift(1)) **12 - 1) * 100

    # Calculate the relative CPI value
    cpi_df['cpi_relative_value'] = cpi_df['cpi_value'] / cpi_df['cpi_value'].iloc[0]

    # Calculate the percentage change in CPI from the start date
    cpi_df['cpi_pct'] = (cpi_df['cpi_relative_value'] - 1) * 100

    return(cpi_df)


############################
### Get CPI Range
############################
def pull_cpi_data(start_date, 
                  end_date, 
                  item = 'All items'):
    """
    Description:
        Get CPI values for a date range for a given item (or 'all').
        For 'all' item, aggregates across all items in the CSV.
    """
    
    # Ensure item is a string
    if not isinstance(item, str):
        item = str(item)
    
    # Log it
    logger.info(f"get_cpi_range called with item={item}")

    # Get item list
    item_list = _item_list()

    # Make sure item is in the list
    if item not in item_list:
        logger.error(f" This item does not exist.")

    # Retrieve the data
    cpi_df = _fetch_item_data(start_date, end_date, item)

    # Add aditional calculations
    cpi_df = _calculations(cpi_df)

    return(cpi_df)