from marshmallow import fields, Schema
from . import db, bcrypt
from sqlalchemy.sql import func
from .OrderModel import OrderSchema



class AddressModel(db.Model):

    __tablename__ = 'address'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),nullable=False)
    phone_number = db.Column(db.String(20),nullable=False)
    house_number = db.Column(db.String(50),nullable=False)
    street = db.Column(db.String(100),nullable=False)
    landmark = db.Column(db.String(50),nullable=True)
    zip_code = db.Column(db.String(20),nullable=True)
    city = db.Column(db.String(20),nullable=True)
    state= db.Column(db.String(30),nullable=True)
    status = db.Column(db.Integer,nullable=True,default=0)
    patient_id = db.Column(db.Integer, db.ForeignKey('registration.id'),nullable=False)
    order_id = db.relationship("OrderModel",backref="address", lazy=True)

    def __init__(self, data):
        self.patient_id = data.get('patient_id')
        self.name = data.get('name')
        self.phone_number = data.get('phone_number')
        self.house_number = data.get('house_number')
        self.street = data.get('street')
        self.landmark = data.get('landmark')
        self.zip_code = data.get('zip_code')
        self.state = data.get('state')
        self.city = data.get('city')
        self.status=data.get('status')

    def save(self):
        db.session.add(self)
        db.session.flush()

    def update(self, data):
        for key, item in data.items():
            setattr(self, key, item)
        db.session.flush()

    def delete(self):
        db.session.delete(self)
        db.session.flush()


    @staticmethod
    def get_one(id):
        return AddressModel.query.get(id)

    @staticmethod
    def get_patient_all_addresses(patient_id):
        return db.session.query(AddressModel).filter(AddressModel.patient_id==patient_id,AddressModel.status==0)

    @staticmethod
    def address_count(patient_id):
        return db.session.query(func.count(AddressModel.id)).filter(AddressModel.patient_id==patient_id,AddressModel.status==0).scalar()
    

    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class AddressSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    house_number = fields.Str(required=True)
    street = fields.Str(required=True)
    landmark = fields.Str(required=False)
    zip_code = fields.Str(required=True)
    city = fields.Str(required=True)
    state = fields.Str(required=True)
    patient_id = fields.Int(required=True)
    status = fields.Int(required=False)
    order_id = fields.Nested(OrderSchema, many=True)