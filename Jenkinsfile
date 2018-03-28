pipeline {
  agent any
  def app
  stages {
    stage('Clone repository') {
        checkout scm
    }
    stage('Set up') {
        sh 'pip install -r requirements.txt'
    }
    
    stage('Test image') {
        app.inside {
            sh 'nosetests tests'
        }
    }
  }
}
