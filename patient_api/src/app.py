from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    send_from_directory,
)
import os
import io
import cv2
from cv2 import error
import numpy as np
import time
from scipy import fftpack
from flask_cors import CORS
from .config import app_config
from .models import db, bcrypt
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from .views.UserPatientView import patient_api as user_blueprint
from .views.RecordsView import records_api as records_blueprint
from .views.DoctorView import doctor_api as doctor_blueprint
from .views.MedicinesView import medicines_api as medicines_blueprint
from .views.CartView import cart_api as cart_blueprint
from .views.AdminView import admin_api as admin_blueprint
from .views.OrderView import orders_api as orders_blueprint
from .views.AddressView import address_api as address_blueprint
from .views.PrescriptionView import prescription_api as prescription_blueprint
from .views.TransactionView import transaction_api as transaction_blueprint
from .views.UserPatientView import custom_response


mail = None
extensions = None
app = None


def create_app(env_name):
    """
    Create App
    """
    global mail
    global app
    global extensions

   
    app = Flask(__name__)
    
    app.config.from_object(app_config[env_name])
    mail = Mail(app)

  
    bcrypt.init_app(app)
    db.init_app(app)
    CORS(app.register_blueprint(user_blueprint, url_prefix="/api/users"))
    CORS(app.register_blueprint(records_blueprint, url_prefix="/api/records"))
    CORS(app.register_blueprint(doctor_blueprint, url_prefix="/api/doctors"))
    CORS(app.register_blueprint(medicines_blueprint, url_prefix="/api/medicines"))
    CORS(app.register_blueprint(cart_blueprint, url_prefix="/api/cart"))
    CORS(app.register_blueprint(admin_blueprint, url_prefix="/api/admin"))
    CORS(app.register_blueprint(orders_blueprint, url_prefix="/api/orders"))
    CORS(app.register_blueprint(address_blueprint, url_prefix="/api/address"))
    CORS(app.register_blueprint(prescription_blueprint,
                           url_prefix="/api/prescriptions"))
    CORS(app.register_blueprint(transaction_blueprint,
                           url_prefix="/api/transactions"))

    @app.before_first_request
    def create_tables():
        db.create_all()

    @app.route("/", methods=["GET"])
    def index():
        """
        Example Endpoint
        """
        return "Congratulations! Your First Endpoint Is Working"

    return app


class SendOTP:
    @classmethod
    def send_email(cls, receiver, message):
        msg = Message(
            subject="OTP", sender=os.getenv('MAIL_USERNAME'), recipients=[receiver]
        )
        msg.body = message
        mail.send(msg)


class SendEmail:

    @classmethod
    def send_schedule_email(cls, receiver,body):
        with app.app_context():
            msg = Message(
                "Appointment Reminder",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[receiver],
            )
            msg.body = body
            mail.send(msg)
            

    @classmethod
    def send_appointment_email(cls, receiver, message):
        msg = Message(
            subject="Appointment Confirmed",
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[receiver],
        )
        msg.body = message
        mail.send(msg)

    @classmethod
    def send_email(cls, receiver, subject, message):
        msg = Message(
            subject=subject, sender=os.getenv('MAIL_USERNAME'), recipients=[receiver]
        )
        msg.body = message
        mail.send(msg)
    
    @classmethod
    def help_email(cls,user_email,subject, message):
        msg = Message(
            subject=subject, sender=os.getenv('MAIL_USERNAME'), recipients=[os.getenv('HELP_MAIL_USERNAME')]
        )
        msg.body = "Sent by: "+ user_email + " :- " + "\n" + message
        mail.send(msg)


class PasswordReset:
    @classmethod
    def send_email(cls, receiver, message):
        print("Inside Send mail")
        msg = Message(
            subject="Reset Password Link",
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[receiver],
        )
        msg.body = "Password reset link"
        msg.html = message
        print("Before Sending Mail")
        mail_datatype = mail.send(msg)
        print("Mail Datatype",mail_datatype)
        print("Completed Send mail")

class UploadFile:

    @classmethod
    def spo2(cls, filename):
        video_capture = cv2.VideoCapture(filename)
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        if duration < 20 or duration > 30:
            return False
        count = 0
        arr = []
        arr1 = []
        while True:
            _, frame = video_capture.read()
            if frame is None:
                break
            frame = cv2.resize(frame, (320, 240))
            mean_red = np.mean(frame[:, :, 2])
            mean_blue = np.mean(frame[:, :, 0])
            std_red = np.std(frame[:, :, 2])
            std_blue = np.std(frame[:, :, 0])
            red = std_red / mean_red
            blue = std_blue / mean_blue
            sp_level = 100 - 5 * (red / blue)
            arr.append(sp_level)
            count = count + 1
            if count == 600:
                break
        video_capture.release()
        cv2.destroyAllWindows()
        return np.mean(arr)


    @classmethod
    def heart_rate(cls, filename):
        try:
            cap = cv2.VideoCapture(filename)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            if duration < 20 or duration > 30:
                return False
            heartbeat_count = 128
            heartbeat_values = [0] * heartbeat_count
            det = []
            while True:
                ret, frame = cap.read()
                if frame is None:
                    break
                frame = cv2.resize(frame, (320, 240))
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                heartbeat_values = heartbeat_values[1:] + [np.mean(img)]
                det.append(heartbeat_values)
            cap.release()
            cv2.destroyAllWindows()
            flat_list = []
            for sublist in det:
                for item in sublist:
                    if item > 0:
                        flat_list.append(item)
            result = sum(flat_list) / len(flat_list)
            return result
        except Exception as e:
            return 'Inside Exception'

class Database:

    @classmethod
    def commit(cls):
        db.session.commit()

    @classmethod
    def rollback(cls):
        db.session.rollback()
