from flask import Flask
from flask_restful import Api
from ezdb import EZDBServer

app = Flask(__name__)
api = Api(app)
api.add_resource(EZDBServer, '/<string:get_msg_unicode>')
if __name__ == '__main__':
    app.run(debug=True)
