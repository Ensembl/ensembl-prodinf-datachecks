pipeline {
  agent {
   docker {
     image 'python:2.7-slim'
   }
  }
  stages {
    stage('Clone repository') {
        steps {
          checkout scm
        }
    }
    stage('Set up') {
        steps {
          sh 'pip install -r requirements.txt'
        }
    }
    
    stage('Test') {
        steps {
            sh 'nosetests tests'
        }
    }
  }
}
