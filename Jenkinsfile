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
            installDeps()
            run("make test")
        }
    }

    onlyOnMaster {
        stage("release") {
            releaseApp(image: img)
        }
    }
}

onlyOnMaster {
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

/**
 * Install some common system dependencies.
 *
 * These are test dependencies that're need to run most of the stages above
 * (tests, lint, ...) but that aren't installed in the production Docker image.
 */
def installDeps() {
    sh "pip3 install -q tox>=3.8.0"
}

/** Run the given command. */
def run(command) {
    sh "apk add build-base"
    sh "cd /var/lib/hypothesis && ${command}"
}
