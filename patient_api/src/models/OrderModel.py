from marshmallow import fields, Schema
from . import db, bcrypt
import datetime
import pytz
from .OrderitemModel import OrderitemSchema

IST = pytz.timezone('Asia/Kolkata')


class OrderModel(db.Model):

    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('registration.id'),nullable=False)
    amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction_history.id'),nullable=False)
    address_id=db.Column(db.Integer, db.ForeignKey('address.id'),nullable=False)
    order_item = db.relationship("OrderitemModel",backref="orders", lazy=True)


    def __init__(self, data):
        self.patient_id = data.get('patient_id')
        self.amount = data.get('amount')
        self.order_date = datetime.datetime.utcnow()
        self.transaction_id = data.get('transaction_id')
        self.address_id=data.get('address_id')

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
        return OrderModel.query.get(id)

    @staticmethod
    def get_patient_orders(patient_id):
        return db.session.query(OrderModel).filter(OrderModel.patient_id==patient_id)
    

    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    patient_id = fields.Int(required=True)
    amount = fields.Float(required=True)
    order_date = fields.DateTime(dump_only=True)
    transaction_id = fields.Int(required=True)
    address_id = fields.Int(required=True)
    order_item = fields.Nested(OrderitemSchema, many=True)