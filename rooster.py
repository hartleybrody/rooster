from flask import Flask, render_template, request
app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        pass
    else:
        return render_template("homepage.html")

if __name__ == "__main__":
    app.debug = True
    app.run()
