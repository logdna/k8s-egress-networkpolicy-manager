pipeline {
  agent any

  options {
    timeout time: 1, unit: 'HOURS'
    timestamps()
    ansiColor 'xterm'
  }

  stages {
    stage('Setup') {
      steps {
        echo "Checking out..."
        checkout scm
      }
    }
    stage('Test') {
      steps {
        echo "Running tests..."
        sh 'make test'
      }
    }
    stage('Build') {
      steps {
        echo "Building..."
        sh 'make build'
      }
    }
    stage('Publish') {
      // when {
      //   anyOf {
      //     branch "master"
      //     branch "main"
      //   }
      // }
      steps {
        echo "Publish to docker.io and GCR..."
        script {
          docker.withRegistry(
            'https://index.docker.io/v1/',
            'dockerhub-username-password'
          ) {
            sh 'make publish'
          }
        }
      }
    }
  }
  post {
    always {
      // Generate JUnit, PEP8, Pylint and Coverage reports.
      withChecks('Unit Tests') {
        junit 'reports/*junit.xml'
      }
      recordIssues(tool: pep8(pattern: 'reports/pep8.report'))
      recordIssues(tool: pyLint(pattern: 'reports/pylint.report'))
    }
  }
}