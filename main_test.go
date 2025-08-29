package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"
)

func TestHandleRoot(t *testing.T) {
	// 设置测试环境变量
	os.Setenv("branch", "test-branch")
	defer os.Unsetenv("branch")

	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleRoot)
	handler.ServeHTTP(rr, req)

	// 检查状态码
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// 检查响应内容包含分支信息
	expected := "test-branch"
	if !contains(rr.Body.String(), expected) {
		t.Errorf("handler returned unexpected body: got %v want to contain %v",
			rr.Body.String(), expected)
	}
}

func TestHandleHealth(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleHealth)
	handler.ServeHTTP(rr, req)

	// 检查状态码
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// 检查响应体
	expected := "OK"
	if rr.Body.String() != expected {
		t.Errorf("handler returned unexpected body: got %v want %v",
			rr.Body.String(), expected)
	}
}

func TestHandleInfo(t *testing.T) {
	// 设置测试环境变量
	os.Setenv("branch", "test-branch")
	os.Setenv("VERSION", "2.0.0")
	defer func() {
		os.Unsetenv("branch")
		os.Unsetenv("VERSION")
	}()

	req, err := http.NewRequest("GET", "/api/info", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleInfo)
	handler.ServeHTTP(rr, req)

	// 检查状态码
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// 检查响应头
	expectedContentType := "application/json"
	if contentType := rr.Header().Get("Content-Type"); contentType != expectedContentType {
		t.Errorf("handler returned wrong content type: got %v want %v",
			contentType, expectedContentType)
	}

	// 解析JSON响应
	var info AppInfo
	err = json.Unmarshal(rr.Body.Bytes(), &info)
	if err != nil {
		t.Fatalf("Could not parse JSON response: %v", err)
	}

	// 验证字段
	if info.Branch != "test-branch" {
		t.Errorf("Expected branch 'test-branch', got '%v'", info.Branch)
	}

	if info.Version != "2.0.0" {
		t.Errorf("Expected version '2.0.0', got '%v'", info.Version)
	}

	if info.Message != "Hello from Jenkins Demo App" {
		t.Errorf("Expected message 'Hello from Jenkins Demo App', got '%v'", info.Message)
	}

	// 验证时间戳格式
	_, err = time.Parse(time.RFC3339, info.Timestamp)
	if err != nil {
		t.Errorf("Timestamp is not in RFC3339 format: %v", err)
	}
}

func TestHandleMetrics(t *testing.T) {
	// 设置测试环境变量
	os.Setenv("branch", "test-branch")
	os.Setenv("VERSION", "2.0.0")
	defer func() {
		os.Unsetenv("branch")
		os.Unsetenv("VERSION")
	}()

	req, err := http.NewRequest("GET", "/metrics", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleMetrics)
	handler.ServeHTTP(rr, req)

	// 检查状态码
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// 检查响应头
	expectedContentType := "text/plain; version=0.0.4; charset=utf-8"
	if contentType := rr.Header().Get("Content-Type"); contentType != expectedContentType {
		t.Errorf("handler returned wrong content type: got %v want %v",
			contentType, expectedContentType)
	}

	responseBody := rr.Body.String()
	
	// 验证Prometheus格式的指标
	expectedMetrics := []string{
		"jenkins_demo_info",
		"jenkins_demo_uptime_seconds",
		"jenkins_demo_requests_total",
		"test-branch",
		"2.0.0",
	}

	for _, metric := range expectedMetrics {
		if !strings.Contains(responseBody, metric) {
			t.Errorf("Metrics response should contain '%s', got: %v", metric, responseBody)
		}
	}
}

func TestGetEnvWithDefault(t *testing.T) {
	testCases := []struct {
		key          string
		defaultValue string
		envValue     string
		expected     string
	}{
		{"TEST_KEY", "default", "", "default"},
		{"TEST_KEY", "default", "custom", "custom"},
		{"NONEXISTENT_KEY", "fallback", "", "fallback"},
	}

	for _, tc := range testCases {
		// 清理环境变量
		os.Unsetenv(tc.key)
		
		// 如果有环境变量值，设置它
		if tc.envValue != "" {
			os.Setenv(tc.key, tc.envValue)
			defer os.Unsetenv(tc.key)
		}

		result := getEnvWithDefault(tc.key, tc.defaultValue)
		if result != tc.expected {
			t.Errorf("getEnvWithDefault(%q, %q) = %q; want %q",
				tc.key, tc.defaultValue, result, tc.expected)
		}
	}
}

func TestHandleInfoWithDefaults(t *testing.T) {
	// 清理所有相关环境变量
	os.Unsetenv("branch")
	os.Unsetenv("VERSION")

	req, err := http.NewRequest("GET", "/api/info", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(handleInfo)
	handler.ServeHTTP(rr, req)

	// 解析JSON响应
	var info AppInfo
	err = json.Unmarshal(rr.Body.Bytes(), &info)
	if err != nil {
		t.Fatalf("Could not parse JSON response: %v", err)
	}

	// 验证默认值
	if info.Branch != "unknown" {
		t.Errorf("Expected default branch 'unknown', got '%v'", info.Branch)
	}

	if info.Version != "1.0.0" {
		t.Errorf("Expected default version '1.0.0', got '%v'", info.Version)
	}
}

func TestAppInfoJSONMarshaling(t *testing.T) {
	info := AppInfo{
		Message:   "Test message",
		Branch:    "test-branch",
		Timestamp: "2024-01-01T00:00:00Z",
		Version:   "1.0.0",
	}

	data, err := json.Marshal(info)
	if err != nil {
		t.Fatalf("Could not marshal AppInfo: %v", err)
	}

	var unmarshaled AppInfo
	err = json.Unmarshal(data, &unmarshaled)
	if err != nil {
		t.Fatalf("Could not unmarshal AppInfo: %v", err)
	}

	// 验证所有字段
	if unmarshaled != info {
		t.Errorf("Marshaling/Unmarshaling changed data: got %+v, want %+v", unmarshaled, info)
	}
}

// 辅助函数
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 || s[0:len(substr)] == substr || s[len(s)-len(substr):] == substr || containsMiddle(s, substr))
}

func containsMiddle(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// 基准测试
func BenchmarkHandleHealth(b *testing.B) {
	req, _ := http.NewRequest("GET", "/health", nil)
	
	for i := 0; i < b.N; i++ {
		rr := httptest.NewRecorder()
		handler := http.HandlerFunc(handleHealth)
		handler.ServeHTTP(rr, req)
	}
}

func BenchmarkHandleInfo(b *testing.B) {
	req, _ := http.NewRequest("GET", "/api/info", nil)
	
	for i := 0; i < b.N; i++ {
		rr := httptest.NewRecorder()
		handler := http.HandlerFunc(handleInfo)
		handler.ServeHTTP(rr, req)
	}
}

func BenchmarkHandleMetrics(b *testing.B) {
	req, _ := http.NewRequest("GET", "/metrics", nil)
	
	for i := 0; i < b.N; i++ {
		rr := httptest.NewRecorder()
		handler := http.HandlerFunc(handleMetrics)
		handler.ServeHTTP(rr, req)
	}
} 