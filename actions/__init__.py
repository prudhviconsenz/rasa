from .defaultlog import log
import logging

log.setLevel(logging.DEBUG)
for x in ["ctparse", "partial_parse", "urllib3.connectionpool", "spotipy.client"]:
    logging.getLogger(x).setLevel(logging.ERROR)
log.debug("logging started")
log.info("logging started")

import random
import os

# ensure repeatable results
random.seed(42)

# only keep conversations from current session
root = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
try:
    os.remove(f"{root}/rasa.db")
    log.warning("deleted rasa.db")
except Exception as e:
    log.exception("failed to delete rasa.db")
