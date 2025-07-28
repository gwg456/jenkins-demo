package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type AppInfo struct {
	Message   string `json:"message"`
	Branch    string `json:"branch"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version"`
}

func main() {
	port := getEnvWithDefault("PORT", "8080")
	
	// 设置路由
	http.HandleFunc("/", handleRoot)
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/api/info", handleInfo)
	
	log.Printf("服务器启动在端口 %s", port)
	log.Printf("分支: %s", os.Getenv("branch"))
	
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal("服务器启动失败:", err)
	}
}

func handleRoot(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello, 2024 Kubernetes！I'm from Jenkins CI！\n分支: %s\n", os.Getenv("branch"))
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

func handleInfo(w http.ResponseWriter, r *http.Request) {
	info := AppInfo{
		Message:   "Hello from Jenkins Demo App",
		Branch:    getEnvWithDefault("branch", "unknown"),
		Timestamp: time.Now().Format(time.RFC3339),
		Version:   getEnvWithDefault("VERSION", "1.0.0"),
	}
	
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(info); err != nil {
		http.Error(w, "编码JSON失败", http.StatusInternalServerError)
		return
	}
}

func getEnvWithDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
