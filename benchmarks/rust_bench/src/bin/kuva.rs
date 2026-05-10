use anyhow::Result;
use csv::WriterBuilder;
use kuva::prelude::*;
use kuva::render_to_raster;
use rust_bench::bench_data::{
    scaled_hist_df, scaled_line_df, scaled_scatter_df, sliced_hist_df, sliced_line_df,
    sliced_scatter_df,
};
use rust_bench::benchmark_io::{run_id, utc_timestamp};
use rust_bench::kuva_utils::{hist_from_df, line_from_df, scatter_from_df};
use std::fs;
use std::fs::OpenOptions;
use std::time::Instant;

fn line(filepath: &str, scale: usize, output_name: &str) -> Result<f64> {
    let df = scaled_line_df(filepath, scale)?;
    let start = Instant::now();
    let line_data = line_from_df(&df)?;
    let line_plot = LinePlot::new().with_data(line_data.points);

    let plots = vec![Plot::Line(line_plot)];
    let layout = Layout::auto_from_plots(&plots)
        .with_title("Rides over time")
        .with_x_label("UNIX seconds")
        .with_y_label("Number of rides");

    let png_bytes = render_to_raster(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;
    fs::write(output_name, png_bytes)?;

    Ok(start.elapsed().as_secs_f64())
}

fn scatter(filepath: &str, scale: usize, output_name: &str) -> Result<f64> {
    let df = scaled_scatter_df(filepath, scale)?;
    let start = Instant::now();
    let scatter_plot_data = scatter_from_df(&df)?;
    let classic_plot = kuva::prelude::ScatterPlot::new()
        .with_data(scatter_plot_data.classic_points)
        .with_color("blue")
        .with_size(0.5);
    let electric_plot = kuva::prelude::ScatterPlot::new()
        .with_data(scatter_plot_data.electric_points)
        .with_color("orange")
        .with_size(0.5);

    let plots = vec![Plot::Scatter(classic_plot), Plot::Scatter(electric_plot)];
    let layout = Layout::auto_from_plots(&plots)
        .with_title("Rides over time")
        .with_x_label("distance")
        .with_y_label("duration (seconds)");

    let png_bytes = render_to_raster(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;
    fs::write(output_name, png_bytes)?;

    Ok(start.elapsed().as_secs_f64())
}

fn hist(filepath: &str, scale: usize, output_name: &str) -> Result<f64> {
    let df = scaled_hist_df(filepath, scale)?;
    let start = Instant::now();
    let hist_data = hist_from_df(&df)?;
    let histogram = kuva::prelude::Histogram::new()
        .with_data(hist_data)
        .with_bins(60);

    let plots = vec![Plot::Histogram(histogram)];
    let layout = Layout::auto_from_plots(&plots).with_title("Distribution of ride times");

    let png_bytes = render_to_raster(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;
    fs::write(output_name, png_bytes)?;

    Ok(start.elapsed().as_secs_f64())
}

fn write_result(
    writer: &mut csv::Writer<std::fs::File>,
    run_id: &str,
    library: &str,
    benchmark: &str,
    result: Result<f64>,
) -> Result<()> {
    let ts = utc_timestamp()?;
    match result {
        Ok(elapsed) => writer.write_record([
            run_id,
            ts.as_str(),
            library,
            benchmark,
            "ok",
            &elapsed.to_string(),
            "",
        ])?,
        Err(err) => writer.write_record([
            run_id,
            ts.as_str(),
            library,
            benchmark,
            "error",
            "",
            &err.to_string(),
        ])?,
    }

    Ok(())
}

fn main() -> Result<()> {
    let run_id = run_id();
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("benchmark_results.csv")?;
    let mut writer = WriterBuilder::new().has_headers(true).from_writer(file);

    let line_slice_cases = [("1k_line", 1_000usize), ("5k_line", 5_000usize)];
    for (label, size) in line_slice_cases {
        let result = sliced_line_df("../data/clean/85k_timeseries.parquet", size).and_then(|df| {
            let start = Instant::now();
            let line_data = line_from_df(&df)?;
            let line_plot = LinePlot::new().with_data(line_data.points);

            let plots = vec![Plot::Line(line_plot)];
            let layout = Layout::auto_from_plots(&plots)
                .with_title("Rides over time")
                .with_x_label("UNIX seconds")
                .with_y_label("Number of rides");

            let png_bytes = render_to_raster(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;
            fs::write(format!("output/kuva_{label}.png"), png_bytes)?;

            Ok(start.elapsed().as_secs_f64())
        });
        write_result(&mut writer, run_id.as_str(), "kuva", label, result)?;
    }

    let line_cases = [
        ("85k_line", 1usize),
        ("170k_line", 2usize),
        ("850k_line", 10usize),
    ];
    for (label, scale) in line_cases {
        let result = line(
            "../data/clean/85k_timeseries.parquet",
            scale,
            &format!("output/kuva_{label}.png"),
        );
        write_result(&mut writer, run_id.as_str(), "kuva", label, result)?;
    }

    let hist_slice_cases = [("2k_histogram", 2_000usize), ("10k_histogram", 10_000usize)];
    for (label, size) in hist_slice_cases {
        let result = sliced_hist_df("../data/clean/1m_histogram.parquet", size).and_then(|df| {
            let start = Instant::now();
            let hist_data = hist_from_df(&df)?;
            let histogram = kuva::prelude::Histogram::new()
                .with_data(hist_data)
                .with_bins(60);

            let plots = vec![Plot::Histogram(histogram)];
            let layout = Layout::auto_from_plots(&plots).with_title("Distribution of ride times");

            let png_bytes = render_to_raster(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;
            fs::write(format!("output/kuva_{label}.png"), png_bytes)?;

            Ok(start.elapsed().as_secs_f64())
        });
        write_result(&mut writer, run_id.as_str(), "kuva", label, result)?;
    }

    let hist_cases = [("1m_histogram", 1usize), ("10m_histogram", 10usize)];
    for (label, scale) in hist_cases {
        let result = hist(
            "../data/clean/1m_histogram.parquet",
            scale,
            &format!("output/kuva_{label}.png"),
        );
        write_result(&mut writer, run_id.as_str(), "kuva", label, result)?;
    }

    let scatter_slice_cases = [("1k_scatter", 1_000usize), ("5k_scatter", 5_000usize)];
    for (label, size) in scatter_slice_cases {
        let result = sliced_scatter_df("../data/clean/500k_scatter.parquet", size).and_then(|df| {
            let start = Instant::now();
            let scatter_plot_data = scatter_from_df(&df)?;
            let classic_plot = kuva::prelude::ScatterPlot::new()
                .with_data(scatter_plot_data.classic_points)
                .with_color("blue")
                .with_size(0.5);
            let electric_plot = kuva::prelude::ScatterPlot::new()
                .with_data(scatter_plot_data.electric_points)
                .with_color("orange")
                .with_size(0.5);

            let plots = vec![Plot::Scatter(classic_plot), Plot::Scatter(electric_plot)];
            let layout = Layout::auto_from_plots(&plots)
                .with_title("Rides over time")
                .with_x_label("distance")
                .with_y_label("duration (seconds)");

            let png_bytes = render_to_raster(plots, layout, 2.0).map_err(|e| anyhow::anyhow!(e))?;
            fs::write(format!("output/kuva_{label}.png"), png_bytes)?;

            Ok(start.elapsed().as_secs_f64())
        });
        write_result(&mut writer, run_id.as_str(), "kuva", label, result)?;
    }

    let scatter_cases = [("500k_scatter", 1usize), ("5m_scatter", 10usize)];
    for (label, scale) in scatter_cases {
        let result = scatter(
            "../data/clean/500k_scatter.parquet",
            scale,
            &format!("output/kuva_{label}.png"),
        );
        write_result(&mut writer, run_id.as_str(), "kuva", label, result)?;
    }

    writer.flush()?;

    Ok(())
}
