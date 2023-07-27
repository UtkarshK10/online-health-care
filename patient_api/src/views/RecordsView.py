from flask import request, g, Blueprint, json, Response
from ..shared.Authentication import Auth
from ..models.PatientRecordsModel import PatientRecordsModel, PatientRecordsSchema
from ..models.DoctorModel import DoctorSchema, DoctorModel
from ..models.PatientRegistrationModel import (
    PatientRegistrationModel,
    PatientRegistrationSchema,
)
from ..models.TransactionModel import TransactionSchema, TransactionModel
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import uuid
import os
import math
from flask_cors import cross_origin

records_api = Blueprint("records_api", __name__)
records_schema = PatientRecordsSchema()
patient_schema = PatientRegistrationSchema()
doctor_schema = DoctorSchema()
transaction_schema = TransactionSchema()

scheduler = BackgroundScheduler({"apscheduler.timezone": "Asia/Calcutta"})
scheduler.start()


@records_api.route("/", methods=["POST"])
@cross_origin()
@Auth.auth_required_patient
def create():
    """
    Create Record
    """
    try:
        user_id = g.user.get("id")

        patient = PatientRegistrationModel.get_one_user(user_id)
        patient_user = patient_schema.dump(patient)
        total_credits = patient_user["total_credit"]
        req_data = request.get_json()
        doctor_id = req_data["doctor_id"]
        doctor = DoctorModel.get_one_user(doctor_id)
        doctor_det = doctor_schema.dump(doctor)
        c_fee = doctor_det["consultation_fee"]
        fee = c_fee + (c_fee * 30) / 100
        if c_fee < 500:
            c_credit = (fee * 50) / 100
        else:
            c_credit = (fee * 40) / 100 + ((fee - 500) * 10) / 100
        c_credit = math.ceil(c_credit)
        if total_credits < c_credit:
            return custom_response(
                {
                    "msg": "You don't have as much credits in your account, please add some to continue"
                },
                400,
            )
        new_credits = total_credits - c_credit
        patient.update({"total_credit": new_credits})
        patient_data = patient_schema.dump(patient)
        amount = c_credit
        done_to = "Booked Appointment"
        trans_data = transaction_format(amount, done_to, user_id)
        transaction = transaction_schema.load(trans_data)
        transaction_det = TransactionModel(transaction)
        transaction_det.save()
        det = transaction_schema.dump(transaction_det)

        req_data["user_id"] = g.user.get("id")
        req_data["transaction_id"] = det["id"]
        data = records_schema.load(req_data)
        post = PatientRecordsModel(data)
        post.save()
        from ..app import Database
        Database.commit()
        data = records_schema.dump(post)
        return custom_response(
            {
                "msg": "Your appointment has been confirmed, further details will be forwarded you via mail!",
                "new_credits": new_credits,
            },
            201,
        )
    except SQLAlchemyError as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Appointment Booking Failed"}, 400)


def transaction_format(a, b, c):
    return {"amount": a, "done_to": b, "patient_id": c}


@records_api.route("/feedback/<int:id>", methods=["PUT"])
@cross_origin()
@Auth.auth_required_patient
def feedback(id):
    try:
        req_data = request.get_json()
        record = PatientRecordsModel.get_one_record(id)
        record_det = records_schema.dump(record)
        if g.user.get("id") != record_det["user_id"]:
            return custom_response({"msg": "Permission Denied"}, 200)
        record.update(req_data)
        doctor_id = record_det['doctor_id']
        doctor = DoctorModel.get_one_user(doctor_id)
        d_rating = PatientRecordsModel.avg_rating(doctor_id)
        d_rating = round(d_rating, 2)
        doctor.update({"rating": d_rating})
        from ..app import Database
        Database.commit()
        f_record = records_schema.dump(record)
        doctor_user = doctor_schema.dump(doctor)
        return custom_response({"msg":"success"}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": e.args}, 400)




@records_api.route("/schedule", methods=["POST"])
@cross_origin()
@Auth.auth_required_doctor
def schedule():
    try:
        data = request.get_json()
        record_id = data['record_id']
        time = data["time"]
        meeting_time = data["meetingTime"]
        room_id = uuid.uuid4().hex
        meeting_url = "https://medico-videocall.herokuapp.com/"+ room_id
        meeting_data = meeting_details_format(meeting_url, room_id, meeting_time)
        record = PatientRecordsModel.get_one_record(record_id)
        record.update(meeting_data)
        from ..app import Database
        Database.commit()
        detailed_record = DoctorModel.record_details(record_id)
        for d,r,p in detailed_record:
            patient_name = p.name
            doctor_name = d.name
        schedule_time = time - 30 * 60 * 1000
        schedule_time = datetime.fromtimestamp(schedule_time / 1000).strftime(
            "%Y-%m-%d %H:%M"
        )
        receiver = data.get("receiver")
        date_time = datetime.strptime(str(schedule_time), "%Y-%m-%d %H:%M")
        message = "Dear "+ patient_name +",\n\n\nWe are writing to confirm your meeting appointment with doctor "+ doctor_name +" on " + meeting_time + ". He will meet you on the video call whose link is provided below.\n\n\nVideo Call Link:\n"+ meeting_url+ "\n\nPlease login with your Medico app's credentials and provide the room id given below.\n\nRoom Id:\n" + room_id+"\n\nRegards,\nMedico Team"
        from ..app import SendEmail

        SendEmail.send_appointment_email(receiver, message)
        msg = "Dear "+ patient_name + ",\n\n\nThis is a special reminder to remind you about your meeting with doctor "+ doctor_name + " today at " + meeting_time + ". He will meet you on the video call whose link is provided below.\n\n\nVideo Call Link:\n"+ meeting_url+ "\n\nPlease login with your Medico app's credentials and provide the room id given below.\n\nRoom Id:\n" + room_id+"\n\nRegards,\nMedico Team"
        schedule_mail(date_time, receiver,msg)
        return custom_response({"msg": time}, 201)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Something Went Wrong"}, 400)


def meeting_details_format(a, b, c):
    return {"meeting_url": a, "room_id": b, "meeting_time": c}


def schedule_mail(date_time, receiver,body):
    job = scheduler.add_job(
        printing_something,
        trigger="date",
        next_run_time=str(date_time),
        args=[receiver,body],
    )


def printing_something(receiver,body):
    from ..app import SendEmail
    SendEmail.send_schedule_email(receiver,body)



@records_api.route("/attended", methods=["PATCH"])
@cross_origin()
@Auth.auth_required_doctor
def update_record():
    """
    Update attended column
    """
    try:
        data = request.get_json()
        record = PatientRecordsModel.get_one_record(data.get("id"))
        record_det = records_schema.dump(record)
        if g.user.get("id") != record_det["doctor_id"]:
            return custom_response({"msg": "Permission Denied"}, 200)
        record.update({"attended": 1})
        from ..app import Database
        Database.commit()
        record_f = records_schema.dump(record)
        return custom_response({"details": record_f}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Something Went Wrong"}, 400)


@records_api.route("/authenticate", methods=["POST"])
@cross_origin()
def authenticate_meet():
    try:
        req_data = request.get_json()
        r_data = login_format(req_data["email"], req_data["password"])
        data = patient_schema.load(r_data, partial=True)
        if not data.get("email") or not data.get("password"):
            return custom_response(
                {"msg": "you need email and password to sign in"}, 400
            )
        patient = PatientRegistrationModel.get_user_by_email(data.get("email"))
        if not patient:
            return custom_response({"msg": "Invalid credentials"}, 400)
        if not patient.check_hash(data.get("password")):
            return custom_response({"msg": "Invalid credentials"}, 400)
        patient_data = patient_schema.dump(patient)
        patient_id = patient_data["id"]
        room_id = req_data["room_id"]
        record = PatientRecordsModel.check_room_id_patient(patient_id, room_id)
        if not record:
            return custom_response({"msg": "Invalid Room Id"}, 400)
        record_det = records_schema.dump(record)
        url = "/" + record_det["meeting_url"].split("/")[3]
        meet = meet_format(url, patient_data["username"])
        return custom_response({"msg": meet}, 200)

    except Exception as e:
        return custom_response({"msg": "Something Went Wrong"}, 400)


def login_format(a, b):
    return {"email": a, "password": b}


def meet_format(a, b):
    return {"meet_url": a, "patient_username": b}


@records_api.route("/authenticate_doctor", methods=["POST"])
@cross_origin()
def authenticate_doctor():
    try:
        req_data = request.get_json()
        r_data = doctor_login_format(req_data["email"], req_data["password"])
        data = doctor_schema.load(r_data, partial=True)
        if not data.get("email") or not data.get("password"):
            return custom_response(
                {"msg": "you need email and password to sign in"}, 400
            )
        doctor = DoctorModel.get_user_by_email(data.get("email"))
        if not doctor:
            return custom_response({"msg": "Invalid credentials"}, 400)
        if not doctor.check_hash(data.get("password")):
            return custom_response({"msg": "Invalid credentials"}, 400)
        doctor_data = doctor_schema.dump(doctor)
        doctor_id = doctor_data["id"]
        record_id = req_data["record_id"]
        record = PatientRecordsModel.get_one_record(record_id)
        if not record:
            return custom_response({"msg": "Invalid Record Id"}, 400)
        record_det = records_schema.dump(record)
        if doctor_id != record_det["doctor_id"]:
            return custom_response({"msg": "Invalid Doctor For This Record"}, 400)
        url = "/" + record_det["meeting_url"].split("/")[3]
        meet = doctor_meet_format(url, doctor_data["username"])
        return custom_response({"msg": meet}, 200)

    except Exception as e:
        print(e.args)
        return custom_response({"msg": "Something Went Wrong"}, 400)


def doctor_login_format(a, b):
    return {"email": a, "password": b}


def doctor_meet_format(a, b):
    return {"meet_url": a, "doctor_username": b}


def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )
