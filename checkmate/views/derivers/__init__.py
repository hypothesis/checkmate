from checkmate.views.derivers.jsonapi import jsonapi_view_deriver


def includeme(config):  # pragma: no cover
    config.add_view_deriver(
        jsonapi_view_deriver, under="rendered_view", over="mapped_view"
    )
