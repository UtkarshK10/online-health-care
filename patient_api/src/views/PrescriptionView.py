from flask import request, g, Blueprint, json, Response
from ..shared.Authentication import Auth
from flask_cors import cross_origin
from ..models.PrescriptionModel import PrescriptionModel, PrescriptionSchema
from ..models.PrescriptionitemModel import PrescriptionitemSchema, PrescriptionitemModel
from ..models.PatientRecordsModel import PatientRecordsModel, PatientRecordsSchema
from ..models.MedicineModel import MedicineSchema, MedicineModel
from ..models.CartModel import CartSchema, CartModel
from ..models.DoctorModel import DoctorSchema, DoctorModel
import pytz
import datetime
import time
import tzlocal



IST = pytz.timezone('Asia/Kolkata')

prescription_api = Blueprint("prescription_api", __name__)
prescription_schema = PrescriptionSchema()
prescriptionitem_schema = PrescriptionitemSchema()
cart_schema = CartSchema()


@prescription_api.route("/create/<int:record_id>", methods=["POST"])
@cross_origin()
@Auth.auth_required_doctor
def generate(record_id):
    try:
        prior_prescription = PrescriptionModel.get_prescription_by_record(record_id)
        if prior_prescription:
            prior_prescription.update({"prescription_date":datetime.datetime.utcnow()})
            prescription_f = prescription_schema.dump(prior_prescription)
            prescription_id = prescription_f['id']
            delete_prescription_items = PrescriptionitemModel.delete_prescription_items(prescription_id)
            req_data = request.get_json()
            for obj in req_data["data"]:
                obj["prescription_id"] = prescription_id
                items = prescriptionitem_schema.load(obj)
                item_det = PrescriptionitemModel(items)
                item_det.save()
                details = prescriptionitem_schema.dump(item_det)
            from ..app import Database
            Database.commit()
            return custom_response({"msg": "Prescription Saved"}, 200)

        data = presc_format(record_id)
        prescription = prescription_schema.load(data)
        prescription_det = PrescriptionModel(prescription)
        prescription_det.save()
        prescript = prescription_schema.dump(prescription_det)
        req_data = request.get_json()
        for obj in req_data["data"]:
            obj["prescription_id"] = prescript["id"]
            items = prescriptionitem_schema.load(obj)
            item_det = PrescriptionitemModel(items)
            item_det.save()
            details = prescriptionitem_schema.dump(item_det)
        from ..app import Database
        Database.commit()
        return custom_response({"msg": "Prescription Saved"}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg": "Unable to create prescription"},400)


def presc_format(a):
    return {"record_id": a}


@prescription_api.route("/show_all", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def show_all_prescription():
    try:
        local_timezone =  tzlocal.get_localzone()
        dateFormat = "%Y-%m-%d %H:%M:%S"
        patient_id = g.user.get("id")
        data = DoctorModel.get_all_prescriptions(patient_id)
        det = []
        for d, r, p in data:
            p.prescription_date = p.prescription_date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
            p.prescription_date = p.prescription_date.strftime(dateFormat)
            res = prescription_format(p.id, p.prescription_date, d.name,r.id,r.doc_rating)
            det.append(res)
        return custom_response({"prescriptions": det}, 201)
    except Exception as e:
        return custom_response({"msg":"Unable to show prescription"},400)

def prescription_format(a, b, c, d, e):
    return {"prescription_id": a, "issue_date": b, "doctor_name": c, "record_id": d, "doc_rating": e}


@prescription_api.route("/show/<int:prescription_id>", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def show_prescription(prescription_id):
    try:
        patient_id = PatientRecordsModel.get_one_prescription_record(prescription_id)
        if g.user.get('id') != patient_id:
            return custom_response({"msg":"Permission Denied"},200)
        data = MedicineModel.get_items(prescription_id)
        det = []
        for m, i in data:
            res = prescriptionitem_format(
                m.name,
                i.description,
                i.quantity,
                m.image_url,
                m.price,
            )
            det.append(res)
        return custom_response({"details": det}, 201)
    except Exception as e:
        return custom_response({"msg":"Unable to show details"},400)


def prescriptionitem_format(a, b, c, d, e):
    return {"Name": a, "description": b, "quantity": c, "image_url": d, "price": e}


@prescription_api.route("/add/<int:prescription_id>", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def add_to_cart(prescription_id):
    try:
        patient_id = PatientRecordsModel.get_one_prescription_record(prescription_id)
        if g.user.get('id') != patient_id:
            return custom_response({"msg":"Permission Denied"},200)
        data = MedicineModel.get_items(prescription_id)
        msg = "Added To Cart"
        for m, i in data:
            medicine_id = m.id
            patient_id = g.user.get("id")
            quantity = i.quantity
            res = cart_format(medicine_id, quantity, patient_id)
            cart_entry_id = CartModel.get_row_id(patient_id, medicine_id)
            if not cart_entry_id:
                row = cart_schema.load(res)
                row_block = CartModel(row)
                row_block.save()
                data = cart_schema.dump(row_block)
            else:
                entry = CartModel.get_one(cart_entry_id)
                cart_entry = cart_schema.dump(entry)
                quan = cart_entry["quantity"]
                new_quantity = quan + quantity
                if new_quantity > 10:
                    new_quantity = 10
                entry.update({"quantity": new_quantity})
                val = cart_schema.dump(entry)
            from ..app import Database
            Database.commit()

        return custom_response({"data": "Done", "msg": msg}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Add to cart failed"},400)


def cart_format(a, b, c):
    return {"medicine_id": a, "quantity": b, "patient_id": c}


def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )