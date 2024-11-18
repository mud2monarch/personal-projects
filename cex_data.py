# imports
import requests
import polars as pl
from dotenv import load_dotenv
import os
from datetime import datetime

# setup constants
load_dotenv()
CG_API_KEY = os.getenv('CG-PRO-API')
exchanges = ['binance', 'gdax', 'okex'] # @dev TODO: make this customizable/input
SECONDS_IN_A_DAY = 86400
THIRTY_DAYS = SECONDS_IN_A_DAY * 30

def load_or_create_df() -> pl.DataFrame:
    try:
        return pl.read_csv('cex_data.csv')
    except Exception as e:
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("returning empty dataframe")
        return pl.DataFrame()

def make_request(endpoint: str):
    headers = {
        'accept': 'application/json',
        'x-cg-pro-api-key': CG_API_KEY
    }

    url = f"https://pro-api.coingecko.com/api/v3/{endpoint}"
    response = requests.get(url, headers = headers)
    return response.json()

def get_historical_cex_volume(
        venue: str,
        start_unix: int,
        end_unix: int) -> pl.DataFrame:
    # @param venue: name of the venue. See "id" at https://api.coingecko.com/api/v3/exchanges/list.
    # @param start_unix: start date of the time range, in unix seconds.
    # @param end_unix: end date of the time range, in unix seconds. Must be <31 days after start_unix.
    # https://www.epochconverter.com/

    endpoint = f"exchanges/{venue}/volume_chart/range?from={start_unix}&to={end_unix}"
    raw = make_request(endpoint=endpoint)
    
    # CG API is currently returning a list of lists, e.g., 
    # [[1700403600000.0,"181926.5992543248794886"],
    # [1700490000000.0,"225520.5509631902435399"]]
    # so I parse the list-of-lists into a list-of-dicts for Polars
    #
    # I also, at this point, convert from MS to S so that I can easily iterate and pull values
    data = []
    for row in raw:
        new_dict = {
            'unix_timestamp' : row[0]/1000,
            'btc_vol' : row[1]
        }
        data.append(new_dict)

    return pl.DataFrame(
            data,
            {'unix_timestamp': pl.Int64, 'btc_vol': pl.Float64}
        ).with_columns(
            # cast unix S timestamp to date; polars represents dates as days since UNIX start
            (pl.col('unix_timestamp') / SECONDS_IN_A_DAY).cast(pl.Date).alias('dt'),
            # add name of the venue to the dataframe
            pl.lit(venue).alias('venue'),
            pl.lit(datetime.today()).alias('date_recorded')
    )

def find_missing_data(
    df: pl.DataFrame) -> pl.DataFrame:
    # @param df: your existing data

    missing_data = pl.DataFrame()

    # cycle through all exchanges in the defined set
    for x in exchanges:
        missing_dates = (
            # create a DataFrame with a date range between July 15, 2023 (i.e., start of our usd_amount_shown_to_user) and today.
            pl.DataFrame().with_columns(
                pl.date_range(pl.date(2023, 7, 15), datetime.today(), "1d").alias('dt')
            ).join(
            # ANTI-join it to the existing data
            # filtered on the particular venue we're working with right now
                df.filter(pl.col('venue') == x),
                on="dt",
                how="anti")
            # this produces a list of days that DON'T have any data for this particular venue
            .with_columns(
            # generate the unix timestamp for those days and sort in ascending order
                ((pl.col('dt').cast(pl.Int64)) * SECONDS_IN_A_DAY).alias('unix_timestamp')
            ).sort('dt')
            .with_columns(
            # divide then floor the unix timestamp by 30 days to cut the set into 30 day chunks
                (pl.col('unix_timestamp').cast(pl.Float64) / THIRTY_DAYS).floor().alias('group')
            ).group_by(
            # find the starting and ending unix timestamp for each 'group', or chunk
                by='group', maintain_order=True)
            .agg(
                [
                    pl.col('unix_timestamp').min().alias('start_timestamp'),
                    pl.col('unix_timestamp').max().alias('end_timestamp')
                ]
            ).with_columns(
            # add back in the name of the venue
                pl.lit(x).alias('venue')
            ).select(
                [
                    'venue',
                    'start_timestamp',
                    'end_timestamp'
                ]
            )
        )
        
        # print out the starting unix timestamp, ending unix timestamp, and venue that are missing
        missing_data = pl.concat([missing_data, missing_dates])

    return missing_data

def fill_missing_data(
    df: pl.DataFrame) -> pl.DataFrame:
    
    missing_data = find_missing_data(df)
    
    for row in missing_data.iter_rows():
        try:
            new_data = get_historical_cex_volume(
                venue= row[0],
                start_unix= row[1],
                end_unix= row[2]
            )
        except Exception as e:
            print(f"Error processing {row[0]}: {str(e)}")
        
        df = pl.concat([df, new_data])
    
    return df

def main():
    df = load_or_create_df()
    print(find_missing_data(df))
    new_df = fill_missing_data(df)
    new_df.write_csv('cex_data.csv')

if __name__ == "__main__":
    main()