use actix_web::{web, HttpRequest, HttpResponse, Result};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::env;

#[derive(Serialize, Deserialize, Debug, PartialEq)]
pub struct AppInfo {
    pub message: String,
    pub branch: String,
    pub timestamp: DateTime<Utc>,
    pub version: String,
}

#[derive(Serialize, Deserialize)]
pub struct MetricsInfo {
    pub uptime_seconds: u64,
    pub requests_total: u64,
    pub version: String,
    pub branch: String,
}

pub async fn handle_root(_req: HttpRequest) -> Result<HttpResponse> {
    let branch = get_env_with_default("branch", "unknown");
    let response = format!(
        "Hello, 2024 Kubernetes！I'm from Jenkins CI！\n分支: {}\n", 
        branch
    );
    Ok(HttpResponse::Ok()
        .content_type("text/plain; charset=utf-8")
        .body(response))
}

pub async fn handle_health(_req: HttpRequest) -> Result<HttpResponse> {
    Ok(HttpResponse::Ok()
        .content_type("text/plain")
        .body("OK"))
}

pub async fn handle_info(_req: HttpRequest) -> Result<HttpResponse> {
    let info = AppInfo {
        message: "Hello from Jenkins Demo App".to_string(),
        branch: get_env_with_default("branch", "unknown"),
        timestamp: Utc::now(),
        version: get_env_with_default("VERSION", "1.0.0"),
    };
    
    Ok(HttpResponse::Ok()
        .content_type("application/json")
        .json(info))
}

pub async fn handle_metrics(_req: HttpRequest) -> Result<HttpResponse> {
    let metrics_text = format!(
        "# HELP jenkins_demo_info Application information\n\
         # TYPE jenkins_demo_info gauge\n\
         jenkins_demo_info{{version=\"{}\",branch=\"{}\"}} 1\n\
         # HELP jenkins_demo_uptime_seconds Uptime in seconds\n\
         # TYPE jenkins_demo_uptime_seconds counter\n\
         jenkins_demo_uptime_seconds {}\n\
         # HELP jenkins_demo_requests_total Total number of requests\n\
         # TYPE jenkins_demo_requests_total counter\n\
         jenkins_demo_requests_total 0\n",
        get_env_with_default("VERSION", "1.0.0"),
        get_env_with_default("branch", "unknown"),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    );
    
    Ok(HttpResponse::Ok()
        .content_type("text/plain; version=0.0.4; charset=utf-8")
        .body(metrics_text))
}

pub fn get_env_with_default(key: &str, default_value: &str) -> String {
    env::var(key).unwrap_or_else(|_| default_value.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use actix_web::{test, App};
    use std::env;

    #[actix_web::test]
    async fn test_handle_root() {
        env::set_var("branch", "test-branch");
        
        let req = test::TestRequest::get().uri("/").to_request();
        let resp = handle_root(req).await.unwrap();
        
        assert_eq!(resp.status(), 200);
        
        env::remove_var("branch");
    }

    #[actix_web::test]
    async fn test_handle_health() {
        let req = test::TestRequest::get().uri("/health").to_request();
        let resp = handle_health(req).await.unwrap();
        
        assert_eq!(resp.status(), 200);
    }

    #[actix_web::test]
    async fn test_handle_info() {
        env::set_var("branch", "test-branch");
        env::set_var("VERSION", "2.0.0");
        
        let req = test::TestRequest::get().uri("/api/info").to_request();
        let resp = handle_info(req).await.unwrap();
        
        assert_eq!(resp.status(), 200);
        
        env::remove_var("branch");
        env::remove_var("VERSION");
    }

    #[actix_web::test]
    async fn test_handle_metrics() {
        env::set_var("branch", "test-branch");
        env::set_var("VERSION", "2.0.0");
        
        let req = test::TestRequest::get().uri("/metrics").to_request();
        let resp = handle_metrics(req).await.unwrap();
        
        assert_eq!(resp.status(), 200);
        assert!(resp.headers().get("content-type").unwrap().to_str().unwrap().contains("text/plain"));
        
        env::remove_var("branch");
        env::remove_var("VERSION");
    }

    #[test]
    fn test_get_env_with_default() {
        // 测试默认值
        let result = get_env_with_default("NONEXISTENT_KEY", "default");
        assert_eq!(result, "default");
        
        // 测试环境变量值
        env::set_var("TEST_KEY", "custom");
        let result = get_env_with_default("TEST_KEY", "default");
        assert_eq!(result, "custom");
        env::remove_var("TEST_KEY");
    }

    #[test]
    fn test_app_info_serialization() {
        let info = AppInfo {
            message: "Test message".to_string(),
            branch: "test-branch".to_string(),
            timestamp: Utc::now(),
            version: "1.0.0".to_string(),
        };
        
        let json = serde_json::to_string(&info).unwrap();
        let deserialized: AppInfo = serde_json::from_str(&json).unwrap();
        
        assert_eq!(info, deserialized);
    }

    #[actix_web::test]
    async fn test_integration_endpoints() {
        let app = test::init_service(
            App::new()
                .route("/", web::get().to(handle_root))
                .route("/health", web::get().to(handle_health))
                .route("/api/info", web::get().to(handle_info))
                .route("/metrics", web::get().to(handle_metrics))
        ).await;

        // 测试根路径
        let req = test::TestRequest::get().uri("/").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());

        // 测试健康检查
        let req = test::TestRequest::get().uri("/health").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());

        // 测试API信息
        let req = test::TestRequest::get().uri("/api/info").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());

        // 测试监控指标
        let req = test::TestRequest::get().uri("/metrics").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());
    }
} 