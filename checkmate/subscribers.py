def set_public_server_name(event):
    event.request.environ["HTTP_HOST"] = event.request.registry.settings["public_host"]
    event.request.environ["wsgi.url_scheme"] = event.request.registry.settings[
        "public_scheme"
    ]
