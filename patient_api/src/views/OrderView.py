from flask import request, g, Blueprint, json, Response
from ..shared.Authentication import Auth
from ..models.OrderModel import OrderSchema, OrderModel
from ..models.CartModel import CartSchema, CartModel
from ..models.MedicineModel import MedicineModel, MedicineSchema
from ..models.PatientRegistrationModel import (
    PatientRegistrationModel,
    PatientRegistrationSchema,
)
from ..models.TransactionModel import TransactionModel, TransactionSchema
from ..models.OrderitemModel import OrderitemModel, OrderitemSchema
from ..models.AddressModel import AddressModel, AddressSchema
from nested_lookup import nested_delete
from flask_cors import cross_origin
import datetime
import time
import pytz
import tzlocal
from datetime import datetime


orders_api = Blueprint("orders_api", __name__)

orders_schema = OrderSchema()
cart_schema = CartSchema()
medicine_schema = MedicineSchema()
patient_schema = PatientRegistrationSchema()
transaction_schema = TransactionSchema()
orderItem_schema = OrderitemSchema()
address_schema = AddressSchema()


@orders_api.route("/confirm", methods=["POST"])
@cross_origin()
@Auth.auth_required_patient
def confirm():
    try:
        data= request.get_json()
        address_id = data['address_id']
        patient_id = g.user.get("id")
        patient = PatientRegistrationModel.get_one_user(patient_id)
        patient_user = patient_schema.dump(patient)
        total_credits = patient_user["total_credit"]


        cart = MedicineModel.get_patient_cart(g.user.get("id"))
        total_price = 0
        for medicine, item in cart:

            total_price += medicine.price * item.quantity

            medicine_id = medicine.id
            medicine_purchased = MedicineModel.get_one(medicine_id)
            new_stock = medicine_purchased.stock - item.quantity
            medicine_purchased.update({"stock": new_stock})
        
        if total_credits < total_price:
            return custom_response(
                {
                    "msg": False,
                    "info": "Insufficient Credits, you need {} credits more".format(
                        total_price - total_credits
                    ),
                },
                200,
            )

        new_credit = total_credits - total_price
        patient.update({"total_credit": new_credit})
        patient_data = patient_schema.dump(patient)

        amount = total_price
        done_to = "Purchased Medicines"
        req_data = transaction_format(amount, done_to,patient_id)
        transaction = transaction_schema.load(req_data)
        transaction_det = TransactionModel(transaction)
        transaction_det.save()
        det = transaction_schema.dump(transaction_det)
        transaction_id = det["id"]
        req_order = order_format(amount, patient_id, transaction_id,address_id)
        order = orders_schema.load(req_order)
        order_det = OrderModel(order)
        order_det.save()
        det_o = orders_schema.dump(order_det)
        order_id = det_o["id"]

        cart = MedicineModel.get_patient_cart(patient_id)
        for medicine, item in cart:
            res = format(medicine.price, item.quantity, medicine.id, order_id)
            order_item = orderItem_schema.load(res)
            orderItem_det = OrderitemModel(order_item)
            orderItem_det.save()
            det_oitem = orderItem_schema.dump(orderItem_det)
        CartModel.empty_patient_cart(patient_id)
        from ..app import Database
        Database.commit()
        return custom_response(
            {
                "msg": "Your order has been successfully placed with order id # "
                + str(order_id),
                "new_credits": new_credit,
            },
            201,
        )
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Sorry, your order could not be placed"},400)


def format(a, b, c, d):
    return {
        "price_per_medicine": a,
        "quantity": b,
        "medicine_id": c,
        "order_id": d,
    }


def transaction_format(a, b, c):
    return {"amount": a, "done_to": b, "patient_id":c}


def order_format(a, b, c, d):
    return {"amount": a, "patient_id": b, "transaction_id": c, "address_id": d}


@orders_api.route("/orders", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def all_orders():
    try:
        local_timezone =  tzlocal.get_localzone()
        dateFormat = "%Y-%m-%d %H:%M:%S"
        patient_id = g.user.get("id")
        orders = OrderModel.get_patient_orders(patient_id)
        det = []
        for i in orders:
            i.order_date = i.order_date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
            i.order_date = i.order_date.strftime(dateFormat)
            res = show_order(i.id, i.order_date, OrderitemModel.total_item_count(i.id))
            det.append(res)
        return custom_response({"orders": det}, 200)
    except Exception as e:
        return custom_response({"msg":"Something went wrong"},400)


def show_order(a, b, c):
    return {"id": a, "order_date": b, "items_count": c}


@orders_api.route("/order_items/<int:order_id>", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def order_items(order_id):
    try:
        order = OrderModel.get_one(order_id)
        order_det = orders_schema.dump(order)
        if g.user.get('id') != order_det['patient_id']:
            return custom_response({"msg":"Permission Denied"},200)
        order_items = MedicineModel.get_order_details(order_id)
        det = []
        for m, i in order_items:
            total_price = i.quantity * i.price_per_medicine
            res = show_items(m.image_url, m.name, total_price, i.quantity)
            det.append(res)
        return custom_response({"details": det}, 200)
    except Exception as e:
        return custom_response({"msg":"Order details could not be fetched"},400)


def show_items(a, b, c, d):
    return {"image_url": a, "name": b, "price": c, "quantity": d}


@orders_api.route("/invoice/<int:order_id>", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def invoice(order_id):
    try:
        patient_id=g.user.get('id')
        patient = PatientRegistrationModel.get_one_user(patient_id)
        patient_user = patient_schema.dump(patient)

        order = OrderModel.get_one(order_id)
        order_det = orders_schema.dump(order)

        address_id=order_det['address_id']
        address = AddressModel.get_one(address_id)
        address_det = address_schema.dump(address)
        nested_delete(address_det, 'patient_id',in_place=True)
        nested_delete(address_det, 'order_id',in_place=True)

        order_items = MedicineModel.get_order_details(order_id)
        det = []
        amount = 0
        # local_timezone =  tzlocal.get_localzone()
        dateFormat = "%Y-%m-%d %H:%M:%S"
        for m, i in order_items:
            total_price = i.quantity * i.price_per_medicine
            amount += total_price
            res = show_items(m.image_url, m.name, total_price, i.quantity)
            det.append(res)
        GST = (amount * 12) / 100
        CGST = GST / 2
        SGST = CGST
        sub_total = amount - GST
        total = amount
    
        t1 = str(order_det['order_date']).split("-",1)
        t2 = str(order_id)
        t3 = str(address_det['zip_code'])
        t4 = t3[int(len(t3)/2):]
        invoice_no = "#TG"+t1[0]+"UD"+t4+t2

        order_date = order_det['order_date']
        print(order_date)

        order_date_arr = str(order_date).split("T")
        order_date = order_date_arr[0] + " " + order_date_arr[1]
        order_date_arr1 = order_date.split(".")
        order_date = order_date_arr1[0]
        print(order_date)
        
        order_date = datetime.strptime(order_date,dateFormat)
        order_time = time.mktime(order_date.timetuple()) + 19800
        print(order_time)
        
        # print(order_date)
        
        # from_zone = tz.gettz('UTC')
        # to_zone = tz.gettz('Asia/Kolkata')

        # # order_date =  order_date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
        # # order_date =  order_date.strftime(dateFormat)
        # order_date = order_date.replace(tzinfo=from_zone)
        # central = order_date.astimezone(to_zone)
        invoice = invoice_format(
            invoice_no,
            patient_user['name'],
            order_id,
            order_time,
            address_det,
            det,
            sub_total,
            GST,
            CGST,
            SGST,
            total
        )
        return custom_response({"invoice":invoice},201)
    except Exception as e:
        return custom_response({"msg":"Invoice could not be generated"},400)
        
def show_items(a, b, c, d):
    return {"image_url": a, "name": b, "price": c, "quantity": d}

def invoice_format(a,b,c,d,e,f,g,h,i,j,k):
    return {
        "Invoice_No":a,
        "Name":b,
        "Order_No.":c,
        "Order_Date":d,
        "Shipping_Address":e,
        "Products":f,
        "Sub_Total":g,
        "GST":h,
        "CGST":i,
        "SGST":j,
        "Total":k
    }



def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )
