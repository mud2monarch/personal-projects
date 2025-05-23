# BigQuery Schema Collector

A command-line tool to fetch and document BigQuery table schemas. This tool can collect schema information for all tables in specified projects or for specific tables.

View a [video demo here](https://youtu.be/ytdzjhRwQzY).

## Prerequisites

- You must run this executable from the command line because you need to provide a list of projects (`--projects`) or tables (`--tables`).
- You need a Google Cloud service account credentials file with BigQuery read access. The default name is `service_account_creds.json`, in the current working directory.
- The service account must have access to the BigQuery projects you want to query.

## Installation

### With executable

1. Download the executable.
2. Place your service account credentials JSON file in the same working directory as the executable (default name: `service_account_creds.json`)
3. Run the executable from the command line (see Usage section below).

### With source code

1. Clone the repository.
2. Place your service account credentials JSON file in the project directory (default name: `service_account_creds.json`)
3. Build the project:
```bash
cargo build --release
```
4. Run the executable from the command line (see Usage section below).
## Usage

### With executable
```bash
# free the executable from quarantine
xattr -d com.apple.quarantine ./uni-schema
# make the file executable
chmod +x ./uni-schema

# Collect schemas for specified tables.
./uni-schema --tables project.dataset.table1,project.dataset.table2

# Specify custom output file.
./uni-schema --tables project.dataset.table1,project.dataset.table2 --output-file my_schemas.txt

# Specify custom credentials file location.
./uni-schema --tables project.dataset.table1,project.dataset.table2 --creds-path /path/to/credentials.json

# Collect schemas for all tables in specified projects. If you provide tables, it will only collect schemas for the specified tables.
./uni-schema --projects project1,project2

# On Windows, add .exe suffix.
uni-schema.exe --tables project.dataset.table1,project.dataset.table2
```

### With source code
```bash
# Collect schemas for all tables in default projects
RUST_LOG=info cargo run

# Collect schemas for specific tables
RUST_LOG=info cargo run -- --tables project.dataset.table1,project.dataset.table2

# Specify custom output file
RUST_LOG=info cargo run -- --output-file my_schemas.txt

# Specify custom credentials file location
RUST_LOG=info cargo run -- --creds-path /path/to/credentials.json
```

### Sample on public datasets
```bash
# Export schemas for Google's public ETH Mainnet datsets using executable
# See https://console.cloud.google.com/marketplace/product/bigquery-public-data/blockchain-analytics-ethereum-mainnet-us.
RUST_LOG=info ./uni-schema \
  --creds-path /Users/your.name/Downloads/service_account_creds_zach_hackathon.json \
  --tables bigquery-public-data.goog_blockchain_ethereum_mainnet_us.transactions,bigquery-public-data.goog_blockchain_ethereum_mainnet_us.logs,bigquery-public-data.goog_blockchain_ethereum_mainnet_us.blocks \
  --output-file gbq-public-llms.txt
```

### Command Line Arguments

- `--tables` (`-t`): Optional but recommended. Comma-separated list of tables in `project.dataset.table` format. Do not separate with spaces.
- `--projects` (`-p`): Optional. Comma-separated list of project IDs. Do not separate with spaces. If you provide tables, it will only collect schemas for the specified tables.
- `--output-file` (`-o`): Optional. Output file path (default: `llms.txt`)
- `--creds-path` (`-c`): Optional. Path to service account credentials JSON file (default: `service_account_creds.json`)

### Output Format

The tool generates a text file with schema information in the following format:

```
=== Table: project.dataset.table ===
|- column_name (TYPE) [MODE]
  |- nested_field (TYPE) [MODE]  # For RECORD types
```

### Logging

Set the `RUST_LOG` environment variable to control log output:
- `RUST_LOG=info`: Standard logging (recommended)
- `RUST_LOG=debug`: Verbose logging
- `RUST_LOG=error`: Error-only logging
