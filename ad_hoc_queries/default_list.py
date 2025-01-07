"""
Locally,
Install NVM `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash`
Install latest NPM `nvm install --lts`
Build the NPM package `npm i @uniswap/default-token-list`
Grab the JSON file in the `build/` folder: uniswap_default_tokenlist.json. Put in directory.

Then, extract all contract addresses into a dataframe.
"""

import pandas as pd
import json
import re

# Read the JSON file
with open('uniswap_default_tokenlist.json', 'r') as f:
    data = json.load(f)
    
# Convert JSON to string and find all 0x addresses
json_str = json.dumps(data)
addresses = re.findall(r'0x[a-fA-F0-9]{40}', json_str)  # specifically match 40 char ETH addresses

# Create DataFrame
default_list = pd.DataFrame(addresses, columns=['address'])
default_list['address'] = default_list['address'].str.lower() # our data need addresses in lowercase