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
        stage('Push Image') {
            steps {
                echo 'Pushing to Docker Hub..'
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                    sh "docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD docker.io"
                    sh "docker push ${DOCKER_IMAGE}"                }
            }
        }
        stage('Test') {
            steps {
              script {
                echo 'Testing..'
                def dockerimage = docker.build("${DOCKER_IMAGE}", "-f ${DOCKERFILE_PATH} .")
                dockerimage.inside {
                    sh 'pytest --junitxml=pytest-report.xml api/tests/test_user_api.py'  // Run pytest with JUnit output
                }
              }
            }
        }
       stage('Deployment') {
            steps {
                echo 'Deploying...'
        
                // Pull the latest image from Docker Hub
                sh "docker pull ${DOCKER_IMAGE}"
        
                // Stop and remove any existing container
                sh "docker stop clinicalx_api || true"
                sh "docker rm clinicalx_api || true"
        
                // Run the new container
                sh "docker run -d --name clinicalx_api -p 3000:3000 ${DOCKER_IMAGE}"
            }
        }

     }
 }
