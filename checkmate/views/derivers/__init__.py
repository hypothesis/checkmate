from checkmate.views.derivers.json_api import json_api_view_deriver


def includeme(config):  # pragma: no cover
    config.add_view_deriver(
        json_api_view_deriver, under="rendered_view", over="mapped_view"
    )
