pipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'lorkorblaq/clinicalx_api'
        DOCKER_TAG = "${DOCKER_IMAGE}:${BUILD_NUMBER}" 
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
                    // sh "docker stop clinicalx_api_test || true"
                    // sh "docker rm clinicalx_api_test || true"
                    sh "docker run -d --name clinicalx_api_test -p 2999:3000 ${DOCKER_IMAGE}"
                    // sh "docker exec clinicalx_api_test pytest tests/test_user_api.py"
                    sh "docker exec clinicalx_api_test pytest --junitxml=pytest-report.xml tests/test_user_api.py"
                    sh "docker stop clinicalx_api_test"
                    sh "docker rm clinicalx_api_test"
                    sh "docker rmi ${DOCKER_TAG} -f"                    
                    }
            }
        }
        stage('Test Stage') {
            steps {
              script {
                echo 'Testing to begin..'
                // sh "docker pull ${DOCKER_IMAGE}"
                echo 'Deploying to testing stage..'
                docker.build("${DOCKER_TAG}", "-f ${DOCKERFILE_PATH} .")
                sh "docker stop clinicalx_api_test_stage || true"
                sh "docker rm clinicalx_api_test_stage || true"
        
                // Run the new container
                sh "docker run -d --name clinicalx_api_test -p 3001:3000 ${DOCKER_IMAGE}"
                echo 'Starting Integration testing'
                // sh "docker rmi \$(docker images -q) || true"
                // echo 'Running unit tests..'
                // sh "docker stop clinicalx_api_test || true"
                // sh "docker rm clinicalx_api_test || true"
                // sh "docker run -d --name clinicalx_api_test ${DOCKER_TAG}"
                // // sh "docker exec clinicalx_api_test pytest tests/test_user_api.py"
                // sh "docker exec clinicalx_api_test pytest --junitxml=pytest-report.xml tests/test_user_api.py"
                sh "docker stop clinicalx_api_test"
                sh "docker rm clinicalx_api_test"
                sh "docker rmi ${DOCKER_TAG} -f"                    
                // sh "docker rmi \$(docker images -q lorkorblaq/clinicalx_api) || true"
              }
            }
        }
        
        stage('Beta stage') {
            steps {
              script {
                echo 'Deploying to Beta stage..'
                // sh "docker pull ${DOCKER_IMAGE}"
                docker.build("${DOCKER_TAG}", "-f ${DOCKERFILE_PATH} .")
                // Stop and remove any existing container
                sh "docker stop clinicalx_api_beta || true"
                sh "docker rm clinicalx_api_beta || true"
                echo 'Starting End to end testing...'
                // Run the new container
                sh "docker run -d --name clinicalx_api_beta -p 3002:3000 ${DOCKER_TAG}"
                // sh "docker rmi \$(docker images -q) || true"
                // def currentImageId = sh(script: "docker inspect --format='{{.Id}}' clinicalx_api_beta", returnStdout: true).trim()
                // def otherImages = sh(script: "docker images --quiet --filter=reference=${repository} --filter=since=${currentImageId}", returnStdout: true).trim()
                // if(otherImages) {
                //     sh "docker rmi $otherImages -f"
                // }
                sh "docker stop clinicalx_api_beta || true"
                sh "docker rm clinicalx_api_beta || true"
                sh "docker rmi ${DOCKER_TAG} -f || true"
              }
            }
        }
        stage('Push Image') {
            steps {
                echo 'Pushing to Docker Hub..'
                        withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS, passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
                            // Use 'withCredentials' block to securely access username and password from Jenkins credentials
                            sh "docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}"                                                   
                            // Push the Docker image to Docker Hub
                            sh "docker push lorkorblaq/clinicalx_api"              
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
                // Remove previous Docker images
                // sh "docker rmi \$(docker images -q) -f || true"
                // sh "docker rmi \$(docker images -q lorkorblaq/clinicalx_api) -f || true"
            }
        }
         stage('Cleanup Images') {
            steps {
                script {
                    echo 'Cleaning up old Docker images..'
                    def images = sh(script: 'docker images --format "{{.ID}}:{{.Repository}}" | grep lorkorblaq/clinicalx_api | head -n -3', returnStdout: true).trim()
                    if(images) {
                        sh "docker rmi $images"
                    }
                }
            }
        }        

     }
 }
