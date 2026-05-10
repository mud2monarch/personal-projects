use anyhow::Result;
use time::OffsetDateTime;
use time::format_description::well_known::Rfc3339;

pub fn run_id() -> String {
    std::env::var("RUN_ID").unwrap_or_else(|_| "adhoc".to_string())
}

pub fn utc_timestamp() -> Result<String> {
    Ok(OffsetDateTime::now_utc().format(&Rfc3339)?)
}
