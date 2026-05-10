import altair as alt
import polars as pl

# %%
python = (
    pl.read_csv("../python_src/benchmark_runs.csv")
    .filter(pl.col("status") == pl.lit("ok"))
    .select(["library", "dataset", "elapsed_seconds"])
)
# %%
rust = (
    pl.read_csv("../rust_bench/benchmark_results.csv")
    .filter(pl.col("error") != pl.lit("error"))
    .select(["library", "dataset", "elapsed_seconds"])
)
# %%
dataset_order = [
    "1k_line",
    "5k_line",
    "85k_line",
    "170k_line",
    "850k_line",
    "1k_scatter",
    "5k_scatter",
    "500k_scatter",
    "5m_scatter",
    "2k_histogram",
    "10k_histogram",
    "1m_histogram",
    "10m_histogram",
]

small_datasets = [
    "1k_line",
    "5k_line",
    "1k_scatter",
    "5k_scatter",
    "2k_histogram",
    "10k_histogram",
]

large_datasets = [
    "85k_line",
    "170k_line",
    "850k_line",
    "500k_scatter",
    "5m_scatter",
    "1m_histogram",
    "10m_histogram",
]

library_style = {
    "plotters": "#B89048",
    "kuva": "#B86C48",
    "charton": "#B85848",
    "matplotlib": "#3EB87F",
    "altair": "#3EB8A9",
    "plotly": "#3E53B8",
}

library_order = list(library_style.keys())
library_colors = [library_style[name] for name in library_order]
rust_library_order = ["plotters", "kuva", "charton"]
rust_library_colors = [library_style[name] for name in rust_library_order]

# %%
big_datasets_all = (
    pl.concat([python, rust])
    .filter(pl.col("dataset").is_in(large_datasets))
    .group_by(["dataset", "library"])
    .agg(pl.col("elapsed_seconds").median().alias("median_seconds"))
)

chart_all = (
    alt.Chart(big_datasets_all)
    .mark_bar()
    .encode(
        x=alt.X(
            "dataset:N",
            sort=dataset_order,
            title="All Libraries",
            axis=alt.Axis(labelAngle=30),
        ),
        xOffset=alt.XOffset("library:N", sort=library_order),
        y=alt.Y(
            "median_seconds:Q",
            title="Median seconds",
            axis=alt.Axis(tickCount=4),
        ),
        color=alt.Color(
            "library:N",
            sort=library_order,
            scale=alt.Scale(domain=library_order, range=library_colors),
            title="Library",
        ),
        tooltip=[
            alt.Tooltip("dataset:N"),
            alt.Tooltip("library:N"),
            alt.Tooltip("median_seconds:Q", format=".3f"),
        ],
    )
    .properties(width=1200, height=600)
    .configure_axisY(gridDash=[4, 4])
    .configure_axis(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
    .configure_legend(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
)

chart_all.save("benchmarks.png", ppi=300)
# %%
chart_rs = (
    alt.Chart(big_datasets_all.filter(pl.col("library").is_in(rust_library_order)))
    .mark_bar()
    .encode(
        x=alt.X(
            "dataset:N",
            sort=dataset_order,
            title="Rust Libraries",
            axis=alt.Axis(labelAngle=30),
        ),
        xOffset=alt.XOffset("library:N", sort=rust_library_order),
        y=alt.Y(
            "median_seconds:Q",
            title="Median seconds",
            axis=alt.Axis(tickCount=4),
            scale=alt.Scale(domain=[0, 10]),
        ),
        color=alt.Color(
            "library:N",
            sort=rust_library_order,
            scale=alt.Scale(domain=rust_library_order, range=rust_library_colors),
            title="Library",
        ),
        tooltip=[
            alt.Tooltip("dataset:N"),
            alt.Tooltip("library:N"),
            alt.Tooltip("median_seconds:Q", format=".3f"),
        ],
    )
    .properties(width=1200, height=600)
    .configure_axisY(gridDash=[4, 4])
    .configure_axis(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
    .configure_legend(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
)

chart_rs.save("rust_benchmarks.png", ppi=300)

small_datasets_all = (
    pl.concat([python, rust])
    .filter(pl.col("dataset").is_in(small_datasets))
    .group_by(["dataset", "library"])
    .agg(pl.col("elapsed_seconds").median().alias("median_seconds"))
)

small_chart_all = (
    alt.Chart(small_datasets_all)
    .mark_bar()
    .encode(
        x=alt.X(
            "dataset:N",
            sort=dataset_order,
            title="All Libraries",
            axis=alt.Axis(labelAngle=30),
        ),
        xOffset=alt.XOffset("library:N", sort=library_order),
        y=alt.Y(
            "median_seconds:Q",
            title="Median seconds",
            axis=alt.Axis(tickCount=4),
        ),
        color=alt.Color(
            "library:N",
            sort=library_order,
            scale=alt.Scale(domain=library_order, range=library_colors),
            title="Library",
        ),
        tooltip=[
            alt.Tooltip("dataset:N"),
            alt.Tooltip("library:N"),
            alt.Tooltip("median_seconds:Q", format=".3f"),
        ],
    )
    .properties(width=1200, height=600)
    .configure_axisY(gridDash=[4, 4])
    .configure_axis(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
    .configure_legend(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
)

small_chart_all.save("small_benchmarks.png", ppi=300)

chart_rs = (
    alt.Chart(small_datasets_all.filter(pl.col("library").is_in(rust_library_order)))
    .mark_bar()
    .encode(
        x=alt.X(
            "dataset:N",
            sort=dataset_order,
            title="Rust Libraries",
            axis=alt.Axis(labelAngle=30),
        ),
        xOffset=alt.XOffset("library:N", sort=rust_library_order),
        y=alt.Y(
            "median_seconds:Q",
            title="Median seconds",
            axis=alt.Axis(tickCount=4),
        ),
        color=alt.Color(
            "library:N",
            sort=rust_library_order,
            scale=alt.Scale(domain=rust_library_order, range=rust_library_colors),
            title="Library",
        ),
        tooltip=[
            alt.Tooltip("dataset:N"),
            alt.Tooltip("library:N"),
            alt.Tooltip("median_seconds:Q", format=".3f"),
        ],
    )
    .properties(width=1200, height=600)
    .configure_axisY(gridDash=[4, 4])
    .configure_axis(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
    .configure_legend(
        labelFont="Avenir Next",
        titleFont="Avenir Next",
        labelFontSize=30,
        titleFontSize=30,
    )
)

chart_rs.save("rust_benchmarks_small.png", ppi=300)

# %%
# sample size measurement
(pl.concat([python, rust]).group_by(["library"]).agg(pl.all().count()))

# numerical
(
    pl.concat([python, rust])
    .filter(pl.col("library").is_in(["plotters", "matplotlib"]))
    .group_by(["library", "dataset"])
    .agg(pl.all().median())
    .sort(["dataset", "library"])
    .write_csv("plotters_v_mpl.csv")
)

small_datasets_all = (
    pl.concat([python, rust])
    .filter(
        pl.col("dataset").is_in(small_datasets),
        pl.col("library").is_in(["kuva", "charton", "matplotlib"]),
    )
    .group_by(["dataset", "library"])
    .agg(pl.col("elapsed_seconds").median().alias("median_seconds"))
    .write_csv("kuva_mpl.csv")
)
