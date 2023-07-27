import jwt
import os
import datetime
from flask import json, Response, request, g
from functools import wraps
from ..models.PatientRegistrationModel import PatientRegistrationModel
from ..models.DoctorModel import DoctorModel
from ..models.PatientRecordsModel import PatientRecordsModel
from ..models.MedicineModel import MedicineModel

class Auth():
  """
  Auth Class
  """
  @staticmethod
  def generate_token_patient(user_id):
    """
    Generate Token Method
    """
    try:
      payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id,
        'iss': 'patient'
      }
      return jwt.encode(
        payload,
        os.getenv('PATIENT_SECRET_KEY'),
        'HS256'
      ).decode("utf-8")
    except Exception as e:
      return Response(
        mimetype="application/json",
        response=json.dumps({'error': 'error in generating patient token'}),
        status=400
      )
    
  @staticmethod
  def generate_token_doctor(user_id):
    """
    Generate Token Method
    """
    try:
      payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id,
        'iss':'doctor'
      }
      return jwt.encode(
        payload,
        os.getenv('DOCTOR_SECRET_KEY'),
        'HS256'
      ).decode("utf-8")
    except Exception as e:
      return Response(
        mimetype="application/json",
        response=json.dumps({'error': 'error in generating doctor token'}),
        status=400
      )

  @staticmethod
  def decode_token_patient(token):
    """
    Decode Token Method
    """
    re = {'data': {}, 'error': {}}
    try:
      payload = jwt.decode(token, os.getenv('PATIENT_SECRET_KEY'))
      re['data'] = {'user_id': payload['sub']}
      return re
    except jwt.ExpiredSignatureError as e1:
      re['error'] = {'message': 'token expired, please login again'}
      return re
    except jwt.InvalidTokenError:
      re['error'] = {'message': 'Invalid token, please try again with a new token'}
      return re
  

  @staticmethod
  def decode_token_doctor(token):
    """
    Decode Token Method
    """
    re = {'data': {}, 'error': {}}
    try:
      payload = jwt.decode(token, os.getenv('DOCTOR_SECRET_KEY'))
      re['data'] = {'user_id': payload['sub']}
      return re
    except jwt.ExpiredSignatureError as e1:
      re['error'] = {'message': 'token expired, please login again'}
      return re
    except jwt.InvalidTokenError:
      re['error'] = {'message': 'Invalid token, please try again with a new token'}
      return re


  @staticmethod
  def find_patient(token):
    """
    Find Patient or Doctor
    """
    re = {'data': {}, 'error': {}}
    try:
      payload = jwt.decode(token, os.getenv('PATIENT_SECRET_KEY'))
      re['data'] = {'account_type': payload['iss']}
      if re['data']['account_type'] == 'patient':
        return 1
      else:
        return 0
    except jwt.ExpiredSignatureError as e1:
      re['error'] = {'message': 'token expired, please login again'}
      return re
    except jwt.InvalidTokenError:
      re['error'] = {'message': 'Invalid token, please try again with a new token'}
      return re
  
  @staticmethod
  def find_doctor(token):
    """
    Find Patient or Doctor
    """
    re = {'data': {}, 'error': {}}
    try:
      payload = jwt.decode(token, os.getenv('DOCTOR_SECRET_KEY'))
      re['data'] = {'account_type': payload['iss']}
      if re['data']['account_type'] == 'doctor':
        return 1
      else:
        return 0
    except jwt.ExpiredSignatureError as e1:
      re['error'] = {'message': 'token expired, please login again'}
      return re
    except jwt.InvalidTokenError:
      re['error'] = {'message': 'Invalid token, please try again with a new token'}
      return re




  @staticmethod
  def auth_required_patient(func):
    """
    Auth Decorator
    """
    @wraps(func)
    def decorated_auth(*args, **kwargs):
      if 'api-token' not in request.headers:
        return Response(
          mimetype="application/json",
          response=json.dumps({'error': 'Authentication token is not available, please login to get one'}),
          status=400
        )

      token = request.headers.get('api-token')
      data = Auth.decode_token_patient(token)
      if data['error']:
        return Response(
          mimetype="application/json",
          response=json.dumps(data['error']),
          status=400
        )
        
      user_id = data['data']['user_id']
      check_user = PatientRegistrationModel.get_one_user(user_id)
      if not check_user:
        return Response(
          mimetype="application/json",
          response=json.dumps({'error': 'user does not exist, invalid token'}),
          status=400
        )
      g.user = {'id': user_id}
      return func(*args, **kwargs)
    return decorated_auth
  

  @staticmethod
  def auth_required_doctor(func):
    """
    Auth Decorator
    """
    @wraps(func)
    def decorated_auth(*args, **kwargs):
      if 'dapi-token' not in request.headers:
        return Response(
          mimetype="application/json",
          response=json.dumps({'error': 'Authentication token is not available, please login to get one'}),
          status=400
        )
      if request.headers.get('dapi-token'):
        token = request.headers.get('dapi-token')
        data = Auth.decode_token_doctor(token)
        if data['error']:
          return Response(
            mimetype="application/json",
            response=json.dumps(data['error']),
            status=400
          )
        user_id = data['data']['user_id']
        check_user = DoctorModel.get_one_user(user_id)
        if not check_user:
          return Response(
          mimetype="application/json",
          response=json.dumps({'error': 'doctor does not exist, invalid token'}),
          status=400
        )
        g.user = {'id': user_id}
        return func(*args, **kwargs)
    return decorated_auth


