# %%
# imports
import requests
import polars as pl
from polars import col
import google.auth
from google.cloud import bigquery
import matplotlib.pyplot as plt

# creds are stored locally
credentials, project = google.auth.default()

# Initialize BigQuery client
client = bigquery.Client(project='uniswap-labs')

# ping Coingecko API to check if all is good
url = "https://api.coingecko.com/api/v3/ping"
response = requests.get(url)
print(response.text)

# %%
# These functions get data from APIs
def get_nance_volume(_days=365):
    # get Binance volume, which only comes in BTC denomination
    url = f"https://api.coingecko.com/api/v3/exchanges/binance/volume_chart?days={_days}"
    response = requests.get(url)
    data = response.json()

    # now get BTC_USD price at each day so I can join it into the btc-denominated volume
    url2 = f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={_days}'
    response2 = requests.get(url2)
    data2 = response2.json()

    return data, data2

# Fetch data from BigQuery
def fetch_bigquery_data(query):
    query_job = client.query(query)
    results = query_job.result()
    # turn the result into a Polars dataframe
    # @dev TODO: should I pull this conversion out into another block?
    goog_data = pl.from_arrow(results.to_arrow())

    return goog_data

# %%
# get Binance volumes

data, data2 = get_nance_volume()

# %%
# get interface volume

_query = ("""
-- omitted
""")

data_bigquery = fetch_bigquery_data(_query)

# %%
# take the data JSON response and turn it into a Polars dataframe
df = (pl.DataFrame(data)
        # from that df, make two new columns
        .select(
            # first column named 'dt' is datetime truncated to day
            pl.from_epoch('column_0', time_unit='ms').dt.truncate('1d').alias('dt'),
            # second column named 'btc_vol' is F32 of btc vol
            col('column_1').cast(pl.Float32).alias('btc_vol')
        )
    )
# take the data2 JSON response and turn it into a Polars dataframe
df2 = (pl.DataFrame(data2['prices'])
        .transpose()
        .select(
            pl.from_epoch('column_0', time_unit='ms').dt.truncate('1d').alias('dt'),
            col('column_1').cast(pl.Float32).alias('btc_usd_px')
        )
    )

df = (
        df.join(
            df2,
            on='dt',
            how='left'
        ).select(
            # this cast is necessary to get everything into microseconds
            col('dt').cast(pl.Datetime),
            (col('btc_vol') * col('btc_usd_px'))
            .alias('usd_vol')
        ).join(
            data_bigquery.with_columns(
                col('interface_dt').cast(pl.Datetime) # this gets rid of the UTC timestamp.
            ),
            left_on='dt',
            right_on='interface_dt',
            how='inner'
        ).rename(
            {'volume':'interface volume',
            'usd_vol':'binance volume'}
        ).sort(
            'dt'
        ).with_columns(
            pl.col('binance volume').rolling_sum(window_size=30).alias('Binance volume l30d (left)'),
            pl.col('interface volume').rolling_sum(window_size=30).alias('Interface volume L30d (right)')
        ).sort(
            'dt',
            descending = True
        )
    )

# %%
df.write_csv('interface_volume.csv')

# %%
plt.plot('dt', 'Interface volume L30d (right)', data=df)
