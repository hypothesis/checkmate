Checkmate
=====

A service for checking URLs are safe.

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

For details of changing the blocklist see:

 * https://stackoverflow.com/c/hypothesis/questions/102/250


Installing Checkmate in a development environment
------------------------------------------------

### You will need

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
