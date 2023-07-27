from marshmallow import fields, Schema
from . import db, bcrypt
from .CartModel import CartSchema,CartModel
from .OrderitemModel import OrderitemSchema,OrderitemModel
from .PrescriptionitemModel import PrescriptionitemModel,PrescriptionitemSchema



class MedicineModel(db.Model):

    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True,nullable=False)
    name = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200),nullable=True,default="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRIh-CQa0Uyf-2GHaeLQD4SBNCCO3IlAVBroQ&usqp=CAU")
    description = db.Column(db.String(200),nullable=False)
    rating = db.Column(db.Integer,nullable=True,default=0)
    status = db.Column(db.Integer,nullable=True,default=0)
    cart = db.relationship("CartModel",backref="medicines", lazy=True)
    order_item = db.relationship("OrderitemModel",backref="medicines", lazy=True)
    prescription_item = db.relationship("PrescriptionitemModel",backref="medicines", lazy=True)

    def __init__(self, data):
        self.name = data.get('name')
        self.stock = data.get('stock')
        self.price = data.get('price')
        self.image_url = data.get('image_url')
        self.description = data.get('description')
        self.rating = data.get('rating')
        self.status = data.get('status')

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
    def get_all():
        return db.session.query(MedicineModel).filter(MedicineModel.status==0)

    @staticmethod
    def delete_one(medicine_id):
        db.session.query(MedicineModel).get(medicine_id).delete()
        db.session.flush()

    @staticmethod
    def get_by_name(value):
        return MedicineModel.query.filter_by(name=value).first()

    @staticmethod
    def get_one(id):
        return MedicineModel.query.get(id)
    
    @staticmethod
    def get_patient_cart(patient_id):
        return db.session.query(MedicineModel,CartModel).join(CartModel).filter(CartModel.patient_id==patient_id)

    @staticmethod
    def get_order_details(order_id):
        return db.session.query(MedicineModel,OrderitemModel).join(OrderitemModel).filter(OrderitemModel.order_id==order_id)

    @staticmethod
    def get_items(prescription_id):
        return db.session.query(MedicineModel,PrescriptionitemModel).join(PrescriptionitemModel).filter(PrescriptionitemModel.prescription_id==prescription_id)


    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class MedicineSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    stock = fields.Int(required=True)
    price = fields.Float(required=True)
    cart = fields.Nested(CartSchema, many=True)
    order_item = fields.Nested(OrderitemSchema, many=True)
    prescription_item = fields.Nested(PrescriptionitemSchema, many=True)
    image_url = fields.Str(required=False)
    description = fields.Str(required=True)
    rating = fields.Int(required=False)
    status= fields.Int(required=False)