from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from starlette.staticfiles import StaticFiles

from frontend.jinja_utils import jenv

jenv = Environment(loader=FileSystemLoader("frontend/public/test"), cache_size=0)
templates_dir = "frontend/prublic/test"
templates = Jinja2Templates(env=jenv, auto_reload=True)
temp = templates.TemplateResponse("index.html", {"request": None});