# Plotting library benchmarks

I'm interested in finding, or helping create, a very fast plotting library in Python. UV, Polars, Ruff, and ty have made Python DS significantly better; plotting is one of the areas most in need of improvement.

Here I benchmark leading Python plotting libraries against Rust plotting libraries in the narrow scope of polars dataframe to png export.

The libraries I'm testing are:
| Lang | Library |
| --- | --- |
| Python | MatPlotLib |
| Python | Plotly |
| Rust | Plotters |
| Rust | Kuva |
| Rust | Charton |

And the test cases are:
- 1k, 5k, 85k, 170k, and 850k datapoint line charts
- 2k, 10k, 1m, and 10m datapoint histograms
- 1k, 5k, 500k, and 5m datapoint scatter plots
