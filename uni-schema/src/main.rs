use clap::Parser;
use log::{debug, error, info, trace, warn};
use reqwest::{Client, Response};
use serde::Deserialize;
use std::fs::File;
use std::io::Write;
use tokio::*;
use yup_oauth2::*;

// Defining serde structs for GET(dataset.list) response.
#[derive(Debug, Deserialize)]
struct DatasetList {
    datasets: Vec<Dataset>,
}

#[derive(Debug, Deserialize)]
struct Dataset {
    datasetReference: DatasetReference,
}

#[derive(Debug, Deserialize)]
struct DatasetReference {
    projectId: String,
    datasetId: String,
}

// Defining serde structs for GET(tables.list) response.
#[derive(Debug, Deserialize)]
struct TableList {
    tables: Vec<Table>,
}

#[derive(Debug, Deserialize)]
struct Table {
    tableReference: TableReference,
    #[serde(skip)]
    schema: Option<Vec<Column>>,
}

#[derive(Debug, Deserialize)]
struct TableReference {
    // In future, consider pulling partition parameter as well.
    projectId: String,
    datasetId: String,
    tableId: String,
}

// Defining serde structs for GET(tables.get) response.
#[derive(Debug, Deserialize)]
struct TableGet {
    schema: Schema,
}

#[derive(Debug, Deserialize)]
struct Schema {
    fields: Vec<Column>,
}

#[derive(Debug, Deserialize)]
struct Column {
    name: String,
    #[serde(rename = "type")]
    field_type: String,
    mode: Option<String>,
    fields: Option<Vec<Column>>,
}

/// BigQuery Table Schema Collector
///
/// Collects table schemas from BigQuery and writes them to a file.
#[derive(Parser, Debug)]
struct Args {
    /// The list of tables to write to the output file.
    /// Enter table names in the format of "project.dataset.table".
    /// Enter multiple tables by separating them with commas.
    /// If you don't want to specify a list of tables, you need to provide a list of projects.
    #[arg(short, long, value_delimiter = ',')]
    tables: Option<Vec<String>>,

    /// If you don't want to specify a list of tables, you need to provide a list of projects.
    /// Enter project IDs separated by commas, no space.
    #[arg(short, long, value_delimiter = ',')]
    projects: Option<Vec<String>>,

    /// The filepath to which to write the final output file.
    /// Defaults to "llms.txt" in the current working directory.
    #[arg(short, long, default_value = "llms.txt")]
    output_file: String,

    /// The filepath to the service account credentials file.
    /// Defaults to "service_account_creds.json" in the current working directory.
    #[arg(short, long, default_value = "service_account_creds.json")]
    creds_path: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    env_logger::init();
    info!("Starting application");

    let args = Args::parse();
    let creds_path = args.creds_path.as_str();
    let output_file_path: &str = args.output_file.as_str();
    let desired_tables: Vec<String> = args.tables.unwrap_or(Vec::new());
    let mut desired_projects: Vec<String> = args.projects.unwrap_or(Vec::new());

    // Split the desired tables into desired projects
    if !desired_tables.is_empty() {
        desired_projects = desired_tables
            .iter()
            .map(|t| t.split(".").next().unwrap_or("").to_string())
            .collect();
        desired_projects.sort();
        desired_projects.dedup();
        info!(
            "Got desired projects from list of tables. Desired projects: {:?}",
            desired_projects
        );
    } else if !desired_projects.is_empty() {
        info!(
            "Got desired projects from list of projects. Desired projects: {:?}",
            desired_projects
        );
    } else {
        error!("No desired projects or tables provided. You must provide a list of projects or tables.");
        return Err("No desired projects or tables provided. You must provide a list of projects or tables.".into());
    }

    let service_account_key: yup_oauth2::ServiceAccountKey =
        read_service_account_key(creds_path)
            .await
            .expect("Failed to read service account key. Please check the path to the service account key file.");
    let authenticator = yup_oauth2::ServiceAccountAuthenticator::builder(service_account_key)
        .build()
        .await
        .expect("failed to create authenticator");
    info!("Authenticator for yup-oauth2 created successfully");

    let token = authenticator
        .token(&["https://www.googleapis.com/auth/bigquery.readonly"])
        .await
        .expect("Failed to get access token");
    info!(
        "Successfully got access token: {}",
        token.token().unwrap().chars().take(4).collect::<String>()
    );

    let mut headers: reqwest::header::HeaderMap = reqwest::header::HeaderMap::new();
    headers.insert(
        reqwest::header::AUTHORIZATION,
        format!("Bearer {}", token.token().unwrap())
            .parse()
            .unwrap(),
    );

    let client = reqwest::Client::builder()
        .default_headers(headers)
        .build()
        .expect("Failed to build reqwest client");

    // Start collecting all datasets.
    let mut all_datasets: Vec<Dataset> = Vec::new();

    for project in desired_projects {
        let url =
            format!("https://bigquery.googleapis.com/bigquery/v2/projects/{project}/datasets");
        info!("GET-ting datasets for project: {}", project);

        match client.get(&url).send().await {
            Err(e) => {
                error!("Failed to GET {} -- {}", url, e);
            }
            Ok(response) => {
                if response.status().is_success() {
                    match response.json::<DatasetList>().await {
                        Err(e) => {
                            error!("Failed to parse JSON for {} -- {}", url, e);
                        }
                        Ok(list) => {
                            info!(
                                "Successfully added {:?} datasets for {}",
                                list.datasets, project
                            );
                            all_datasets.extend(list.datasets);
                        }
                    }
                } else {
                    warn!("Non-200 response from {} -- {}", url, response.status());
                }
            }
        }
    }

    // start collecting all tables
    let mut all_tables: Vec<Table> = Vec::new();

    if desired_tables.is_empty() {
        for dataset in all_datasets {
            let url = format!(
                "https://bigquery.googleapis.com/bigquery/v2/projects/{}/datasets/{}/tables",
                dataset.datasetReference.projectId, dataset.datasetReference.datasetId
            );
            info!("GET-ting tables for dataset {}", url);

            match client.get(&url).send().await {
                Err(e) => {
                    error!("Failed to GET {} with error {}", url, e);
                }

                Ok(response) => {
                    if response.status().is_success() {
                        match response.json::<TableList>().await {
                            Err(e) => {
                                error!("Failed to parse JSON for {} -- {}", url, e);
                            }
                            Ok(list) => {
                                info!(
                                    "Successfully added {:?} tables for {}",
                                    list.tables, dataset.datasetReference.datasetId
                                );
                                all_tables.extend(list.tables);
                            }
                        }
                    }
                }
            }
        }
    } else {
        for table in desired_tables {
            let table_parts: Vec<String> = table.split(".").map(String::from).collect();

            if table_parts.len() == 3 {
                let table_ref = TableReference {
                    projectId: table_parts[0].to_string(),
                    datasetId: table_parts[1].to_string(),
                    tableId: table_parts[2].to_string(),
                };
                let temp_table = Table {
                    tableReference: table_ref,
                    schema: None,
                };
                all_tables.push(temp_table);
                info!(
                    "Successfully added table: {}.{}.{}",
                    table_parts[0], table_parts[1], table_parts[2]
                );
                continue;
            } else {
                error!(
                    "Skipping invalid \"table\" value: {}. Expected format: project.dataset.table.",
                    table
                );
                continue;
            }
        }
    }

    // start collecting all schemas
    // 9/28 don't think this needs to be mutably borrowed?
    for table in &mut all_tables {
        let url: String = format!(
            "https://bigquery.googleapis.com/bigquery/v2/projects/{}/datasets/{}/tables/{}",
            table.tableReference.projectId,
            table.tableReference.datasetId,
            table.tableReference.tableId
        );
        info!(
            "GET-ting schema for {}.{}.{}",
            table.tableReference.projectId,
            table.tableReference.datasetId,
            table.tableReference.tableId
        );

        match client.get(&url).send().await {
            Err(e) => {
                error!("Failed to GET {} with error {}.", url, e);
            }
            Ok(response) => {
                if response.status().is_success() {
                    match response.json::<TableGet>().await {
                        Err(e) => {
                            error!("Failed to parse JSON for {} -- {}.", url, e);
                        }
                        Ok(table_get) => {
                            let columns: Vec<Column> = table_get.schema.fields;
                            table.schema = Some(columns);
                        }
                    }
                } else {
                    warn!(
                        "Failed to get schema for {}.{}.{} - Status: {}",
                        table.tableReference.projectId,
                        table.tableReference.datasetId,
                        table.tableReference.tableId,
                        response.status()
                    );
                }
            }
        }
    }

    // Write all schemas to a file.

    // Helper function to write columns with proper indentation to a file.
    fn write_column(file: &mut File, column: &Column, indent: usize) -> std::io::Result<()> {
        let indent_str = " ".repeat(indent);
        writeln!(
            file,
            "{}|- {} ({}) [{}]",
            indent_str,
            column.name,
            column.field_type,
            column.mode.as_deref().unwrap_or("REQUIRED")
        )?;

        // If this is a RECORD type, print its nested fields
        if let Some(fields) = &column.fields {
            for field in fields {
                write_column(file, field, indent + 2)?; // Increase indentation for nested fields
            }
        }

        Ok(())
    }

    let mut output_file = File::create(output_file_path).expect("Failed to create output file");
    let mut tables_written: Vec<&Table> = Vec::new();

    for table in &all_tables {
        writeln!(
            output_file,
            "\n=== Table: {}.{}.{} ===",
            table.tableReference.projectId,
            table.tableReference.datasetId,
            table.tableReference.tableId
        )?;

        if let Some(columns) = &table.schema {
            for column in columns {
                write_column(&mut output_file, column, 0)?; // Start with 0 indentation
            }
        } else {
            writeln!(output_file, "No schema available")?;
        }

        info!(
            "Finished writing table: {}.{}.{}",
            table.tableReference.projectId,
            table.tableReference.datasetId,
            table.tableReference.tableId
        );
        tables_written.push(table);
    }

    info!("Finished writing {} tables.", tables_written.len());
    info!(
        "Wrote tables: {:?}",
        tables_written
            .iter()
            .map(|t| format!(
                "{}.{}.{}",
                t.tableReference.projectId, t.tableReference.datasetId, t.tableReference.tableId
            ))
            .collect::<Vec<_>>()
    );

    Ok(())
}
