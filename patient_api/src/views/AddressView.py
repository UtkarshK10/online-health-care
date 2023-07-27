from flask import request, g, Blueprint, json, Response
from flask_cors import cross_origin
from ..shared.Authentication import Auth
from ..models.AddressModel import AddressSchema,AddressModel
from ..models.PatientRegistrationModel import PatientRegistrationModel,PatientRegistrationSchema
from flask_cors import CORS, cross_origin

address_api = Blueprint("address_api", __name__)

address_schema = AddressSchema()

@address_api.route("/", methods=["POST"])
@cross_origin()
@Auth.auth_required_patient
def save_address():
    try:
        data = request.get_json()
        patient_id = g.user.get('id')
        address_count = AddressModel.address_count(patient_id)
        if address_count >= 3:
            return custom_response({"msg":"Max. Address Limit Reached,Delete An Address and add New",},200)
        new_address=data['new_address']
        if (new_address):
            del data['new_address']
            data["patient_id"] = patient_id
            save_data = address_schema.load(data)
            add = AddressModel(save_data)
            add.save()
            from ..app import Database
            Database.commit()
            save_data = address_schema.dump(add)
            address_id=save_data['id']
            return custom_response({"address":address_id},200)
        else:
            address_id=data['id']
            return custom_response({"address":address_id},200) 
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to Add Address."},400)   

@address_api.route("/all", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def get_address():
    try:
        patient_id=g.user.get('id')
        addresses=AddressModel.get_patient_all_addresses(patient_id)
        det=[]
        for address in addresses:
            res=address_format(address.id,
            address.name,
            address.phone_number,
            address.house_number,
            address.street,
            address.landmark,
            address.zip_code,
            address.city,
            address.state)
            det.append(res)
        return custom_response({"addresses":det},200)
    except Exception as e:
        return custom_response({"msg":"No Address found"},400)

def address_format(a, b, c, d, e, f, g,h,i):
    return {
        "id": a,
        "name": b,
        "phone_number": c,
        "house_number": d,
        "street": e,
        "landmark": f,
        "zip_code": g,
        "city":h,
        "state":i
    }


@address_api.route("/address_count", methods=["GET"])
@cross_origin()
@Auth.auth_required_patient
def get_address_count():
    try:
        patient_id = g.user.get('id')
        address_count = AddressModel.address_count(patient_id)
        return custom_response({"address_count":address_count},201)
    except Exception as e:
        return custom_response({"msg":"Not able to fetch all addresses."},400)


@address_api.route("/delete_address", methods=["DELETE"])
@cross_origin()
@Auth.auth_required_patient
def delete_address():
    try:
        data = request.get_json()
        address_id = data['address_id']
        address = AddressModel.get_one(address_id)
        address_det = address_schema.dump(address)
        if g.user.get('id') != address_det['patient_id']:
            return custom_response({"msg":"Permission Denied"},403)
        address.update({"status":1})
        from ..app import Database
        Database.commit()
        address_f = address_schema.dump(address)
        return custom_response(address_f,200)
    except Exception as e:
        from ..app import Database
        Database.rollback()
        return custom_response({"msg":"Unable to delete address"},400)



    
def custom_response(res, status_code):
    """
    Custom Response Function
    """
    return Response(
        mimetype="application/json", response=json.dumps(res), status=status_code
    )
