from flask import request, g, Blueprint, json, Response
from ..shared.Authentication import Auth
from ..models.CartModel import CartModel, CartSchema
from ..models.MedicineModel import MedicineSchema, MedicineModel
from ..models.PatientRegistrationModel import (
    PatientRegistrationModel,
    PatientRegistrationSchema,
)
from flask_cors import cross_origin


cart_api = Blueprint("cart_api", __name__)

cart_schema = CartSchema()
patient_schema = PatientRegistrationSchema()
medicine_schema = MedicineSchema()


@cart_api.route("/add_to", methods=["POST", "PUT"])
@cross_origin()
@Auth.auth_required_patient
def add_to_cart():
    try:
        data = request.get_json()
        medicine_id = data.get("medicine_id")
        patient_id = g.user.get("id")
        data["patient_id"] = patient_id
        quantity = data.get("quantity")
        cart_entry_id = CartModel.get_row_id(patient_id, medicine_id)
        
        msg = "Added to Cart!"
        if not cart_entry_id:
            row = cart_schema.load(data)
            row_block = CartModel(row)
            row_block.save()
            data = cart_schema.dump(row_block)
        else:
            if quantity == 1:
                entry = CartModel.get_one(cart_entry_id)
                cart_entry = cart_schema.dump(entry)
                quan = cart_entry["quantity"]
                new_quantity = quan + 1
                if new_quantity > 10:
                    new_quantity = 10
                entry.update({"quantity": new_quantity})
                data = cart_schema.dump(entry)
            else:
                entry = CartModel.get_one(cart_entry_id)
                cart_entry = cart_schema.dump(entry)
                quan = cart_entry["quantity"]
                new_quantity = quan - 1
                if new_quantity < 1:
                    new_quantity = 1
                entry.update({"quantity": new_quantity})
                data = cart_schema.dump(entry)
        from ..app import Database
        Database.commit()
        return custom_response({"data": data, "msg": msg}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to add to the Cart"},400)


@cart_api.route("/", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def show_cart():
    try:
        cart = MedicineModel.get_patient_cart(g.user.get("id"))
        det = []
        for medicine, item in cart:
            
            res = format(
                medicine.name,
                medicine.price,
                medicine.image_url,
                item.quantity,
                item.id,
                medicine.description,
                medicine.id,
            )

            det.append(res)
        return custom_response({"details": det}, 200)
    except Exception as e:
        return custom_response({"msg":"Unable to fetch from the Cart"},400)


def format(a, b, c, d, e, f, g):
    return {
        "medicine_name": a,
        "price": b,
        "image_url": c,
        "quantity": d,
        "id": e,
        "description": f,
        "medicine_id": g,
    }


@cart_api.route("/delete", methods=["DELETE"])
@cross_origin()
@Auth.auth_required_patient
def delete_from_cart():
    try:
        data = request.get_json()
        del_id = data.get("id")
        del_item = CartModel.get_one(del_id)
        data = cart_schema.dump(del_item)
        if data.get("patient_id") != g.user.get("id"):
            return custom_response({"error": "Permission Denied"}, 403)
        del_item.delete()
        from ..app import Database
        Database.commit()
        return custom_response({"msg": "Deleted"}, 200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to delete from the Cart"},400)


@cart_api.route("/check", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def checkout():
    try:
        patient_id = g.user.get("id")
        patient = PatientRegistrationModel.get_one_user(patient_id)
        patient_user = patient_schema.dump(patient)
        total_credits = patient_user["total_credit"]
        cart = MedicineModel.get_patient_cart(g.user.get("id"))
        total_price = 0
        for medicine, item in cart:
            total_price += medicine.price * item.quantity
        if total_credits >= total_price:
            return custom_response({"msg": True}, 200)
        else:
            return custom_response(
                {
                    "msg": False,
                    "info": "Insufficient Credits, you need {} credits more".format(
                        total_price - total_credits
                    ),
                },
                200,
            )
    except Exception as e:
        return custom_response({"msg":"Unable to check out from the Cart"},400)


def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )
