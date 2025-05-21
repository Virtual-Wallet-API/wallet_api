from starlette.templating import Jinja2Templates

templates_dir = "frontend/templates"
templates = Jinja2Templates(directory=templates_dir)
