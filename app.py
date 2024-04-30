import os
import pickle
from http import HTTPStatus
from flask import Flask, request, jsonify, redirect, url_for, abort, session
from flask_cors import CORS
from db import Database  # Assuming you have a separate module for database operations
from config import DevelopmentConfig as devconf
from flask_bcrypt import Bcrypt 

host = os.environ.get('FLASK_SERVER_HOST', devconf.HOST)
port = os.environ.get('FLASK_SERVER_PORT', devconf.PORT)
version = str(devconf.VERSION).lower()
url_prefix = str(devconf.URL_PREFIX).lower()
route_prefix = f"/{url_prefix}/{version}"

def create_app():
    app = Flask(__name__)
    cors = CORS(app, resources={f"{route_prefix}/*": {"origins": "*"}})
    app.config.from_object(devconf)
    return app

app = create_app()
app.secret_key = 'abcdefghijklmnopqrstuvwxyz'
db = Database(devconf)
bcrypt = Bcrypt(app) 

def prediction(lst):
    filename = 'model/model.pickle'
    with open(filename, 'rb') as file:
        model = pickle.load(file)
    pred_value = model.predict([lst])
    return pred_value


def get_response_msg(data, status_code):
    message = {'status': status_code, 'data': data if data else 'No records found'}
    response_msg = jsonify(message)
    response_msg.status_code = status_code
    return response_msg

def prediction(lst):
    filename = 'model/model.pickle'
    with open(filename, 'rb') as file:
        model = pickle.load(file)
    pred_value = model.predict([lst])
    return pred_value

@app.route(f"{route_prefix}/user", methods=['POST'])
def insert_user():
    data = request.get_json()
    try:
        _email = data['email']
        _phone_number = data['phone_number']
        _password = data['password']
        _hashed_password = bcrypt.generate_password_hash(_password).decode('utf-8')

        sql = "INSERT INTO user(email, phone_number,password) VALUES ('%s', '%s', '%s')"
        data = ( _email,_phone_number, _hashed_password)

        db.run_query(query=sql % data)
        db.close_connection()

        return jsonify({"message": "User inserted successfully"}), HTTPStatus.CREATED
    except Exception as e:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(e))

@app.route(f"{route_prefix}/login", methods=['POST'])
def login():
    data = request.get_json()
    try:
        _email = data['email']
        _password = data['password']

        sql = "SELECT * FROM user WHERE email = '%s'"
        data = ( _email)

        records = db.run_query(query=sql % data)

        db.close_connection()

        if bcrypt.check_password_hash(records[0][3],_password):
            session['loggedin'] = True
            session['user_id'] = records[0][0]
            return jsonify({"user_id": records[0][0]})
        else:
            return jsonify({"result": 'fail'})

    except Exception as e:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(e))


@app.route(f"{route_prefix}/user-inputs-last", methods=['get'])
def user_inputs_last():
    try:
        user_id = session.get('user_id')
        sql = f"SELECT * FROM user_input WHERE user_id ='{user_id}' ORDER BY id DESC LIMIT 1"
        records = db.run_query(query=sql)
        db.close_connection()
        response = get_response_msg(records, HTTPStatus.OK)
        return response

    except Exception as e:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(e))


@app.route(f"{route_prefix}/user-inputs", methods=['POST'])
def insert_user_data():
    data = request.get_json()
    if session.get('loggedin') == False:
        return jsonify({"message": 'You are not logged in'})
    try:
        _age= data['age']
        _SB = data['systolic_bp']
        _DB= data['diastolic_bp']
        _BS = data['BS']
        _BT = data['BT']
        _HR = data['HR']  
        _checkup_for= data['checkup_for']
        _consult_med_prof = data['consult_med_prof']
        _care_planned = data['care_planned']
        _regions = data['regions']
        _recent_injury = data['recent_injury']
        _smoking_duration = data['smoking_duration']
        _allergic_history = data['allergic_history']
        _pregnant = data['pregnant']
        _hypertension = data['hypertension']
        _weight = data['weight']
        _result = data['result']
        # _user_id = data['user_id']
        _user_id = session.get('user_id')

        pred = prediction([float(_age), float(_SB), float(_DB), float(_BS), float(_BT), float(_HR) ])
        predResult = pred.tolist()
        
        sql = "INSERT INTO user_input(user_id,checkup_for, consult_med_prof,care_planned,regions,recent_injury,smoking_duration,allergic_history,pregnant,hypertension,weight,Age,SB,DB,BS,BT,HR,result) VALUES ('%s','%s', '%s', '%s','%s', '%s', '%s','%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s')"
        data = (_user_id,_checkup_for,_consult_med_prof, _care_planned,_regions,_recent_injury ,_smoking_duration,_allergic_history,_pregnant,_hypertension,_weight,_age,_SB,_DB,_BS,_BT, _HR,predResult[0]) # type: ignore
        

        # return jsonify({"message":sql % data })
        db.run_query(query=sql % data)
        
        db.close_connection()

        return jsonify({"message": "User inserted successfully"}), HTTPStatus.CREATED
    except Exception as e:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(e))

@app.route(f"{route_prefix}/health", methods=['GET'])
def health():
    try:
        db_status = "Connected to DB" if db.db_connection_status else "Not connected to DB"
        response = get_response_msg("I am fine! " + db_status, HTTPStatus.OK)
        return response
    except Exception as e:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, description=str(e))

@app.route(f"{route_prefix}/prediction", methods=['post'])
def predict():
    data = request.get_json()
    _age= float(data['age'])
    _SB = float(data['systolic_bp'])
    _DB= float(data['diastolic_bp'])
    _BS = float(data['BS'])
    _BT = float(data['BT'])
    _HR = float(data['HR'])
    pred = prediction([_age, _SB, _DB, _BS, _BT, _HR ])
    predResult = pred.tolist()
    return jsonify({"prediction" : predResult[0]})

@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('health'))

@app.errorhandler(HTTPStatus.NOT_FOUND)
def page_not_found(e):    
    return get_response_msg(data=str(e), status_code=HTTPStatus.NOT_FOUND)

@app.errorhandler(HTTPStatus.BAD_REQUEST)
def bad_request(e):
    return get_response_msg(str(e), HTTPStatus.BAD_REQUEST)

@app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def internal_server_error(e):
    return get_response_msg(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

if __name__ == '__main__':
    app.run(host=host, port=port)
