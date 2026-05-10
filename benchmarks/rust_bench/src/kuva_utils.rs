use anyhow::Result;
use polars::prelude::*;

pub struct ScatterPlot {
    pub points: Vec<(f64, f64)>,
    pub color_by: Option<Vec<String>>,
}

pub struct GroupedScatterPlot {
    pub classic_points: Vec<(f64, f64)>,
    pub electric_points: Vec<(f64, f64)>,
}

pub fn hist_from_df(df: &DataFrame) -> Result<Vec<f64>> {
    let values: Vec<f64> = df.column("seconds")?.f64()?.into_no_null_iter().collect();

    Ok(values)
}

pub fn scatter_from_df(df: &DataFrame) -> Result<GroupedScatterPlot> {
    let distances = df.column("distance")?.f64()?;
    let durations = df.column("duration_seconds")?.f64()?;
    let rideable_types = df.column("rideable_type")?.str()?;

    let mut classic_points = Vec::new();
    let mut electric_points = Vec::new();

    for ((distance, duration), rideable_type) in distances
        .into_no_null_iter()
        .zip(durations.into_no_null_iter())
        .zip(rideable_types.into_no_null_iter())
    {
        let point = (distance, duration);
        match rideable_type {
            "classic_bike" => classic_points.push(point),
            "electric_bike" => electric_points.push(point),
            _ => {}
        }
    }

    Ok(GroupedScatterPlot {
        classic_points,
        electric_points,
    })
}

pub fn line_from_df(df: &DataFrame) -> Result<ScatterPlot> {
    let points: Vec<(f64, f64)> = df
        .column("unix_s")?
        .f64()?
        .into_no_null_iter()
        .zip(
            df.column("num_rides")?
                .u32()?
                .into_no_null_iter()
                .map(|f| f as f64),
        )
        .collect();

    Ok(ScatterPlot {
        points,
        color_by: None,
    })
}
