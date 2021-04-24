"""Plotly Dash HTML layout override."""
from flask import render_template
from flask import current_app as app
from flask_flatpages import FlatPages
import os
# path = os.path.dirname(os.path.dirname(__file__))
# try:

# html_layout = render_template(
#         "dash.html",
#         title="Plotly Dash Flask Tutorial",
#         description="Embed Plotly Dash into your Flask applications.",
#         template="home-template",
#         body="This is a homepage served with Flask.",
#     )
# html_layout = open(os.path.join(path, 'templates', 'dash.html')).read()
# html_layout = """
# {% extends "base.html" %}
#
# {% block title %}{{ page.title }}{% endblock %}
#
# {%app_entry%}
# """

html_layout = """
<!DOCTYPE html>
    <html>
        <head>
        <meta charset="utf-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="shortcut icon" href="static/favicon.png">
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
        </head>
        <body class="dash-template">
            <!-- Wrapper -->
    
            <div id="wrapper">
            <section id="header">
                <header>
                    <a itemprop="url" href="/">
                      <img itemprop="logo" src="/static/img/logo.png" alt="Dummy logotype" />
                    </a>
              </header>
              <nav id="nav">
                <input type="checkbox" id="menutoggle">
                <label for="menutoggle" class="labeltoggle">&#9776; Menu</label>
                <ul>
                  <li><a href="/">Blog</a></li>
                  <li><a href="/dashapp">Visualizations</a></li>
                  <li><a href="/about">About</a></li>
                  <li><a href="/contact">Contact</a></li>
                </ul>
              </nav>
            </section>
                    <main>
                    {%app_entry%}
                    </main>
                
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </div><!-- ./#wrapper -->
        </body>
    </html>
"""

# html_layout = """
# <!DOCTYPE html>
#     <html>
#         <head>
#             {%metas%}
#             <title>{%title%}</title>
#             {%favicon%}
#             {%css%}
#         </head>
#         <body class="dash-template">
#             <header>
#               <div class="nav-wrapper">
#                 <a href="/">
#                     <img src="/static/img/logo.png" class="logo" />
#                     <h1>Plotly Dash Flask Tutorial</h1>
#                   </a>
#                 <nav>
#                 </nav>
#             </div>
#             </header>
#             {%app_entry%}
#             <footer>
#                 {%config%}
#                 {%scripts%}
#                 {%renderer%}
#             </footer>
#         </body>
#     </html>
# """
