from marshmallow import fields, Schema
from . import db, bcrypt
from sqlalchemy.sql import func


class PrescriptionitemModel(db.Model):

    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'),nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'),nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)

    def __init__(self, data):
        self.prescription_id = data.get('prescription_id')
        self.medicine_id = data.get('medicine_id')
        self.quantity = data.get('quantity')
        self.description = data.get('description')

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
        return PrescriptionitemModel.query.get(id)
    
    @staticmethod
    def delete_prescription_items(prescription_id):
        db.session.query(PrescriptionitemModel).filter(PrescriptionitemModel.prescription_id==prescription_id).delete()
        db.session.flush()

    

    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class PrescriptionitemSchema(Schema):
    id = fields.Int(dump_only=True)
    prescription_id = fields.Int(required=True)
    medicine_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    description = fields.Str(required=True)
    