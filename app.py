import os

from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db = SQLAlchemy(app)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        pass
    else:
        return render_template("homepage.html")

if __name__ == "__main__":
    app.debug = True
    app.run()
