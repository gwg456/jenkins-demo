use actix_web::{web, App, HttpServer, middleware::Logger};
use jenkins_demo::{handle_root, handle_health, handle_info, handle_metrics, get_env_with_default};
use std::env;
use log::info;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();
    
    let port = get_env_with_default("PORT", "8080");
    let bind_address = format!("0.0.0.0:{}", port);
    
    info!("服务器启动在端口 {}", port);
    info!("分支: {}", env::var("branch").unwrap_or_else(|_| "unknown".to_string()));
    
    HttpServer::new(|| {
        App::new()
            .wrap(Logger::default())
            .route("/", web::get().to(handle_root))
            .route("/health", web::get().to(handle_health))
            .route("/api/info", web::get().to(handle_info))
            .route("/metrics", web::get().to(handle_metrics))
    })
    .bind(&bind_address)?
    .run()
    .await
} 