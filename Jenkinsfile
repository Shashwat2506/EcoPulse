pipeline {
    agent any

    parameters {
        string(
            name: 'IMAGE_NAME',
            defaultValue: 'your-dockerhub-username/ecopulse',
            description: 'Docker Hub repository name (e.g., studentuser/ecopulse)'
        )
        string(
            name: 'REGISTRY_CREDENTIALS_ID',
            defaultValue: 'dockerhub-credentials',
            description: 'Jenkins Credentials ID for Docker Hub (Username with Password)'
        )
        string(
            name: 'KUBECONFIG_CREDENTIALS_ID',
            defaultValue: 'minikube-kubeconfig',
            description: 'Jenkins Credentials ID for Minikube Kubeconfig (Secret file)'
        )
        choice(
            name: 'DEPLOY_TARGET',
            choices: ['minikube', 'dry-run'],
            description: 'Target environment: deploy to live Minikube cluster or execute dry-run validation'
        )
    }

    environment {
        APP_NAME = 'ecopulse'
        BUILD_TAG = "${BUILD_NUMBER}"
        FULL_IMAGE = "${params.IMAGE_NAME}:${BUILD_TAG}"
        LATEST_IMAGE = "${params.IMAGE_NAME}:latest"
        PYTHONUNBUFFERED = '1'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        ansiColor('xterm')
    }

    stages {
        stage('Checkout') {
            steps {
                echo "==> [Stage 1/8] Checking out repository source code from Git..."
                checkout scm
                sh 'git log -1 --pretty=format:"Commit: %h by %an on %cd: %s"'
            }
        }

        stage('Environment & Dependencies') {
            steps {
                echo "==> [Stage 2/8] Setting up Python virtual environment and installing dependencies..."
                sh '''
                    python3 -m venv venv || python -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Automated Tests & Quality') {
            steps {
                echo "==> [Stage 3/8] Running pytest test suite and input validation..."
                sh '''
                    . venv/bin/activate
                    pytest --junitxml=pytest-results.xml
                '''
            }
            post {
                always {
                    junit testResults: 'pytest-results.xml', allowEmptyResults: true
                }
            }
        }

        stage('Docker Image Build') {
            steps {
                echo "==> [Stage 4/8] Building Docker container image: ${FULL_IMAGE}..."
                sh """
                    docker build -t ${FULL_IMAGE} -t ${LATEST_IMAGE} .
                """
            }
        }

        stage('Docker Hub Push') {
            steps {
                echo "==> [Stage 5/8] Authenticating and pushing Docker image to registry..."
                withCredentials([usernamePassword(
                    credentialsId: params.REGISTRY_CREDENTIALS_ID,
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                        docker push ${FULL_IMAGE}
                        docker push ${LATEST_IMAGE}
                        docker logout
                    """
                }
            }
        }

        stage('Deploy to Minikube') {
            when {
                expression { return params.DEPLOY_TARGET == 'minikube' }
            }
            steps {
                echo "==> [Stage 6/8] Deploying to Minikube Kubernetes cluster..."
                withCredentials([file(
                    credentialsId: params.KUBECONFIG_CREDENTIALS_ID,
                    variable: 'KUBECONFIG_FILE'
                )]) {
                    sh """
                        export KUBECONFIG="\$KUBECONFIG_FILE"
                        
                        # Substitute image reference dynamically
                        sed -i 's|your-dockerhub-username/ecopulse:latest|${FULL_IMAGE}|g' k8s/deployment.yaml
                        
                        # Apply Kubernetes manifests
                        kubectl apply -f k8s/deployment.yaml
                        kubectl apply -f k8s/service.yaml
                    """
                }
            }
        }

        stage('Deployment Verification') {
            when {
                expression { return params.DEPLOY_TARGET == 'minikube' }
            }
            steps {
                echo "==> [Stage 7/8] Verifying rollout status and pod readiness..."
                withCredentials([file(
                    credentialsId: params.KUBECONFIG_CREDENTIALS_ID,
                    variable: 'KUBECONFIG_FILE'
                )]) {
                    sh """
                        export KUBECONFIG="\$KUBECONFIG_FILE"
                        
                        # Wait for rolling update completion (timeout 180s)
                        kubectl rollout status deployment/ecopulse-deployment --timeout=180s
                        
                        # Display deployment status and pod details
                        kubectl get deployments -l app=ecopulse
                        kubectl get pods -l app=ecopulse
                        kubectl get services -l app=ecopulse
                    """
                }
            }
        }

        stage('Dry-Run Verification') {
            when {
                expression { return params.DEPLOY_TARGET == 'dry-run' }
            }
            steps {
                echo "==> [Dry-Run Mode] Validating Kubernetes YAML manifests..."
                sh """
                    sed 's|your-dockerhub-username/ecopulse:latest|${FULL_IMAGE}|g' k8s/deployment.yaml | kubectl apply --dry-run=client -f -
                    kubectl apply --dry-run=client -f k8s/service.yaml
                    echo "Kubernetes manifests validated successfully (dry-run)."
                """
            }
        }
    }

    post {
        success {
            echo "SUCCESS: EcoPulse CI/CD Pipeline completed successfully for Build #${BUILD_NUMBER}!"
        }
        failure {
            echo "ERROR: Pipeline failed. Check console output for stage failure details."
        }
        always {
            cleanWs deleteDirs: true, notFailBuild: true
        }
    }
}
