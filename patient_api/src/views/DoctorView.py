from flask import request, json, Response, Blueprint, g,jsonify,make_response
from flask_cors import CORS, cross_origin
from ..models.DoctorModel import DoctorModel, DoctorSchema
from ..models.PatientRecordsModel import PatientRecordsModel, PatientRecordsSchema
from ..models.AddDoctorModel import AddDoctorSchema,AddDoctorModel
from ..shared.Authentication import Auth
from flask_mail import Message
from random import randint
from werkzeug.utils import secure_filename
import pyrebase
import math

import datetime
import pytz
import secrets
import hashlib
from nested_lookup import nested_delete
from flask_cors import cross_origin

IST = pytz.timezone("Asia/Kolkata")

doctor_api = Blueprint("doctor_api", __name__)

doctor_schema = DoctorSchema()


config = {
    "apiKey": "AIzaSyAaYfbMWdqFDotoJ4bcuW-I5fxsPuAkjb4",
    "authDomain": "online-health-di.firebaseapp.com",
    "databaseURL": "https://online-health-di.firebaseio.com",
    "projectId": "online-health-di",
    "storageBucket": "online-health-di.appspot.com",
    "messagingSenderId": "1039323266430",
    "appId": "1:1039323266430:web:52779145563fe1351fc72f",
    "measurementId": "G-N1N2CMKCQM"
}

firebase = pyrebase.initialize_app(config)

storage = firebase.storage()

otp = None


@doctor_api.route("/", methods=["POST"])
@cross_origin()
def create():
    try:
        global otp
        req = request.form
        req_data = {}
        for key, val in req.items():
            if key != "file":
                req_data[key] = val

        data = doctor_schema.load(req_data)

        doctor_in_db = DoctorModel.get_user_by_email(data.get("email"))

        doctor_in_db_username = AddDoctorModel.admin_provided_username(
            data.get("username"))

        doctor_in_db_ph_no = DoctorModel.get_user_by_ph_no(
            data.get("phone"))

        if doctor_in_db:
            message = {
                "msg": "User already exist, please supply another email address"}
            return custom_response(message, 400)

        if not doctor_in_db_username:
            message = {
                "msg": "Admin provided username is invalid, please contact admin"}
            return custom_response(message, 400)
        
        if doctor_in_db_ph_no:
          
            message = {
                "msg": "Phone number already exist, please supply another number"}
            return custom_response(message, 400)

        upload = request.files["file"]
        storage.child("doctor_images/" +
                      str(req.get("username")) + ".jpg").put(upload)
        links = storage.child("doctor_images/" + str(req.get("username")) + ".jpg").get_url(
            None
        )
        if links:
            data["profile_url"] = links
        
        otp = randint(100000, 999999)
        data['otp'] = otp
        doctor = DoctorModel(data)
        doctor.save()
        doctor_data = doctor_schema.dump(doctor)

        from ..app import Database
        Database.commit()

        message = "Your OTP is " + str(otp)
        from ..app import SendOTP

        SendOTP.send_email(doctor_data.get("email"), message)

        return custom_response(
            {"msg": "Registration successful",
                "username": doctor_data.get("username")}, 201
        )
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to register"}, 400)


@doctor_api.route("/validate/<string:username>", methods=["POST"])
@cross_origin()
def validate(username):
    try:
        new_data = request.get_json()
        user_otp = new_data.get("otp")
        doctor = DoctorModel.get_user_by_username(username)
        doctor_det = doctor_schema.dump(doctor)
        if doctor_det['otp'] == int(user_otp):
            doctor.update({"verified": "1"})
            from ..app import Database
            Database.commit()
            doctor_data = doctor_schema.dump(doctor)
            token = Auth.generate_token_doctor(doctor_data.get("id"))
            return custom_response(
                {
                    "msg": "Registration successful",
                    "jwt_token": token,
                    "username": doctor_data.get("username"),
                    "name": doctor_data.get("name"),
                    "email": doctor_data.get("email"),
                    "phone": doctor_data.get("phone"),
                    "profile_url": doctor_data.get("profile_url"),
                    "experience": doctor_data.get("experience"),
                    "speciality": doctor_data.get("speciality"),
                },
                200,
            )
        else:
            return custom_response({"msg": "Invalid OTP"}, 401)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Validation failed"}, 400)


@doctor_api.route("/reset", methods=["POST"])
@cross_origin()
def reset():
    try:
        req_data = request.get_json()
        proto = req_data['protocol']
        addr = req_data['host']
        doctor_format = email_format(req_data['email'])
        data = doctor_schema.load(doctor_format, partial=True)
        if not data.get("email"):
            return custom_response({"msg": "you need email to reset password"}, 400)
        doctor = DoctorModel.get_user_by_email(data.get("email"))
        if not doctor:
            return custom_response({"msg": "Email not registered"}, 400)
        doctor_data = doctor_schema.dump(doctor)
        token = secrets.token_hex(16)
        reset_token = hashlib.sha256(token.encode()).hexdigest()
        token_allotment_time = datetime.datetime.utcnow()

        doctor = DoctorModel.get_one_user(doctor_data.get("id"))

        doctor.update({"reset_token": reset_token,
                       "reset_token_exp": token_allotment_time})
        from ..app import Database
        Database.commit()
        doctor_data = doctor_schema.dump(doctor)

        recover_url = str(proto) + "//" + str(addr) +"/doctors/reset"  + "/" + token

        from ..app import PasswordReset

        PasswordReset.send_email(doctor_data.get("email"), recover_url)

        return custom_response({"msg": "Check your email for further process!"}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Failed to send reset link"}, 400)

def email_format(a):
    return{
        "email":a
    }


@doctor_api.route("/reset/<string:token>", methods=["PUT"])
@cross_origin()
def reset_with_token(token):
    try:
        reset_token = hashlib.sha256(token.encode()).hexdigest()
        doctor = DoctorModel.get_user_by_reset_token(reset_token)
        if not doctor:
            return custom_response({"msg": "Reset link revoked, please request again"}, 400)
        datetimeFormat = "%Y-%m-%d %H:%M:%S"
        curr_time = datetime.datetime.utcnow().strftime(datetimeFormat)
        doctor_data = doctor_schema.dump(doctor)
        token_time = doctor_data.get("reset_token_exp")
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
        data = doctor_schema.load(req_data, partial=True)
        doctor.update(
            {"password": data.get("password"),
             "reset_token_exp": None, "reset_token": None}
        )
        from ..app import Database
        Database.commit()
        doctor_user = doctor_schema.dump(doctor)
        return custom_response(
            {"user": doctor_user, "msg": "Your password has been reset successfully!"}, 200
        )
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to reset password"}, 400)


@doctor_api.route("/", methods=["GET"])
@cross_origin()
def get_all():
    """
    Get All Users
    """
    try:
        doctor = DoctorModel.get_all_users()
        doctor_data = doctor_schema.dump(doctor, many=True)
        det = []
        for d in doctor_data:
            c_fee = d["consultation_fee"]
            fee = c_fee + (c_fee * 30) / 100
            if c_fee < 500:
                c_credit = (fee * 50) / 100
            else:
                c_credit = (fee * 40) / 100 + ((fee - 500) * 10) / 100
            c_credit = math.ceil(c_credit)
            if d['verified']=='1':
                res = doctor_format(
                    d['id'],
                    d['username'],
                    d['name'],
                    d['email'],
                    d['phone'],
                    d['profile_url'],
                    d['experience'],
                    d['speciality'],
                    c_credit,
                    d['rating'],
                )
                det.append(res)
        return custom_response(det, 200)
    except Exception as e:
        return custom_response({"msg": "Unable to get all doctors"}, 400)


def doctor_format(a, b, c, d, e, f, g, h, i, j):
    return {
        "id": a,
        "username": b,
        "name": c,
        "email": d,
        "phone": e,
        "profile_url": f,
        "experience": g,
        "speciality": h,
        "consulation_fee": i,
        "rating": j
    }


@doctor_api.route("/me", methods=["PUT"])
@cross_origin()
@Auth.auth_required_doctor
def update():
    try:
        upload = ""
        if request.files:
            upload = request.files["file"]
        links = None
        doctor = DoctorModel.get_one_user(g.user.get("id"))
        if upload != "":
            storage.child("doctor_images/" +
                          str(g.user.get("id")) + ".jpg").put(upload)
            links = storage.child(
                "doctor_images/" + str(g.user.get("id")) + ".jpg"
            ).get_url(None)
            doctor.update({"profile_url": links})
        else:
            req_data = request.get_json()
            phone_no = req_data['phone']
            doctor_in_db_ph_no = DoctorModel.get_other_user_by_ph_no(phone_no,g.user.get('id'))
            if doctor_in_db_ph_no:
                message = {"msg": "Phone number already exist, please supply another number"}
                return custom_response(message, 400)
            data = doctor_schema.load(req_data, partial=True)
            doctor.update(data)
        from ..app import Database
        Database.commit()
        doctor_user = doctor_schema.dump(doctor)
        returned_user = {
            "name": doctor_user["name"],
            "username": doctor_user["username"],
            "email": doctor_user["email"],
            "experience": doctor_user["experience"],
            "consultation_fee": doctor_user["consultation_fee"],
            "phone": doctor_user["phone"],
            "profile_url": doctor_user["profile_url"],
        }
        return custom_response({"user": returned_user}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to update details"}, 400)

@doctor_api.route("/me", methods=["GET"])
@cross_origin()
@Auth.auth_required_doctor
def get_me():
    """
    Get Me
    """
    try:
        doctor = DoctorModel.get_one_user(g.user.get("id"))
        doctor_user = doctor_schema.dump(doctor)
        returned_user = {
            "name": doctor_user["name"],
            "username": doctor_user["username"],
            "email": doctor_user["email"],
            "experience": doctor_user["experience"],
            "consultation_fee": doctor_user["consultation_fee"],
            "phone": doctor_user["phone"],
            "profile_url": doctor_user["profile_url"],
        }
        return custom_response({"user": returned_user}, 200)
    except Exception as e:
        return custom_response({"msg": "Unable to fetch details"}, 400)


@doctor_api.route("/pat_details", methods=["GET"])
@cross_origin()
@Auth.auth_required_doctor
def get_all_details():
    """
    Query patient details
    """
    try:
        doctor = DoctorModel.get_one_user(g.user.get("id"))
        details = DoctorModel.patient_details(doctor.id)
        det = []
        for doctor, precord, patient in details:
            res = format(
                patient.name,
                patient.age,
                patient.gender,
                precord.temperature,
                precord.symptoms,
                precord.contact,
                precord.difficulty,
                precord.travel,
                precord.disease,
                precord.apply,
                precord.oxy_level,
                patient.email,
                precord.id,
                precord.attended,
                precord.heart_rate,
                precord.room_id,
                precord.meeting_time
            )
            det.append(res)
        return {"details": det}
    except Exception as e:
        return custom_response({"msg": "Unable to get patient record"}, 400)


def format(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p,q):
    return {
        "patient_name": a,
        "age": b,
        "gender": c,
        "temperature": d,
        "symptoms": e,
        "contact_with_others": f,
        "breathing_difficulty": g,
        "past_travel": h,
        "prior_or_current_disease": i,
        "might_be_causing_condition": j,
        "oxygen_level": k,
        "patient_email": l,
        "patient_record_id": m,
        "attended": n,
        "heart_rate": o,
        "room_id": p,
        "meeting_time":q
    }


@doctor_api.route("/login", methods=["POST"])
@cross_origin()
def login():
    """
    User Login Function
    """
    try:
        req_data = request.get_json()
        data = doctor_schema.load(req_data, partial=True)

        if not data.get("email") or not data.get("password"):
            return custom_response({"msg": "you need email and password to sign in"}, 400)
        doctor = DoctorModel.get_user_by_email(data.get("email"))
        if not doctor:
            return custom_response({"msg": "invalid credentials"}, 400)
        if not doctor.check_hash(data.get("password")):
            return custom_response({"msg": "invalid credentials"}, 400)
        doctor_data = doctor_schema.dump(doctor)

        if doctor_data.get("verified") == "1":
            token = Auth.generate_token_doctor(doctor_data.get("id"))
            det = []
            return jsonify(
                {
                    "msg": "Registration successful",
                    "jwt_token": token,
                    "username": doctor_data.get("username"),
                    "name": doctor_data.get("name"),
                    "email": doctor_data.get("email"),
                    "phone": doctor_data.get("phone"),
                    "profile_url": doctor_data.get("profile_url"),
                    "experience": doctor_data.get("experience"),
                    "speciality": doctor_data.get("speciality"),
                }
            )
        else:
            otp = randint(100000, 999999)
            doctor.update({'otp':otp})

            from ..app import Database
            Database.commit()

            message = "Your OTP is " + str(otp)
            from ..app import SendOTP

            SendOTP.send_email(doctor_data.get("email"), message)
            return custom_response(
                {"msg": "unverified",
                    "username": doctor_data.get("username")}, 200
            )
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Login Failed"}, 400)


def login_format(a,b,c,d,e,f,g,h):
    return {
                    "msg": "Registration successful",
                    "jwt_token": a,
                    "username": b,
                    "name": c,
                    "email": d,
                    "phone": e,
                    "profile_url": f,
                    "experience": g,
                    "speciality": h
            }
              
    



@doctor_api.route("/patient_count", methods=["GET"])
@cross_origin()
@Auth.auth_required_doctor
def patient_count():
    """
    Get Total Patients
    """
    try:
        doctor = DoctorModel.get_one_user(g.user.get("id"))
        total = PatientRecordsModel.total_pat_count(doctor.id)
        att = PatientRecordsModel.att_pat_count(doctor.id)
        not_att = total - att
        return {"total": total, "attended": att, "unattended": not_att}
    except Exception as e:
        return custom_response({"msg": "Unable to fetch patient count"}, 400)

@doctor_api.route('/help',methods=['POST'])
@cross_origin()
@Auth.auth_required_doctor
def send_help_email():
    try:
        data = request.get_json()
        doctor_id = g.user.get('id')
        doctor = DoctorModel.get_one_user(doctor_id)
        if not doctor:
            return custom_response({"msg":"Please Login Again"},400)
        doctor_user = doctor_schema.dump(doctor)
        from ..app import SendEmail
        SendEmail.help_email(doctor_user['email'],data['subject'],data['message'])
        return custom_response({"msg":"Your issue has been sent successfully"},200)
    except Exception as e:
        return custom_response({"msg": "Unable to send request"}, 400)

@doctor_api.route('/find/<string:token>')
@cross_origin()
def find(token):
    try:
        from ..shared.Authentication import Auth
        p_account_type = Auth.find_patient(token)
        d_account_type = Auth.find_doctor(token)
        if p_account_type == 1:
            return custom_response({"msg":"patient"},200)
        elif d_account_type == 1:
            return custom_response({"msg":"doctor"},200)
        else:
            return custom_response({"msg":"Invalid Token or Expired Token"},400)
    except Exception as e:
        return custom_response({"msg": "Unable to find patient or doctor"}, 400)


def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )

