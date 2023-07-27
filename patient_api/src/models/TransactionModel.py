from marshmallow import fields, Schema
from . import db, bcrypt
import datetime
import pytz
from .PatientRecordsModel import PatientRecordsSchema
from .OrderModel import OrderSchema

IST = pytz.timezone('Asia/Kolkata')


class TransactionModel(db.Model):

    __tablename__ = 'transaction_history'

    id = db.Column(db.Integer, primary_key=True)
    done_to = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime)
    patient_id = db.Column(db.Integer, db.ForeignKey('registration.id'),nullable=False)
    records = db.relationship("PatientRecordsModel",backref="transaction_history", lazy=True)
    orders = db.relationship("OrderModel",backref="transaction_history", lazy=True)


    def __init__(self, data):
        self.done_to = data.get('done_to')
        self.amount = data.get('amount')
        self.transaction_date = datetime.datetime.utcnow()
        self.patient_id = data.get('patient_id')

    def save(self):
        db.session.add(self)
        db.session.flush()

    def delete(self):
        db.session.delete(self)
        db.session.flush()

    def update(self, data):
        for key, item in data.items():
            setattr(self, key, item)
        db.session.flush()


    @staticmethod
    def get_one(id):
        return TransactionModel.query.get(id)

    @staticmethod
    def get_all_transaction(patient_id):
        return db.session.query(TransactionModel).filter(TransactionModel.patient_id==patient_id)


    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)
    done_to = fields.Str(required=True)
    amount = fields.Float(required=True)
    transaction_date = fields.DateTime(dump_only=True)
    patient_id = fields.Int(required=True)
    records = fields.Nested(PatientRecordsSchema, many=True)
    orders = fields.Nested(OrderSchema, many=True)