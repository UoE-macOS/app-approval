from flask import Flask, abort, render_template, request
from validation import valid_uuid, valid_uun
from apprequest import Request
import random 
import pprint

app = Flask(__name__)

api1_base = '/appreq/api/v1.0/'
ui1_base = '/request/'

@app.route(api1_base + "request/<string:uun>/<string:uuid>/approve", methods=['GET'])
def approve(uuid):
    return "This would approve the request with uuid: {:s}".format(uuid)

@app.route(api1_base + "request/<string:uun>/<string:uuid>/deny", methods=['GET'])
def deny(uuid):
    return "This would deny the request with uuid: {:s}".format(uuid)

@app.route(api1_base + "request/<string:uun>/<string:uuid>/show", methods=['GET'])
def show(uuid):
    return "This would show the request with uuid: {:s}".format(uuid)

@app.route(api1_base + "requests/<string:uun>/list", methods=['GET'])
def list(uun):
    return "This would list requests belonging to user: {:s}".format(uun)

@app.route(ui1_base + "<string:uun>/<string:uuid>/view", methods=['GET'])
def landing(uun, uuid):
    if valid_uuid(uuid) and valid_uun(uun):
        try:
            req = Request(uuid, uun)
            return render_template('landing.html', **req.attributes)
        except Exception as ex:
            return render_template('error.html', error='Couldn\'t load request.')
    else:
        return render_template('error.html', error='Invalid UUID or Username')


@app.route(ui1_base + "<string:uun>/<string:uuid>/process", methods=['POST'])
def process(uun, uuid):
    
    response = request.form['response'] 
    msg = request.form['message'] or 'Denied'

    req = Request(uuid, uun)
  
    try:
        if response == 'approve':
            req.approve()
            return render_template('success.html', message="Request was successfully approved")
        elif response == 'deny':
            req.deny(msg)       
            return render_template('success.html', message="Request was successfully denied")
        else:
            abort(400) # Unknown action.
  
    except Exception as ex: 
        return render_template('error.html', error="Something went wrong, the request has not been processed: {:s}".format(ex))

def _approve():
    return random.choice([True, False])

def _deny():
    return random.choice([True, False])



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
