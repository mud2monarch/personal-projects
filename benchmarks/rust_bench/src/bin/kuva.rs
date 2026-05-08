use anyhow::Result;
use csv::WriterBuilder;
use kuva::prelude::*;
use rust_bench::kuva_utils::*;
use std::fs;
use std::fs::OpenOptions;
use std::time::Instant;

fn main() -> Result<()> {
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("benchmark_results.csv")?;
    let mut writer = WriterBuilder::new().has_headers(true).from_writer(file);

    // Begin timing 1
    let line_data_85k = line("../data/clean/85k_timeseries.parquet").unwrap();

    let start = Instant::now();
    let line_plot = LinePlot::new().with_data(line_data_85k.points);

    let plots = vec![Plot::Line(line_plot)];
    let layout = Layout::auto_from_plots(&plots)
        .with_title("Rides over time")
        .with_x_label("UNIX seconds")
        .with_y_label("Number of rides");

    let png_bytes = render_to_png(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;

    let line_elapsed = start.elapsed();
    writer.write_record(["kuva", "85k_line", &line_elapsed.as_secs_f64().to_string()])?;

    _ = fs::write("85k_line.png", png_bytes)?;

    let scatter_plot_data = scatter("../data/clean/500k_scatter.parquet").unwrap();

    // Begin timing 2
    let start = Instant::now();
    let scatter_plot = kuva::prelude::ScatterPlot::new()
        .with_data(scatter_plot_data.points)
        .with_colors(scatter_plot_data.color_by.unwrap())
        .with_size(0.2);

    let plots = vec![Plot::Scatter(scatter_plot)];
    let layout = Layout::auto_from_plots(&plots)
        .with_title("Rides over time")
        .with_x_label("distance")
        .with_y_label("duration (seconds)");

    let png_bytes = render_to_png(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;

    let scatter_elapsed = start.elapsed();
    writer.write_record([
        "kuva",
        "500k_scatter",
        &scatter_elapsed.as_secs_f64().to_string(),
    ])?;
    _ = fs::write("500k_scatter.png", png_bytes)?;

    let hist_data = hist("../data/clean/1m_histogram.parquet").unwrap();

    // Begin timing 3
    let start = Instant::now();
    let histogram = kuva::prelude::Histogram::new()
        .with_data(hist_data)
        .with_bins(60);

    let plots = vec![Plot::Histogram(histogram)];
    let layout = Layout::auto_from_plots(&plots).with_title("Distribution of ride times");

    let png_bytes = render_to_png(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;

    let hist_elapsed = start.elapsed();
    writer.write_record([
        "kuva",
        "1m_histogram",
        &hist_elapsed.as_secs_f64().to_string(),
    ])?;

    _ = fs::write("1m_histogram.png", png_bytes)?;

    _ = writer.flush()?;

    Ok(())
}
