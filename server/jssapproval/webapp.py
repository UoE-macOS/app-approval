from flask import Flask, abort, render_template, request
from validation import valid_uuid, valid_uun
from jssrequest import JSSRequest
from jsstools import JSSTools
from dateutil import parser
import random 
import pprint
import traceback

app = Flask(__name__, template_folder='/usr/share/jssapproval/templates')

api1_base = '/appreq/api/v1.0/'
ui1_base = '/request/'

@app.route(ui1_base)
def homepage():
    return render_template('index.html')

@app.route(ui1_base + "<string:uun>/<string:uuid>/view", methods=['GET'])
def landing(uun, uuid):
    if valid_uuid(uuid) and valid_uun(uun):
        try:
            try: 
                current_user = request.environ['REMOTE_USER']
            except KeyError:
                current_user = 'unknown' 
            req = JSSRequest(uuid, uun)
            print "about to try to template... " + current_user
            req.attributes['approver'] = current_user
            return render_template('landing.html', **req.attributes)
        except Exception as ex:
            return render_template('error.html', error='Couldn\'t load request. {}: {}\n{}'.format(type(ex).__name__, str(ex), traceback.print_exc()))
    else:
        return render_template('error.html', error='Invalid UUID or Username')


@app.route(ui1_base + "<string:uun>/<string:uuid>/process", methods=['POST'])
def process(uun, uuid):
    
    response = request.form['response'] 
    msg = request.form['message'] or 'Denied'

    req = JSSRequest(uuid, uun)

    try:
        current_user = request.environ['REMOTE_USER']
    except KeyError:
        current_user = 'unknown' 
    
    try:
        if response == 'approve':
            req.approve(approver=current_user)
            return render_template('success.html', message="Request was successfully approved by " + current_user)
        elif response == 'deny':
            req.deny(reason=msg, approver=current_user)       
            return render_template('success.html', message="Request was successfully denied by " + current_user)
        else:
            abort(400) # Unknown action.
  
    except Exception as ex:
        return render_template('error.html', error='Failed to process request. {}: {}'.format(type(ex).__name__, str(ex)))

@app.route(ui1_base + "<string:uun>/list")
@app.route(ui1_base + "<string:uun>/list/<string:status>")
def list_requests(uun, status=None):
    if valid_uun(uun):
        try:
            tools = JSSTools()
            requests = tools.get_user_requests_uun(uun)
            if status:
                if status.lower() in ['approved', 'pending','denied']:
                    requests = [r for r in requests if r['status'].lower() == status.lower()]
            return render_template('request_list.html', UUN=uun, requests=requests)
        except Exception as ex:
            return render_template('error.html', error='No requests found for {}: {} {}\n{}'.format(uun, type(ex).__name__, str(ex), traceback.print_exc()))
    else:
        return render_template('error.html', error='Invalid UUID or Username')

@app.context_processor
def utility_processor():
    def format_date(datestring):
        date = parser.parse(datestring)
        return date.strftime("%d-%m-%Y %H:%M")
    return dict(format_date=format_date)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
