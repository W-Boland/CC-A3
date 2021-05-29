from flask import Flask, request

application = Flask(__name__)

@application.route("/")
def index():
    return "hello, Welcome"


if __name__ == '__main__':
    application.run()