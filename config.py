############################
### Import Packages
############################
import pandas as pd

# Ignore warnings
import warnings
warnings.filterwarnings("ignore")

############################
### Fetch List of All Items
############################
def _item_list():
    """
    Retrieve the list of all items and their names.
    """

    url = "https://raw.githubusercontent.com/palewire/cpi/35da72a4628d0b1be9ecfc1a323451b98f69af4a/data/items.csv"
    
    # Read in csv file
    df = pd.read_csv(url)

    # Create a list of all items
    ITEMS = df['name'].tolist()

    return(ITEMS)