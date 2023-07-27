from marshmallow import fields, Schema
from . import db, bcrypt
import datetime
import pytz
from .PrescriptionitemModel import PrescriptionitemSchema,PrescriptionitemModel

IST = pytz.timezone('Asia/Kolkata')


class PrescriptionModel(db.Model):

    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'),nullable=False)
    prescription_date = db.Column(db.DateTime)
    prescription_item = db.relationship("PrescriptionitemModel",
                              backref="records", lazy=True)


    def __init__(self, data):
        self.record_id = data.get('record_id')
        self.prescription_date = datetime.datetime.utcnow()


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
        return PrescriptionModel.query.get(id)

    @staticmethod
    def get_prescription_by_record(value):
        return PrescriptionModel.query.filter_by(record_id=value).first()
    

    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class PrescriptionSchema(Schema):
    id = fields.Int(dump_only=True)
    record_id = fields.Int(required=True)
    prescription_date = fields.DateTime(dump_only=True)
    presciption_item = fields.Nested(PrescriptionitemSchema,many=True)