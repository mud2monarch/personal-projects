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
- 85k datapoint timeseries (line)
- 85k datapoint timeseries (column)
- 500k datapoint scatter plot
- 50k datapoint scatter plot
- 100k datapoint histogram
- 1m datapoint histogram