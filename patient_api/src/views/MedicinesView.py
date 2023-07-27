from flask import request, g, Blueprint, json, Response
from ..shared.Authentication import Auth
from ..models.MedicineModel import MedicineModel, MedicineSchema

from flask_cors import cross_origin
medicines_api = Blueprint("medicines_api", __name__)

medicines_schema = MedicineSchema()




@medicines_api.route("/", methods=["GET"])
@cross_origin()
def get_all():
    """
    Get All Medicines
    """
    try:
        medicines = MedicineModel.get_all()
        data = medicines_schema.dump(medicines, many=True)
        return custom_response({"msg": data}, 200)
    except Exception as e:
        return custom_response({"msg": "Unable to fetch medicines"}, 400)


def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )
