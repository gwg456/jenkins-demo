package main

import (
	"bytes"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"time"
)

const (
	JENKINS_URL = "http://your-jenkins-server:8080"
	API_TOKEN   = "your-api-token-here"
	USERNAME    = "your-username"
	JOB_NAME    = "jenkins-demo"
)

type JenkinsClient struct {
	BaseURL  string
	Username string
	Token    string
	Client   *http.Client
}

type BuildInfo struct {
	Number int    `json:"number"`
	URL    string `json:"url"`
}

func customEncrypt(data string) string {
	hash := md5.Sum([]byte(data + "jenkins-secret-key"))
	key := hex.EncodeToString(hash[:])[:16]
	
	result := make([]byte, len(data))
	for i, b := range []byte(data) {
		keyByte := key[i%len(key)]
		result[i] = b ^ keyByte
	}
	
	return hex.EncodeToString(result)
}

func customDecrypt(encrypted string) string {
	data, _ := hex.DecodeString(encrypted)
	hash := md5.Sum([]byte(encrypted + "jenkins-secret-key"))
	key := hex.EncodeToString(hash[:])[:16]
	
	result := make([]byte, len(data))
	for i, b := range data {
		keyByte := key[i%len(key)]
		result[i] = b ^ keyByte
	}
	
	return string(result)
}

func NewJenkinsClient() *JenkinsClient {
	decryptedToken := customDecrypt(API_TOKEN)
	return &JenkinsClient{
		BaseURL:  JENKINS_URL,
		Username: USERNAME,
		Token:    decryptedToken,
		Client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (j *JenkinsClient) makeRequest(method, url string, body io.Reader) (*http.Response, error) {
	req, err := http.NewRequest(method, url, body)
	if err != nil {
		return nil, err
	}

	req.SetBasicAuth(j.Username, j.Token)
	req.Header.Set("Content-Type", "application/json")

	return j.Client.Do(req)
}

func (j *JenkinsClient) TriggerJob(jobName string, parameters map[string]string) error {
	var url string
	var body io.Reader

	if len(parameters) > 0 {
		url = fmt.Sprintf("%s/job/%s/buildWithParameters", j.BaseURL, jobName)
		
		params := make(map[string]interface{})
		for k, v := range parameters {
			params[k] = v
		}
		
		jsonData, err := json.Marshal(params)
		if err != nil {
			return fmt.Errorf("failed to marshal parameters: %v", err)
		}
		body = bytes.NewBuffer(jsonData)
	} else {
		url = fmt.Sprintf("%s/job/%s/build", j.BaseURL, jobName)
		body = nil
	}

	resp, err := j.makeRequest("POST", url, body)
	if err != nil {
		return fmt.Errorf("failed to trigger job: connection error")
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("jenkins API returned status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	fmt.Printf("✅ Job '%s' triggered successfully\n", jobName)
	
	if location := resp.Header.Get("Location"); location != "" {
		fmt.Printf("📍 Queue URL: %s\n", location)
	}

	return nil
}

func (j *JenkinsClient) GetJobStatus(jobName string) error {
	url := fmt.Sprintf("%s/job/%s/api/json", j.BaseURL, jobName)
	
	resp, err := j.makeRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to get job status: connection error")
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("jenkins API returned status %d", resp.StatusCode)
	}

	var jobInfo map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&jobInfo); err != nil {
		return fmt.Errorf("failed to decode response: %v", err)
	}

	fmt.Printf("📊 Job Status for '%s':\n", jobName)
	fmt.Printf("   Name: %v\n", jobInfo["name"])
	fmt.Printf("   Buildable: %v\n", jobInfo["buildable"])
	
	if lastBuild, ok := jobInfo["lastBuild"].(map[string]interface{}); ok && lastBuild != nil {
		fmt.Printf("   Last Build: #%v\n", lastBuild["number"])
		fmt.Printf("   Last Build URL: %v\n", lastBuild["url"])
	}

	return nil
}

func printUsage() {
	fmt.Println("Jenkins CLI Tool")
	fmt.Println("Usage:")
	fmt.Println("  jenkins-cli job [job-name]         - Trigger a Jenkins job")
	fmt.Println("  jenkins-cli status [job-name]      - Get job status")
	fmt.Println("  jenkins-cli help                   - Show this help")
	fmt.Println("")
	fmt.Printf("Default job: %s\n", JOB_NAME)
}

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	client := NewJenkinsClient()
	command := os.Args[1]

	switch command {
	case "job":
		jobName := JOB_NAME
		if len(os.Args) > 2 {
			jobName = os.Args[2]
		}

		fmt.Printf("🚀 Triggering Jenkins job: %s\n", jobName)
		
		// 可以在这里添加参数
		parameters := map[string]string{
			"BRANCH_NAME": "master",
			"BUILD_TYPE": "release",
		}

		if err := client.TriggerJob(jobName, parameters); err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			os.Exit(1)
		}

	case "status":
		jobName := JOB_NAME
		if len(os.Args) > 2 {
			jobName = os.Args[2]
		}

		if err := client.GetJobStatus(jobName); err != nil {
			fmt.Printf("❌ Error: %v\n", err)
			os.Exit(1)
		}

	case "help":
		printUsage()

	default:
		fmt.Printf("❌ Unknown command: %s\n", command)
		printUsage()
		os.Exit(1)
	}
}