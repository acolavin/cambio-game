import yaml
import pathlib

from ..app import app

GAME_RULES = None

with open(str(pathlib.Path(__file__).parent.absolute()).rstrip('/') + '/game_rules.yaml', 'r') as fid:
    GAME_RULES = yaml.load(fid)
    # TODO: User safelaod for yaml... or better yet don't use yaml.
    app.logger.info(GAME_RULES)

from .login_routes import *
from .game_routes import *
