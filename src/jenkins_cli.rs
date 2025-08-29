use clap::{Arg, Command};
use reqwest::blocking::Client;
use serde_json::{Map, Value};
use std::collections::HashMap;
use std::time::Duration;
use anyhow::{Result, anyhow};
use base64::Engine;

const JENKINS_URL: &str = "http://your-jenkins-server:8080";
const API_TOKEN: &str = "your-api-token-here";
const USERNAME: &str = "your-username";
const JOB_NAME: &str = "jenkins-demo";

struct JenkinsClient {
    base_url: String,
    username: String,
    token: String,
    client: Client,
}

impl JenkinsClient {
    fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        JenkinsClient {
            base_url: JENKINS_URL.to_string(),
            username: USERNAME.to_string(),
            token: API_TOKEN.to_string(),
            client,
        }
    }

    fn get_auth_header(&self) -> String {
        let credentials = format!("{}:{}", self.username, self.token);
        let encoded = base64::engine::general_purpose::STANDARD.encode(credentials.as_bytes());
        format!("Basic {}", encoded)
    }

    fn trigger_job(&self, job_name: &str, parameters: &HashMap<String, String>) -> Result<()> {
        let url = if parameters.is_empty() {
            format!("{}/job/{}/build", self.base_url, job_name)
        } else {
            format!("{}/job/{}/buildWithParameters", self.base_url, job_name)
        };

        let mut request = self.client
            .post(&url)
            .header("Authorization", self.get_auth_header())
            .header("Content-Type", "application/json");

        if !parameters.is_empty() {
            let params: Map<String, Value> = parameters
                .iter()
                .map(|(k, v)| (k.clone(), Value::String(v.clone())))
                .collect();
            request = request.json(&params);
        }

        let response = request
            .send()
            .map_err(|_| anyhow!("connection error"))?;

        if response.status().is_success() {
            println!("✅ Job '{}' triggered successfully", job_name);
            
            if let Some(location) = response.headers().get("Location") {
                if let Ok(location_str) = location.to_str() {
                    println!("📍 Queue URL: {}", location_str);
                }
            }
            Ok(())
        } else {
            let status = response.status();
            let body = response.text().unwrap_or_else(|_| "Unknown error".to_string());
            Err(anyhow!("jenkins API returned status {}: {}", status, body))
        }
    }

    fn get_job_status(&self, job_name: &str) -> Result<()> {
        let url = format!("{}/job/{}/api/json", self.base_url, job_name);

        let response = self.client
            .get(&url)
            .header("Authorization", self.get_auth_header())
            .send()
            .map_err(|_| anyhow!("connection error"))?;

        if response.status().is_success() {
            let job_info: Value = response
                .json()
                .map_err(|_| anyhow!("failed to decode response"))?;

            println!("📊 Job Status for '{}':", job_name);
            
            if let Some(name) = job_info.get("name") {
                println!("   Name: {}", name);
            }
            
            if let Some(buildable) = job_info.get("buildable") {
                println!("   Buildable: {}", buildable);
            }
            
            if let Some(last_build) = job_info.get("lastBuild") {
                if let Some(number) = last_build.get("number") {
                    println!("   Last Build: #{}", number);
                }
                if let Some(url) = last_build.get("url") {
                    println!("   Last Build URL: {}", url);
                }
            }

            Ok(())
        } else {
            Err(anyhow!("jenkins API returned status {}", response.status()))
        }
    }
}

fn print_help() {
    println!("Jenkins CLI Tool");
    println!("Usage:");
    println!("  jenkins-cli job [job-name]         - Trigger a Jenkins job");
    println!("  jenkins-cli status [job-name]      - Get job status");
    println!("  jenkins-cli help                   - Show this help");
    println!();
    println!("Default job: {}", JOB_NAME);
}

fn main() -> Result<()> {
    let matches = Command::new("jenkins-cli")
        .version("1.0.0")
        .about("Jenkins CLI Tool")
        .subcommand(
            Command::new("job")
                .about("Trigger a Jenkins job")
                .arg(
                    Arg::new("job-name")
                        .help("Name of the job to trigger")
                        .value_name("JOB_NAME")
                        .index(1)
                )
        )
        .subcommand(
            Command::new("status")
                .about("Get job status")
                .arg(
                    Arg::new("job-name")
                        .help("Name of the job to check")
                        .value_name("JOB_NAME")
                        .index(1)
                )
        )
        .subcommand(Command::new("help").about("Show help information"))
        .get_matches();

    let client = JenkinsClient::new();

    match matches.subcommand() {
        Some(("job", sub_matches)) => {
            let job_name = sub_matches
                .get_one::<String>("job-name")
                .map(|s| s.as_str())
                .unwrap_or(JOB_NAME);

            println!("🚀 Triggering Jenkins job: {}", job_name);

            // 添加参数
            let mut parameters = HashMap::new();
            parameters.insert("BRANCH_NAME".to_string(), "master".to_string());
            parameters.insert("BUILD_TYPE".to_string(), "release".to_string());

            if let Err(e) = client.trigger_job(job_name, &parameters) {
                eprintln!("❌ Error: {}", e);
                std::process::exit(1);
            }
        }
        
        Some(("status", sub_matches)) => {
            let job_name = sub_matches
                .get_one::<String>("job-name")
                .map(|s| s.as_str())
                .unwrap_or(JOB_NAME);

            if let Err(e) = client.get_job_status(job_name) {
                eprintln!("❌ Error: {}", e);
                std::process::exit(1);
            }
        }
        
        Some(("help", _)) => {
            print_help();
        }
        
        _ => {
            print_help();
            std::process::exit(1);
        }
    }

    Ok(())
}
