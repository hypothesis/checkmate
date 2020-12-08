/**
 * This app's Jenkins Pipeline.
 *
 * This is written in Jenkins Scripted Pipeline language.
 * For docs see:
 * https://jenkins.io/doc/book/pipeline/syntax/#scripted-pipeline
*/

// Import the Hypothesis shared pipeline library, which is defined in this
// repo: https://github.com/hypothesis/pipeline-library
@Library("pipeline-library") _

// Build the hypothesis/checkmate Docker image.
def img

node {
    // The args that we'll pass to Docker run each time we run the Docker
    // image.
    runArgs = "-u root -e SITE_PACKAGES=true"

    stage("Build") {
        // Checkout the commit that triggered this pipeline run.
        checkout scm
        // Build the Docker image.
        img = buildApp(name: "hypothesis/checkmate")
    }

    stage("Tests") {
        testApp(image: img, runArgs: "${runArgs}") {
            /* Install dependencies required to run the tox env */
            sh "apk add build-base postgresql-dev python3-dev"
            sh "pip3 install -q tox>=3.8.0"
            
            sh "cd /var/lib/hypothesis && make test"
        }
    }

    onlyOnMain {
        stage("release") {
            releaseApp(image: img)
        }
    }
}

onlyOnMain {
    milestone()
    stage("qa deploy") {
        deployApp(image: img, app: "checkmate", env: "qa")
    }

    milestone()
    stage("prod deploy") {
        input(message: "Deploy to prod?")
        milestone()
        deployApp(image: img, app: "checkmate", env: "prod")
    }
}