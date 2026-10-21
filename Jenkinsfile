
pipeline {
    agent any

    parameters {
        string(
            name: 'IMAGE_NAME',
            defaultValue: 'shashwat2504/ecopulse',
            description: 'Docker Hub repository name'
        )
        string(
            name: 'REGISTRY_CREDENTIALS_ID',
            defaultValue: 'dockerhub-credentials',
            description: 'Jenkins ID for Docker Hub credentials'
        )
        string(
            name: 'KUBECONFIG_CREDENTIALS_ID',
            defaultValue: 'minikube-kubeconfig',
            description: 'Jenkins ID for Minikube kubeconfig secret file'
        )
        choice(
            name: 'DEPLOY_TARGET',
            choices: ['dry-run', 'minikube'],
            description: 'dry-run validates manifests locally; minikube deploys to a configured cluster'
        )
    }

    environment {
        APP_NAME = 'ecopulse'
        PYTHONUNBUFFERED = '1'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Stage 1: Checkout source code'
                checkout scm
                sh 'git log -1 --pretty=format:"Commit: %h - %s"'
            }
        }

        stage('Environment & Dependencies') {
            steps {
                echo 'Stage 2: Install Python dependencies'
                sh '''
                    set -eu
                    python3 -m venv venv
                    . venv/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Automated Tests & Quality') {
            steps {
                echo 'Stage 3: Run automated tests'
                sh '''
                    set -eu
                    . venv/bin/activate
                    PYTHONPATH="$WORKSPACE" python -m pytest --junitxml=pytest-results.xml
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
                echo 'Stage 4: Build Docker image'
                sh '''
                    set -eu
                    docker build \
                        -t "$IMAGE_NAME:$BUILD_NUMBER" \
                        -t "$IMAGE_NAME:latest" .
                '''
            }
        }

        stage('Docker Hub Push') {
            steps {
                echo 'Stage 5: Push images to Docker Hub'
                withCredentials([
                    usernamePassword(
                        credentialsId: params.REGISTRY_CREDENTIALS_ID,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )
                ]) {
                    sh '''
                        set -eu
                        echo "$DOCKER_PASS" | docker login \
                            --username "$DOCKER_USER" --password-stdin
                        docker push "$IMAGE_NAME:$BUILD_NUMBER"
                        docker push "$IMAGE_NAME:latest"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            when {
                expression { params.DEPLOY_TARGET == 'minikube' }
            }
            steps {
                echo 'Stage 6: Deploy to configured Kubernetes cluster'
                withCredentials([
                    file(
                        credentialsId: params.KUBECONFIG_CREDENTIALS_ID,
                        variable: 'KUBECONFIG_FILE'
                    )
                ]) {
                    sh '''
                        set -eu
                        export KUBECONFIG="$KUBECONFIG_FILE"

                        kubectl cluster-info

                        sed "s|your-dockerhub-username/ecopulse:latest|$IMAGE_NAME:$BUILD_NUMBER|g" \
                            k8s/deployment.yaml > deployment-ci.yaml

                        kubectl apply -f deployment-ci.yaml
                        kubectl apply -f k8s/service.yaml
                    '''
                }
            }
        }

        stage('Deployment Verification') {
            when {
                expression { params.DEPLOY_TARGET == 'minikube' }
            }
            steps {
                echo 'Stage 7: Verify Kubernetes deployment'
                withCredentials([
                    file(
                        credentialsId: params.KUBECONFIG_CREDENTIALS_ID,
                        variable: 'KUBECONFIG_FILE'
                    )
                ]) {
                    sh '''
                        set -eu
                        export KUBECONFIG="$KUBECONFIG_FILE"

                        kubectl rollout status \
                            deployment/ecopulse-deployment --timeout=180s

                        kubectl get deployments -l app=ecopulse
                        kubectl get pods -l app=ecopulse
                        kubectl get services -l app=ecopulse
                    '''
                }
            }
        }

        stage('Dry-Run Verification') {
            when {
                expression { params.DEPLOY_TARGET == 'dry-run' }
            }
            steps {
                echo 'Stage 8: Validate Kubernetes YAML locally, without contacting a cluster'
                sh '''
                    set -eu
                    . venv/bin/activate
                    python -m pip install PyYAML

                    python - <<'PY'
import sys
from pathlib import Path
import yaml

manifest_dir = Path("k8s")
files = sorted(manifest_dir.glob("*.yaml"))
files += sorted(manifest_dir.glob("*.yml"))

if not files:
    sys.exit("FAIL: No YAML manifests found in k8s/")

count = 0

for path in files:
    print(f"Checking {path}")
    with path.open(encoding="utf-8") as stream:
        documents = [
            doc for doc in yaml.safe_load_all(stream)
            if doc is not None
        ]

    if not documents:
        sys.exit(f"FAIL: {path} contains no YAML documents")

    for doc in documents:
        if not isinstance(doc, dict):
            sys.exit(f"FAIL: {path} contains a non-object document")

        for field in ("apiVersion", "kind", "metadata"):
            if field not in doc:
                sys.exit(f"FAIL: {path} is missing {field}")

        if not isinstance(doc["metadata"], dict):
            sys.exit(f"FAIL: {path} has invalid metadata")

        print(f"  OK: {doc['kind']} manifest")
        count += 1

print(f"SUCCESS: Parsed and checked {count} Kubernetes manifest(s).")
PY
                '''
            }
        }
    }

    post {
        success {
            echo "SUCCESS: EcoPulse pipeline completed for build #${BUILD_NUMBER}."
        }
        failure {
            echo 'ERROR: Pipeline failed. Review the first failing stage in Console Output.'
        }
        always {
            cleanWs deleteDirs: true, notFailBuild: true
        }
    }
}
