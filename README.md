Checkmate
=====

A service for checking URLs are safe.

Installing Checkmate in a development environment
------------------------------------------------

### You will need

* Checkmate integrates with h and the Hypothesis client, so you will need to
  set up development environments for each of those before you can develop Checkmate:

  * https://h.readthedocs.io/en/latest/developing/install/
  * https://h.readthedocs.io/projects/client/en/latest/developers/developing/

* [Git](https://git-scm.com/)

* [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.
  
### Clone the git repo

    git clone https://github.com/hypothesis/checkmate.git

This will download the code into a `checkmate` directory in your current working
directory. You need to be in the `checkmate` directory from the remainder of the
installation process:

    cd checkmate

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the assets.

This will start the app on http://localhost:9099

**That's it!** You’ve finished setting up your Checkmate development environment. 
Run `make help` to see all the commands that are available for running the tests,
linting, code formatting, etc.

Configuration
-------------

Environment variables:

| Name | Effect | Example |
|------|--------|---------|
| `CHECKMATE_BLOCKLIST_URL`   | Where to download the blocklist online | `https://some-aws-s3.bucket/file.txt` |
| `CHECKMATE_BLOCKLIST_PATH`  | Where to store the blocklist locally   | `/var/lib/hypothesis/blocklist.txt` |

For details of changing the blocklist see:

 * https://stackoverflow.com/c/hypothesis/questions/102/250
