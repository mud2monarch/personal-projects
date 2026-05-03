# /// script
# dependencies = [
#   "polars"
# ]
# ///

import logging

logging.basicConfig(level=logging.INFO)

import polars as pl


def haversine_miles(
    s_lat: pl.Expr,
    s_lon: pl.Expr,
    e_lat: pl.Expr,
    e_lon: pl.Expr,
    unit: str = "miles",
) -> pl.Expr:

    EARTH_RADIUS = {
        "miles": 3958.8,
        "kilometers": 6371.0,
        "meters": 6371000.0,
        "feet": 20902231.0,
    }
    radius = EARTH_RADIUS[unit]

    s_lat, s_lon, e_lat, e_lon = (
        s_lat.radians(),
        s_lon.radians(),
        e_lat.radians(),
        e_lon.radians(),
    )

    d_lat = e_lat - s_lat
    d_lon = e_lon - s_lon

    a = (d_lat / 2).sin().pow(2) + s_lat.cos() * e_lat.cos() * (d_lon / 2).sin().pow(2)

    return radius * 2 * a.sqrt().arcsin()


logger = logging.getLogger(__name__)

# 85k line chart
# X = dt_minute
# Y = num_rides or avg_duration
# Color by rideable_type
(
    pl.read_parquet("raw/*.parquet")
    .with_columns(
        (pl.col("ended_at") - pl.col("started_at")).alias("duration"),
        pl.col("started_at").dt.truncate("1m").alias("dt_minute"),
    )
    .group_by("rideable_type", "dt_minute")
    .agg(
        pl.col("ride_id").count().alias("num_rides"),
        pl.col("duration").mean().alias("avg_duration"),
    )
    .select(["dt_minute", "num_rides", "avg_duration", "rideable_type"])
    .write_parquet("clean/85k_timeseries.parquet")
)
logger.info("85k timeseries written")

# 500k scatter
# X = distance
# Y = duration
# Color by rideable_type
(
    pl.read_parquet("raw/*.parquet")
    .with_columns(
        haversine_miles(
            pl.col("start_lat"),
            pl.col("start_lng"),
            pl.col("end_lat"),
            pl.col("end_lng"),
        ).alias("distance"),
        (pl.col("ended_at") - pl.col("started_at")).alias("duration"),
    )
    # 99th percentile
    .filter(
        pl.col("distance") < 5.140833,
        pl.col("duration") < pl.duration(minutes=58, seconds=13, milliseconds=473),
    )
    .select(["rideable_type", "distance", "duration"])
    .slice(10_000, 500_000)
    .write_parquet("clean/500k_scatter.parquet")
)
logger.info("500k scatter written")

# 50k scatter
# X = distance
# Y = duration
# Color by rideable_type
(
    pl.read_parquet("raw/*.parquet")
    .with_columns(
        haversine_miles(
            pl.col("start_lat"),
            pl.col("start_lng"),
            pl.col("end_lat"),
            pl.col("end_lng"),
        ).alias("distance"),
        (pl.col("ended_at") - pl.col("started_at")).alias("duration"),
    )
    # 99th percentile
    .filter(
        pl.col("distance") < 5.140833,
        pl.col("duration") < pl.duration(minutes=58, seconds=13, milliseconds=473),
    )
    .select(["rideable_type", "distance", "duration"])
    .slice(10_000, 50_000)
    .write_parquet("clean/50k_scatter.parquet")
)
logger.info("50k scatter written")

# 100k histogram
(
    pl.read_parquet("raw/*.parquet")
    .with_columns(
        (pl.col("ended_at") - pl.col("started_at")).alias("duration"),
    )
    # 99th percentile
    .filter(
        pl.col("duration") < pl.duration(minutes=58, seconds=13, milliseconds=473),
    )
    .select("duration")
    .slice(10_000, 100_000)
    .write_parquet("clean/100k_histogram.parquet")
)
logger.info("100k histogram written")

# 1m histogram
(
    pl.read_parquet("raw/*.parquet")
    .with_columns(
        (pl.col("ended_at") - pl.col("started_at")).alias("duration"),
    )
    # 99th percentile
    .filter(
        pl.col("duration") < pl.duration(minutes=58, seconds=13, milliseconds=473),
    )
    .select("duration")
    .slice(10_000, 1_000_000)
    .write_parquet("clean/1m_histogram.parquet")
)
logger.info("1m histogram written")
