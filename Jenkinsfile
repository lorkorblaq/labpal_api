pipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'lorkorblaq/clinicalx_api'
        DOCKER_TAG = "${DOCKER_IMAGE}:latest"
        // ${BUILD_NUMBER}" 
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
                    docker.build("${DOCKER_TAG}", "-f ${DOCKERFILE_PATH} .")
                    }
                script{
                    echo 'Running unit tests..'
                    sh "docker stop clinicalx_api_build || true"
                    sh "docker rm clinicalx_api_build || true"
                    sh "docker run -d --name clinicalx_api_build -p 2997:3000 ${DOCKER_TAG}"
                    // sh "docker exec clinicalx_api_build pytest tests/test_user_api.py"
                    sh "docker exec clinicalx_api_build pytest --junitxml=pytest-report.xml end_points/tests/test_user_api.py"
                    sh "docker stop clinicalx_api_build"
                    sh "docker rm clinicalx_api_build"
                    // sh "docker rmi ${DOCKER_TAG} -f"                    
                    }
            }
        }
        stage('Push Image') {
            steps {
                // script {
                //     echo 'Building image..'
                //     docker.build("${DOCKER_TAG}", "-f ${DOCKERFILE_PATH} .")
                //     }
                echo 'Pushing to Docker Hub..'
                // docker.build("${DOCKER_TAG}", "-f ${DOCKERFILE_PATH} .")
                    // Use 'withCredentials' block to securely access username and password from Jenkins credentials
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                    sh "docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}"                                                   
                    // Push the Docker image to Docker Hub
                    sh "docker push ${DOCKER_TAG}" 
                    sh "docker rmi ${DOCKER_TAG} -f || true"
                    }
            }
        }    
        stage('Test Stage') {
            steps {
              script {
                echo 'Testing to begin..'
                sh "docker pull ${DOCKER_TAG}"
                echo 'Deploying to testing stage..'
                // docker.build("${DOCKER_TAG}", "-f ${DOCKERFILE_PATH} .")
                sh "docker stop clinicalx_api_test || true"
                sh "docker rm clinicalx_api_test || true"
                // Run the new container
                sh "docker run -d --name clinicalx_api_test -p 2998:3000 ${DOCKER_TAG}"
                // sh "docker exec clinicalx_api_test pytest --junitxml=pytest-report.xml /end_points/tests/test_user_api.py"
                sh "docker stop clinicalx_api_test"
                sh "docker rm clinicalx_api_test"
                sh "docker rmi ${DOCKER_TAG} -f"                    
              }
            }
        }
        
        stage('Beta stage') {
            steps {
              script {
                echo 'Deploying to Beta stage..'
                sh "docker pull ${DOCKER_TAG}"
                // Stop and remove any existing container
                sh "docker stop clinicalx_api_beta || true"
                sh "docker rm clinicalx_api_beta || true"
                echo 'Starting End to end testing...'
                // Run the new container
                sh "docker run -d --name clinicalx_api_beta -p 2999:3000 ${DOCKER_TAG}"
                sh "docker stop clinicalx_api_beta || true"
                sh "docker rm clinicalx_api_beta || true"
                sh "docker rmi ${DOCKER_TAG} -f || true"
              }
            }
        }

       
        stage('Production Deployment') {
            steps {
                echo 'Deploying to production...'
        
                // Pull the latest image from Docker Hub
                sh "docker pull ${DOCKER_TAG}"
        
                // Stop and remove any existing container
                sh "docker stop clinicalx_api || true"
                sh "docker rm clinicalx_api || true"
        
                // Run the new container
                sh "docker run -d --name clinicalx_api -p 3000:3000 ${DOCKER_TAG}"
            }
        }       

     }
 }
