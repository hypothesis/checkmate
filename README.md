Checkmate
=========

A service for checking URLs are safe.

Installing Checkmate in a development environment
-------------------------------------------------

### You will need

* [Git](https://git-scm.com/)

* [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.

* [Docker](https://docs.docker.com/install/).
  Follow the [instructions on the Docker website](https://docs.docker.com/install/)
  to install Docker.

### Clone the Git repo

    git clone https://github.com/hypothesis/checkmate.git

This will download the code into a `checkmate` directory in your current working
directory. You need to be in the `checkmate` directory from the remainder of the
installation process:

    cd checkmate

### Run the services with Docker Compose

Start the services that Checkmate requires using Docker Compose:

    make services

### Create the development data and settings

Create the database contents and environment variable settings needed to get
Checkmate working:

    make devdata

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the assets.

This will start the app on http://localhost:9099.

**That's it!** You’ve finished setting up your Checkmate development environment.
Run `make help` to see all the commands that are available for running the tests,
linting, code formatting, etc.

API
---

### `GET /api/check?url=<url_to_check>`

Check a specific URL for problems. The return values are in a [JSON:API](https://jsonapi.org/) style.

**Return codes:**

 * `200` - The URL has reasons to block (JSON body)
 * `204` - The URL has no reasons to block (no body)
 * `400` - There is something wrong with your request

**Return examples:**

Reasons are listed in decreasing order of severity.

```json5
// 200 OK
{
    "data": [
        {
            "type": "reason", "id": "malicious",
            "attributes": {"severity": "mandatory"}
        },
        {
            "type": "reason", "id": "high-io",
            "attributes": {"severity": "advisory"}
        }
    ],
    "meta": {
        "maxSeverity": "mandatory"
    }
}
```

In the case of errors:

```json5
// 400 Bad Request
{
    "errors": [
        {
            "id": "BadURLParameter",
            "detail": "Parameter 'url' is required",
            "source": {"parameter": "url"}
        }
    ]
}
```

### `GET /_status`

Check the service status

**Return codes:**

 * `200` - If the service is up

**Return example:**

```json5
//200 OK
{"status": "okay"}
```

Configuration
-------------

Environment variables:

| Name | Effect | Example |
|------|--------|---------|
| `CHECKMATE_BLOCKLIST_URL`   | Where to download the blocklist online | `https://some-aws-s3.bucket/file.txt` |
| `CHECKMATE_SECRET` | Secret used for signing URLs | `AB823F97FF2E330C1A20`
| `PUBLIC_SCHEME` | Scheme used on the public accessible checkmate instance | `https`
| `PUBLIC_HOST` | Host of the public accessible checkmate instance | `some-domain.com`

For details of changing the blocklist see:

 * https://stackoverflow.com/c/hypothesis/questions/102/250

Using Checkmate in a development environment
--------------------------------------------

### Authenticating requests

To authenticate requests to the dev server you must specify an API key via
HTTP Basic Authentication. Set the username field to the API key and leave the
password blank. In the local development environment a default `dev_api_key` API
key is accepted:


```sh
curl http://dev_api_key@localhost:9099/api/check?url=http://example.com/
```

### Accessing the admin pages

To access the admin UI for Checkmate, visit http://localhost:9099/ui/admin.
You will need to login using an @hypothes.is Google account.
