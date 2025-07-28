pipeline {
    agent {
        label 'master'
    }
    
    environment {
        DOCKER_REGISTRY = 'registry-vpc.cn-beijing.aliyuncs.com'
        IMAGE_NAME = 'moseeker/jenkins-demo'
        DOCKER_BUILDKIT = '1'
    }
    
    stages {
        stage('Prepare') {
            steps {
                echo "🚀 1.准备阶段 - 检出代码"
                checkout scm
                script {
                    // 使用Git命令获取提交信息
                    env.BUILD_TAG = sh(
                        returnStdout: true, 
                        script: 'git rev-parse --short HEAD'
                    ).trim()
                    
                    env.BUILD_TIME = sh(
                        returnStdout: true,
                        script: 'date "+%Y%m%d-%H%M%S"'
                    ).trim()
                    
                    if (env.BRANCH_NAME != 'master') {
                        env.BUILD_TAG = "${env.BRANCH_NAME}-${env.BUILD_TAG}"
                    }
                    
                    echo "构建标签: ${env.BUILD_TAG}"
                    echo "分支名称: ${env.BRANCH_NAME}"
                }
            }
        }
        
        stage('Test') {
            steps {
                echo "🧪 2.功能测试阶段"
                script {
                    try {
                        // 基本功能测试
                        sh 'go run main.go &'
                        sh 'sleep 3'
                        sh 'curl -f http://localhost:8080/health || exit 1'
                        sh 'pkill -f "go run main.go" || true'
                        
                        echo "✅ 功能测试通过"
                    } catch (Exception e) {
                        echo "❌ 功能测试失败: ${e.message}"
                        throw e
                    }
                }
            }
        }
        
        stage('Build') {
            steps {
                echo "🏗️ 3.构建Docker镜像"
                script {
                    try {
                        // 构建Docker镜像
                        sh """
                            docker build \
                                --build-arg BUILD_TIME=${env.BUILD_TIME} \
                                --build-arg GIT_COMMIT=${env.BUILD_TAG} \
                                -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_TAG} \
                                -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest \
                                .
                        """
                        
                        echo "✅ 镜像构建成功: ${env.BUILD_TAG}"
                    } catch (Exception e) {
                        echo "❌ 镜像构建失败: ${e.message}"
                        throw e
                    }
                }
            }
        }
        
        stage('Push') {
            steps {
                echo "📤 4.推送Docker镜像"
                script {
                    // 使用Jenkins凭据管理
                    withCredentials([usernamePassword(
                        credentialsId: 'aliyun-docker-registry',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )]) {
                        sh '''
                            echo $DOCKER_PASSWORD | docker login $DOCKER_REGISTRY \
                                --username $DOCKER_USERNAME --password-stdin
                            
                            docker push $DOCKER_REGISTRY/$IMAGE_NAME:$BUILD_TAG
                            docker push $DOCKER_REGISTRY/$IMAGE_NAME:latest
                            
                            echo "✅ 镜像推送成功"
                        '''
                    }
                }
            }
            post {
                always {
                    // 清理本地镜像
                    sh "docker rmi ${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_TAG} || true"
                    sh "docker rmi ${DOCKER_REGISTRY}/${IMAGE_NAME}:latest || true"
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo "🚀 5.部署阶段"
                script {
                    if (env.BRANCH_NAME == 'master') {
                        // 生产环境部署需要人工确认
                        input message: "确认要部署到生产环境吗？", 
                              ok: "确认部署",
                              parameters: [
                                  choice(name: 'ENVIRONMENT', 
                                        choices: ['production', 'staging'], 
                                        description: '选择部署环境')
                              ]
                    }
                    
                    // 更新K8s配置文件
                    sh "sed -i 's/<BUILD_TAG>/${env.BUILD_TAG}/g' k8s.yaml"
                    sh "sed -i 's/<BRANCH_NAME>/${env.BRANCH_NAME}/g' k8s.yaml"
                    
                    // 部署到Kubernetes
                    sh "kubectl apply -f k8s.yaml --record"
                    
                    // 等待部署完成
                    sh "kubectl rollout status deployment jenkins-demo --timeout=300s"
                    
                    // 获取服务信息
                    sh "kubectl get pods -l app=jenkins-demo"
                    sh "kubectl get svc jenkins-demo-service"
                    
                    echo "✅ 部署成功完成"
                }
            }
        }
        
        stage('Post Deploy Tests') {
            steps {
                echo "🔍 部署后验证"
                script {
                    // 健康检查
                    sh '''
                        SERVICE_IP=$(kubectl get svc jenkins-demo-service -o jsonpath='{.spec.clusterIP}')
                        for i in {1..5}; do
                            if curl -f http://$SERVICE_IP/health; then
                                echo "✅ 健康检查通过"
                                break
                            else
                                echo "⏳ 等待服务就绪... ($i/5)"
                                sleep 10
                            fi
                        done
                    '''
                }
            }
        }
    }
    
    post {
        always {
            echo "🧹 清理工作空间"
            cleanWs()
        }
        success {
            echo "🎉 流水线执行成功！"
            // 可以添加成功通知，如钉钉、邮件等
        }
        failure {
            echo "❌ 流水线执行失败！"
            // 可以添加失败通知
        }
        unstable {
            echo "⚠️ 流水线执行不稳定"
        }
    }
}
