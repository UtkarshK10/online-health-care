from marshmallow import fields, Schema
from . import db, bcrypt
from sqlalchemy.sql import func





class CartModel(db.Model):

    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'),nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('registration.id'),nullable=False)

    def __init__(self, data):
        self.quantity = data.get('quantity')
        self.patient_id = data.get('patient_id')
        self.medicine_id = data.get('medicine_id')

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
        return CartModel.query.get(id)


    @staticmethod
    def get_row_id(patient_id,medicine_id):
        return db.session.query(CartModel.id).filter(CartModel.medicine_id == medicine_id,CartModel.patient_id==patient_id).scalar()

    @staticmethod
    def empty_patient_cart(patient_id):
        db.session.query(CartModel).filter(CartModel.patient_id==patient_id).delete()
        db.session.flush()


    def __repr__(self):
        return '<id {}>'.format(self.id)

    


class CartSchema(Schema):
    id = fields.Int(dump_only=True)
    quantity = fields.Int(required=True)
    medicine_id = fields.Int(required=True)
    patient_id = fields.Int(required=True)