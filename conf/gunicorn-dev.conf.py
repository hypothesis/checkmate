from glob import glob

bind = "0.0.0.0:9099"
reload = True
reload_extra_files = glob("checkmate/templates/**/*", recursive=True)
timeout = 0
