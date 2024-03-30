pipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'lorkorblaq/clinicalx_api'
        DOCKER_REGISTRY_URL = 'https://hub.docker.com'
        GIT_CREDENTIALS = 'gitpass'
        DOCKER_CREDENTIALS= 'dockerpass'
        DOCKERFILE_PATH = 'Dockerfile'
    }
    stages {
        stage('checkout') {
            steps {
                git(url: 'https://github.com/lorkorblaq/clinicalx_api.git', branch: 'main', credentialsId: GIT_CREDENTIALS)
            }
        }
        stage('Build Image') {
            steps {
                script {
                    echo 'Building image..'
                    docker.build("${DOCKER_IMAGE}", "-f ${DOCKERFILE_PATH} .")
                    }
            }
        }
        stage('Unit Testing') {
            steps {
              script {
                echo 'Unit testing to begin..'
                  
                echo 'Running unit tests..'
                sh "docker run -d --name clinicalx_api_test ${DOCKER_IMAGE}"
                // sh "docker exec clinicalx_api_test pytest tests/test_user_api.py"
                sh "docker exec clinicalx_api_test pytest --junitxml=pytest-report.xml tests/test_user_api.py"
                sh "docker stop clinicalx_api_test"
                sh "docker rm clinicalx_api_test"
              }
            }
        }
        
        stage('Push Image') {
            steps {
                echo 'Pushing to Docker Hub..'
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                    sh "docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD docker.io"
                    sh "docker push ${DOCKER_IMAGE}"                }
            }
        }
        stage('Test Deployment') {
            steps {
              script {
                echo 'Deploying to testing stage..'
                sh "docker pull ${DOCKER_IMAGE}"
        
                // Stop and remove any existing container
                sh "docker stop clinicalx_api_test_stage || true"
                sh "docker rm clinicalx_api_test_stage || true"
        
                // Run the new container
                sh "docker run -d --name clinicalx_api_test_stage -p 3001:3000 ${DOCKER_IMAGE}"
                sh "docker rmi \$(docker images -q) || true"
              }
            }
        }
        
       stage('Deployment Production') {
            steps {
                echo 'Deploying to production...'
        
                // Pull the latest image from Docker Hub
                sh "docker pull ${DOCKER_IMAGE}"
        
                // Stop and remove any existing container
                sh "docker stop clinicalx_api || true"
                sh "docker rm clinicalx_api || true"
        
                // Run the new container
                sh "docker run -d --name clinicalx_api -p 3000:3000 ${DOCKER_IMAGE}"
                // Remove previous Docker images
                sh "docker rmi \$(docker images -q) || true"
            }
        }

     }
 }
