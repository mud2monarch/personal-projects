# %%
import os
import glob
import pprint
import polars as pl

# %%
csv_files = []
base_dir = '2023-citibike-tripdata'

for month in os.listdir(base_dir):
    month_path = os.path.join(base_dir, month)
    if os.path.isdir(month_path):
        # for file in os.listdir(month_path):
        csv_files.extend(glob.glob(os.path.join(month_path, '*.csv')))

pprint.pprint(csv_files)

# %%
schema = {
    'ride_id': pl.String,
    'rideable_type': pl.Categorical,
    'started_at': pl.Datetime,
    'ended_at': pl.Datetime,
    'start_station_name': pl.String,
    'start_station_id': pl.String, # there are two stations, JC064 and JC065 that are not Float-formattable. Also wonder if this should be a pl.Categorical.
    'end_station_name': pl.String,
    'end_station_id': pl.String,
    'start_lat': pl.Float64,
    'start_lng': pl.Float64,
    'end_lat': pl.Float64,
    'end_lng': pl.Float64,
    'member_casual': pl.Categorical
}

# %%
df = pl.read_csv('2023-citibike-tripdata/202301-citibike-tripdata/202301-citibike-tripdata_1.csv', schema = schema)

df.head()

# %%
valid_lazy_frames = []
invalid_lazy_frames = []

for path in csv_files:
    try:
        lf = pl.scan_csv(path)
        valid_lazy_frames.append(path)
    except Exception as e:
        invalid_lazy_frames.append(path)
        print(f"Error processing {path}: {str(e)}")

pprint.pprint(f'length of invalid lazy frames is {len(invalid_lazy_frames)}')
pprint.pprint(invalid_lazy_frames)

# %%
pl.scan_csv(csv_files, schema=schema).sink_parquet('2023-citibike-tripdata.parquet')