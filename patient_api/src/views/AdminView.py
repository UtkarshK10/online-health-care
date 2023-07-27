from flask import request, g, Blueprint, json, Response,render_template,session,redirect,url_for,flash
from ..shared.Authentication import Auth
from ..models.MedicineModel import MedicineModel,MedicineSchema
from ..models.PatientRegistrationModel import PatientRegistrationModel,PatientRegistrationSchema
from ..models.AddDoctorModel import AddDoctorModel,AddDoctorSchema
from random import randint
import pyrebase
import os
import datetime
import time
import pytz
import tzlocal



from werkzeug.utils import secure_filename

config = {
    "apiKey": "AIzaSyDH7AJCJ-x5NBn4OQGAn7XdWljX5-Pb2rw",
    "authDomain": "online-health-mi.firebaseapp.com",
    "databaseURL": "https://online-health-mi.firebaseio.com",
    "projectId": "online-health-mi",
    "storageBucket": "online-health-mi.appspot.com",
    "messagingSenderId": "487529763081",
    "appId": "1:487529763081:web:0c3a3e010f8b284a4543d8",
    "measurementId": "G-7HQTKCR7LB"
}

firebase = pyrebase.initialize_app(config)

storage = firebase.storage()

admin_api = Blueprint("admin_api", __name__)

medicines_schema = MedicineSchema()
addition_schema = AddDoctorSchema()
otp = None

@admin_api.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('admin_api.get_all_medicines'))
    return render_template('index.html')

@admin_api.route("/login",methods=['POST'])
def login():
    try:
        global otp
        email_value = request.form.get('email')
        email_arr = os.getenv('ADMIN_EMAIL')
        if email_value not in email_arr:
            flash('Invalid Email Id','danger')
            return render_template('index.html')
        
        otp = randint(100000, 999999)
        message = "Your OTP is " + str(otp)
        from ..app import SendOTP

        SendOTP.send_email(email_value, message)

        return render_template('otp.html')
    except Exception as e:
        return custom_response({"msg":"Unable to login as Admin."},400)

@admin_api.route("/validate", methods=["POST"])
def validate():
    try:
        user_otp = request.form.get("otp")
        if otp == int(user_otp):
            session['username'] = os.getenv('SECRET_KEY')
            return redirect(url_for('admin_api.get_all_medicines'))
        else:
            flash('Invalid OTP','danger')
            return render_template('otp.html')
    except Exception as e:
        return custom_response({"msg":"Unable to verify Admin's account"},400)

@admin_api.route('/logout')
def logout():
    try:
        session.pop('username', None)
        return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to Logout as Admin"},400)

@admin_api.route('/add_page')
def add_page():
    try:
        if 'username' in session:
            return render_template('add.html')
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to add new Medicine."},400)

@admin_api.route("/add", methods=["POST"])
def add_one_medicine():
    """
    Create Medicine
    """
    try:
        if 'username' in session:
            req = request.form
            req_data = {}
            for key, val in req.items():
                if key != "file":
                    req_data[key] = val
            rating = randint(3 , 5)
            req_data['rating'] = rating
            data = medicines_schema.load(req_data)
            upload = request.files["file"]
            storage.child("medicine_images/" + str(req.get("name")) + ".jpg").put(upload)
            links = storage.child("medicine_images/" + str(req.get("name")) + ".jpg").get_url(None)
            if links:
                data["image_url"] = links
            medicine_block = MedicineModel(data)
            medicine_block.save()
            from ..app import Database
            Database.commit()
            data = medicines_schema.dump(medicine_block)
            flash('New Medicine Added','success')
            return redirect(url_for('admin_api.get_all_medicines'))
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to add new Medicine."},400)
    

@admin_api.route("/show_all", methods=["GET"])
def get_all_medicines():
    """
    Get All Medicines
    """
    try:
        if 'username' in session:
            medicines = MedicineModel.get_all()
            data = medicines_schema.dump(medicines, many=True)
            return render_template('medicine.html',medicine=data)
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to fetch all Medicines"},400)

@admin_api.route('/update_page/<int:id>')
def update_page(id):
    try:
        if 'username' in session:
            medicine_id = id
            return render_template('update.html',medicine_id=medicine_id)
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to update the Medicine"},400)

@admin_api.route("/update", methods=["POST"])
def update_one_medicine():
    """
    Update Medicine
    """
    try:
        if 'username' in session:
            req = request.form
            req_data = {}
            for key, val in req.items():
                req_data[key] = val
            medicine_id = req_data['id']
            medicine = MedicineModel.get_one(medicine_id)
            medicine_det = medicines_schema.dump(medicine)
            stock = medicine_det['stock']
            if req_data['attribute'] == 'stock':
                stock = stock + int(req_data['val'])
                medicine.update({"stock":stock})
            else:
                medicine.update({"price":req_data['val']})
            from ..app import Database
            Database.commit()
            flash('Medicine Updated','success')
            return redirect(url_for('admin_api.get_all_medicines'))
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to update the Medicine"},400)


@admin_api.route("/delete/<int:id>", methods=["GET"])
def delete_one_medicine(id):
    """
    Delete A medicine
    """
    try:
        if 'username' in session:
            medicine = MedicineModel.get_one(id)
            if not medicine:
                return custom_response({"error": "medicine not found"}, 404)
            medicine.update({"status":1})
            medicine_f = medicines_schema.dump(medicine)
            from ..app import Database
            Database.commit()
            return redirect(url_for('admin_api.get_all_medicines'))
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to delete the Medicine"},400)

@admin_api.route('/add_doctor_page')
def add_doctor_page():
    try:
        if 'username' in session:
            return render_template('collab.html')
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to add new Doctor"},400)

@admin_api.route("/add_doctor", methods=["POST"])
def add_doctor():
    """
    Add Doctor
    """
    try:
        if 'username' in session:
            req = request.form
            req_data = {}
            for key, val in req.items():
                    req_data[key] = val
            name = req_data['name']
            exist_name = AddDoctorModel.get_one_by_name(name)
            data = addition_schema.load(req_data)
            doctor = AddDoctorModel(data)
            doctor.save()
            doctor_data = addition_schema.dump(doctor)
            name = doctor_data['name']
            id = doctor_data['id']
            t1 = name[:2].upper()
            t2 = str(len(name))
            username = "MEDDOC" + t2 + t1 + str(id)
            doc_record = AddDoctorModel.get_one(id) 
            doc_record.update({"username": username})
            from ..app import Database
            Database.commit()
            flash('Doctor Added','success')
            return render_template('collab.html',username=username)
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to add new Doctor"},400)

@admin_api.route("/doctors", methods=["GET"])
def get_all_doctors():
    try:
        local_timezone =  tzlocal.get_localzone()
        dateFormat = "%Y-%m-%d %H:%M:%S"
        if 'username' in session:
            doctor=AddDoctorModel.get_all()
            # det=[]
            for d in doctor:
                d.addition_date = d.addition_date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
                d.addition_date = d.addition_date.strftime(dateFormat)
                # res=add_format(d.id,d.name,d.username,d.addition_date)
                # det.append(res)
            return render_template('collab_doctors.html',doctor=doctor)
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to fetch all Doctor"},400)




@admin_api.route("/orders", methods=["GET"])
def get_all_orders():
    try:
        local_timezone =  tzlocal.get_localzone()
        dateFormat = "%Y-%m-%d %H:%M:%S"
        if 'username' in session:
            orders=PatientRegistrationModel.get_all_orders()
            det=[]
            for p,o in orders:
                o.order_date = o.order_date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
                o.order_date = o.order_date.strftime(dateFormat)
                res=order_format(o.id,p.name,p.email,o.order_date,o.amount)
                det.append(res)
            return render_template('order.html',order=det)
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to fetch all Orders"},400)


def order_format(a,b,c,d,e):
    return {
        "id":a,
        "patient_name":b,
        "patient_email":c,
        "order_date":d,
        "amount":e
    }


@admin_api.route("/order_item/<int:id>", methods=["GET"])
def get_order_items(id):
    try:
        if 'username' in session:
            items=MedicineModel.get_order_details(id)
            det = []
            for m, i in items:
                total_price = i.quantity * i.price_per_medicine
                res = show_items(m.image_url, m.name, total_price, i.quantity)
                det.append(res)
            return render_template('orderitem.html',item=det)
        else:
            return redirect(url_for('admin_api.home'))
    except Exception as e:
        return custom_response({"msg":"Unable to fetch Order Details"},400)


def show_items(a, b, c, d):
    return {"image_url": a, "name": b, "price": c, "quantity": d}




def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )




