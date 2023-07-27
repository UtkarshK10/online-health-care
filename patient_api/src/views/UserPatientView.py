from flask import (
    Flask,
    request,
    json,
    Response,
    Blueprint,
    g,
    jsonify,
    make_response,
    url_for,
    redirect,
)
import os
from flask_cors import CORS, cross_origin
from flask_mail import Message
from random import randint
from werkzeug.utils import secure_filename

from ..models.PatientRegistrationModel import (
    PatientRegistrationModel,
    PatientRegistrationSchema,
)
from ..models.TransactionModel import TransactionSchema, TransactionModel

from ..shared.Authentication import Auth

import pyrebase
import datetime
import pytz
import secrets
import hashlib
from nested_lookup import nested_delete
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import cross_origin

IST = pytz.timezone("Asia/Kolkata")

patient_config = {
    "apiKey": "AIzaSyDPq3eNI3vfRXXzx6wt0ZlZvOrVIn96yPw",
    "authDomain": "online-health-pi-aef06.firebaseapp.com",
    "databaseURL": "https://online-health-pi-aef06.firebaseio.com",
    "projectId": "online-health-pi-aef06",
    "storageBucket": "online-health-pi-aef06.appspot.com",
    "messagingSenderId": "411004578142",
    "appId": "1:411004578142:web:3ff7c11c5595df7e0407cf",
    "measurementId": "G-05S804B028"
}

config0 = {
    "apiKey": "AIzaSyADC7B1hu1P6yMfc_uuGLXL9dONtzi7O3k",
    "authDomain": "online-health-vi1.firebaseapp.com",
    "databaseURL": "https://online-health-vi1.firebaseio.com",
    "projectId": "online-health-vi1",
    "storageBucket": "online-health-vi1.appspot.com",
    "messagingSenderId": "833844514637",
    "appId": "1:833844514637:web:881d6f66e47d7485f4b104",
    "measurementId": "G-JCKNK3DHG6"
}

config1 = {
    "apiKey": "AIzaSyC9fxftaAnWHaoxTBCVTFDU8b5nncrtfeA",
    "authDomain": "online-health-vi2.firebaseapp.com",
    "databaseURL": "https://online-health-vi2.firebaseio.com",
    "projectId": "online-health-vi2",
    "storageBucket": "online-health-vi2.appspot.com",
    "messagingSenderId": "449992394066",
    "appId": "1:449992394066:web:d8a0eb4ad126dab345668b",
    "measurementId": "G-W22P5MP54J"
}

config2 = {
    "apiKey": "AIzaSyBJd023jwhJ05sSnpYIdukUi84pdyJh0Z4",
    "authDomain": "online-health-vi3.firebaseapp.com",
    "databaseURL": "https://online-health-vi3.firebaseio.com",
    "projectId": "online-health-vi3",
    "storageBucket": "online-health-vi3.appspot.com",
    "messagingSenderId": "548148666762",
    "appId": "1:548148666762:web:6653310359dc52f8f02873",
    "measurementId": "G-PXC4M8NRYC"
}

config3 = {
    "apiKey": "AIzaSyAheElY6t0omnUQHqc4AlgW4ZNCjKW28O0",
    "authDomain": "online-health-vi4.firebaseapp.com",
    "databaseURL": "https://online-health-vi4.firebaseio.com",
    "projectId": "online-health-vi4",
    "storageBucket": "online-health-vi4.appspot.com",
    "messagingSenderId": "56831276146",
    "appId": "1:56831276146:web:f12be507e3c4d69195feeb",
    "measurementId": "G-WZ0MXM9N4Y"
}

config4 = {
    "apiKey": "AIzaSyBkpd9FyYfH9gZfGZK6S6sk9SjAktbQnVU",
    "authDomain": "online-health-vi5.firebaseapp.com",
    "databaseURL": "https://online-health-vi5.firebaseio.com",
    "projectId": "online-health-vi5",
    "storageBucket": "online-health-vi5.appspot.com",
    "messagingSenderId": "353393532596",
    "appId": "1:353393532596:web:b5d9d528ff790d6dcbc1e1",
    "measurementId": "G-239KWQ9WYL"
}


patient_firebase = pyrebase.initialize_app(patient_config)
patient_storage = patient_firebase.storage()


video_firebase0 = pyrebase.initialize_app(config0)
storage0 = video_firebase0.storage()

video_firebase1 = pyrebase.initialize_app(config1)
storage1 = video_firebase1.storage()

video_firebase2 = pyrebase.initialize_app(config2)
storage2 = video_firebase2.storage()

video_firebase3 = pyrebase.initialize_app(config3)
storage3 = video_firebase3.storage()

video_firebase4 = pyrebase.initialize_app(config4)
storage4 = video_firebase4.storage()


patient_api = Blueprint("patient_api", __name__)

patient_schema = PatientRegistrationSchema()
transaction_schema = TransactionSchema()


@patient_api.route("/", methods=["POST"])
@cross_origin()
def create():
    try:
        req_data = request.get_json()
        data = patient_schema.load(req_data)

        patient_in_db = PatientRegistrationModel.get_user_by_email(
            data.get("email"))
        patient_in_db_username = PatientRegistrationModel.get_user_by_username(
            data.get("username")
        )
        patient_in_db_ph_no = PatientRegistrationModel.get_user_by_ph_no(
            data.get("phone")
        )

        if patient_in_db:
            message = {
                "msg": "User already exist, please provide another email address"}
            return custom_response(message, 400)

        if patient_in_db_username:
            message = {
                "msg": "Userame already exist, please provide another username"}
            return custom_response(message, 400)
        
        if patient_in_db_ph_no:
            message = {
                "msg": "Phone number already exist, please provide another phone number"}
            return custom_response(message, 400)

        otp = randint(100000, 999999)
        data['otp'] = otp
        patient = PatientRegistrationModel(data)
        patient.save()
        patient_data = patient_schema.dump(patient)

        from ..app import Database
        Database.commit()

        message = "Your OTP is " + str(otp)
        from ..app import SendOTP

        SendOTP.send_email(patient_data.get("email"), message)

        return custom_response(
            {"msg": "Registration successful",
                "username": patient_data.get("username")}, 201
        )
    except SQLAlchemyError as e:
        from ..app import Database
        Database.rollback()
        msg = "Unable To Register"
        return custom_response({"msg": msg}, 400)


@patient_api.route("/validate/<string:username>", methods=["POST"])
@cross_origin()
def validate(username):
    try:
        new_data = request.get_json()
        user_otp = new_data.get("otp")
        patient = PatientRegistrationModel.get_user_by_username(username)
        patient_det = patient_schema.dump(patient)
        if patient_det['otp'] == int(user_otp):
            patient.update({"verified": "1"})
            from ..app import Database
            Database.commit()
            patient_data = patient_schema.dump(patient)
            token = Auth.generate_token_patient(patient_data.get("id"))
            return custom_response(
                {
                    "msg": "Verification successful",
                    "jwt_token": token,
                    "username": patient_data.get("username"),
                    "name": patient_data.get("name"),
                    "email": patient_data.get("email"),
                    "phone": patient_data.get("phone"),
                    "gender": patient_data.get("gender"),
                    "age": patient_data.get("age"),
                    "total_credit": patient_data.get("total_credit"),
                    "profile_url": patient_data.get("profile_url"),
                },
                200,
            )
        else:
            return custom_response({"msg": "Invalid OTP"}, 401)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Validation Failed"}, 400)


@patient_api.route("/payment", methods=["PUT"])
@cross_origin()
@Auth.auth_required_patient
def updateCredits():
    try:
        patient_id = g.user.get("id")
        patient = PatientRegistrationModel.get_one_user(patient_id)
        if not patient:
            return custom_response(
                {"msg": "Please provide correct authetication details"}, 401
            )
        patient_user = patient_schema.dump(patient)
        data = request.get_json()
        payload = data["credit"]
        credits = patient_user.get("total_credit")
        cre = (payload * 40) / 100 + ((payload - 500) * 10) / 100
        credits += cre
        patient.update({"total_credit": credits})
        patient_schema.dump(patient)

        amount = cre
        done_to = "Bought Credits For \u20B9 " + str(payload)
        req_data = transaction_format(amount, done_to, patient_id)
        transaction = transaction_schema.load(req_data)
        transaction_det = TransactionModel(transaction)
        transaction_det.save()
        from ..app import Database
        Database.commit()
        det = transaction_schema.dump(transaction_det)

        return custom_response(
            {"msg": "Success! credits added to your account",
                "new_credits": credits}, 200
        )
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Payment Failed"}, 400)


def transaction_format(a, b, c):
    return {"amount": a, "done_to": b, "patient_id": c}


@patient_api.route("/me", methods=["PUT"])
@cross_origin()
@Auth.auth_required_patient
def update():
    try:
        upload = ""
        if request.files:
            upload = request.files["file"]
        links = None
        patient = PatientRegistrationModel.get_one_user(g.user.get("id"))
        if upload != "":
            patient_storage.child("patient_images/" +
                                  str(g.user.get("id")) + ".jpg").put(upload)
            links = patient_storage.child(
                "patient_images/" + str(g.user.get("id")) + ".jpg"
            ).get_url(None)
            patient.update({"profile_url": links})
        else:
            req_data = request.get_json()
            phone_no = req_data['phone']
            patient_in_db_ph_no = PatientRegistrationModel.get_other_user_by_ph_no(phone_no,g.user.get('id'))
            if patient_in_db_ph_no:
                message = {"msg": "Phone number already exist, please provide another phone number"}
                return custom_response(message, 400)
            data = patient_schema.load(req_data, partial=True)
            patient.update(data)
        from ..app import Database
        Database.commit()
        patient_user = patient_schema.dump(patient)
        returned_user = {
            "name": patient_user["name"],
            "username": patient_user["username"],
            "email": patient_user["email"],
            "age": patient_user["age"],
            "gender": patient_user["gender"],
            "phone": patient_user["phone"],
            "profile_url": patient_user["profile_url"],
        }
        return custom_response({"user": returned_user}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to update details"}, 400)


@patient_api.route("/me", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def get_me():
    try:
        patient = PatientRegistrationModel.get_one_user(g.user.get("id"))
        patient_user = patient_schema.dump(patient)
        returned_user = {
            "name": patient_user["name"],
            "username": patient_user["username"],
            "email": patient_user["email"],
            "age": patient_user["age"],
            "gender": patient_user["gender"],
            "phone": patient_user["phone"],
            "profile_url": patient_user["profile_url"],
        }
        return custom_response({"user": returned_user}, 200)
    except Exception as e:
        return custom_response({"msg": "Unable to fetch details"}, 400)


@patient_api.route("/upload", methods=["POST"])
@cross_origin()
@Auth.auth_required_patient
def uploadVideo():
    try:
        patient_id = g.user.get('id')
        from ..app import UploadFile

        file = request.files["file"]
        if patient_id % 5 == 1:
            storage1.child("videos/" + str(g.user.get("id")) +
                           ".mp4").put(file)

            links = storage1.child(
                "videos/" + str(g.user.get("id")) + ".mp4").get_url(None)
        elif patient_id % 5 == 2:
            storage2.child("videos/" + str(g.user.get("id")) +
                           ".mp4").put(file)

            links = storage2.child(
                "videos/" + str(g.user.get("id")) + ".mp4").get_url(None)
        elif patient_id % 5 == 3:
            storage3.child("videos/" + str(g.user.get("id")) +
                           ".mp4").put(file)

            links = storage3.child(
                "videos/" + str(g.user.get("id")) + ".mp4").get_url(None)
        elif patient_id % 5 == 4:
            storage4.child("videos/" + str(g.user.get("id")) +
                           ".mp4").put(file)

            links = storage4.child(
                "videos/" + str(g.user.get("id")) + ".mp4").get_url(None)
        else:
            storage0.child("videos/" + str(g.user.get("id")) +
                           ".mp4").put(file)

            links = storage0.child(
                "videos/" + str(g.user.get("id")) + ".mp4").get_url(None)

        data = UploadFile.spo2(links)
        h_data = UploadFile.heart_rate(links)
        if data == False or h_data == False:
            return custom_response({"msg":"Video Length Should Be Between 20 To 30 Secs."},400)
        return custom_response({"spo2": data, "heart_rate": h_data}, 200)
    except Exception as e:
        return custom_response({"msg": "Unable to upload video"}, 400)


@patient_api.route("/reset", methods=["POST"])
@cross_origin()
def reset():
    try:
        req_data = request.get_json()
        proto = req_data['protocol']
        addr = req_data['host']
        patient_format = email_format(req_data['email'])
        data = patient_schema.load(patient_format, partial=True)
        if not data.get("email"):
            return custom_response({"msg": "you need email to reset password"}, 400)
        patient = PatientRegistrationModel.get_user_by_email(data.get("email"))
        if not patient:
            return custom_response({"msg": "Email not registered"}, 400)
        patient_data = patient_schema.dump(patient)
        token = secrets.token_hex(16)
        reset_token = hashlib.sha256(token.encode()).hexdigest()
        token_allotment_time = datetime.datetime.utcnow()
        patient = PatientRegistrationModel.get_one_user(patient_data.get("id"))

        patient.update(
            {"reset_token": reset_token, "reset_token_exp": token_allotment_time}
        )
        from ..app import Database
        Database.commit()
        patient_data = patient_schema.dump(patient)
        
        recover_url = str(proto) + "//" + str(addr) + "/reset"  + "/" + token
        print("Recover Url",recover_url)
        from ..app import PasswordReset
        print("Before Sending Password Reset Email")
        print("Printing Pemail")
        pemail = patient_data.get("email")
        print(pemail)
        PasswordReset.send_email(pemail, recover_url)
        print("Hello Mini")
        return custom_response({"msg": "Check your email for further process!"}, 200)
    except Exception as e:
        print(e)
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to send reset link"}, 400)

def email_format(a):
    return{
        "email":a
    }

@patient_api.route("/reset/<string:token>", methods=["PUT"])
@cross_origin()
def reset_with_token(token):
    try:
        reset_token = hashlib.sha256(token.encode()).hexdigest()
        patient = PatientRegistrationModel.get_user_by_reset_token(reset_token)
        if not patient:
            return custom_response({"msg": "Reset link revoked, please request again"}, 400)
        datetimeFormat = "%Y-%m-%d %H:%M:%S"
        curr_time = datetime.datetime.utcnow().strftime(datetimeFormat)
        patient_data = patient_schema.dump(patient)
        token_time = patient_data.get("reset_token_exp")
        token_time_arr = str(token_time).split("T")
        token_time = token_time_arr[0] + " " + token_time_arr[1]
        token_time_arr1 = token_time.split(".")
        token_time = token_time_arr1[0]
        diff = datetime.datetime.strptime(
            str(curr_time), datetimeFormat
        ) - datetime.datetime.strptime(str(token_time), datetimeFormat)

        if diff.seconds / 60 > 30:
            return custom_response({"msg": "Token Expired"}, 400)
        req_data = request.get_json()
        data = patient_schema.load(req_data, partial=True)
        patient.update(
            {"password": data.get("password"),
             "reset_token_exp": None, "reset_token": None}
        )
        from ..app import Database
        Database.commit()
        patient_user = patient_schema.dump(patient)
        return custom_response(
            {"user": patient_user, "msg": "Your password has been reset successfully!"}, 200
        )
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to update password"}, 400)


@patient_api.route("/login", methods=["POST"])
@cross_origin()
def login():
    """
    User Login Function
    """
    try:
        req_data = request.get_json()
        data = patient_schema.load(req_data, partial=True)
        if not data.get("email") or not data.get("password"):
            return custom_response({"msg": "you need email and password to sign in"}, 400)
        patient = PatientRegistrationModel.get_user_by_email(data.get("email"))
        if not patient:
            return custom_response({"msg": "Invalid credentials"}, 400)
        if not patient.check_hash(data.get("password")):
            return custom_response({"msg": "Invalid credentials"}, 400)
        patient_data = patient_schema.dump(patient)
        if patient_data.get("verified") == "1":
            token = Auth.generate_token_patient(patient_data.get("id"))
            return custom_response(
                {
                    "msg": "Login successful",
                    "jwt_token": token,
                    "username": patient_data.get("username"),
                    "name": patient_data.get("name"),
                    "email": patient_data.get("email"),
                    "phone": patient_data.get("phone"),
                    "gender": patient_data.get("gender"),
                    "age": patient_data.get("age"),
                    "total_credit": patient_data.get("total_credit"),
                    "profile_url": patient_data.get("profile_url"),
                },
                200,
            )
        else:
            otp = randint(100000, 999999)
            patient.update({'otp':otp})
            from ..app import Database
            Database.commit() 
            message = "Your OTP is " + str(otp)
            from ..app import SendOTP

            SendOTP.send_email(patient_data.get("email"), message)
            return custom_response(
                {"msg": "unverified", "username": patient_data.get("username")}, 200
            )
    except Exception as e:
        from ..app import Database
        Database.rollback() 
        return custom_response({"msg": "Login Unsuccessful"}, 400)

@patient_api.route('/help',methods=['POST'])
@cross_origin()
@Auth.auth_required_patient
def send_help_email():
    try:
        data = request.get_json()
        patient_id = g.user.get('id')
        patient = PatientRegistrationModel.get_one_user(patient_id)
        if not patient:
            return custom_response({"msg":"Please Login Again"},400)
        patient_user = patient_schema.dump(patient)
        from ..app import SendEmail
        SendEmail.help_email(patient_user['email'],data['subject'],data['message'])
        return custom_response({"msg":"Your issue has been sent successfully"},200)
    except Exception as e:
        return custom_response({"msg": "Sorry, issue was not sent successfully"}, 400)

def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )
