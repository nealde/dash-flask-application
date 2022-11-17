import pygments, markdown
from flask import Flask, flash, redirect, render_template, render_template_string, request, url_for
from flask_flatpages import FlatPages, pygmented_markdown, pygments_style_defs
from flask_mail import Mail, Message
from flask_assets import Environment
from .forms.paginate import Paginate as Paginate
from .forms.forms import ContactForm as ContactForm


def my_markdown(text):
    markdown_text = render_template_string(text)
    pygmented_text = markdown.markdown(markdown_text, extensions=["codehilite", "fenced_code", "tables", "mdx_math"])
    return pygmented_text


def init_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config")
    app.config["FLATPAGES_HTML_RENDERER"] = my_markdown

    assets = Environment()
    assets.init_app(app)


    with app.app_context():
        assets.auto_build = True
        from . import routes
        from .plotlydash.dashboard import init_dashboard

        app = init_dashboard(app, routes.pages)

    return app
