from fastapi.templating import Jinja2Templates
from frontend.jinja_utils import jenv

templates_dir = "frontend/templates"
templates = Jinja2Templates(env=jenv, auto_reload=True)