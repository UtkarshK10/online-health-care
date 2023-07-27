from flask import request, g, Blueprint, json, Response
from ..shared.Authentication import Auth
from ..models.TransactionModel import TransactionModel,TransactionSchema
from flask_cors import cross_origin
import datetime
import time
import pytz
import tzlocal


transaction_api = Blueprint("transaction_api", __name__)

transaction_schema = TransactionSchema()

@transaction_api.route("/show_transactions", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def show_all_transactions():
    try:
        local_timezone =  tzlocal.get_localzone()
        dateFormat = "%Y-%m-%d %H:%M:%S"
        patient_id = g.user.get('id')
        data = TransactionModel.get_all_transaction(patient_id)
        det=[]
        for i in data:
            i.transaction_date = i.transaction_date.replace(tzinfo=pytz.utc).astimezone(local_timezone)
            i.transaction_date = i.transaction_date.strftime(dateFormat)
            res = transaction_format(i.id,i.done_to,i.amount,i.transaction_date)
            det.append(res)
        return custom_response({"details":det},201)
    except Exception as e:
        return custom_response({"msg":"Unable to show Transactions"},400)


def transaction_format(a,b,c,d):
    return {
        "transaction_id":a,
        "done_to":b,
        "amount":c,
        "transaction_date":d
    }

def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )