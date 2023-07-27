from marshmallow import fields, Schema
from . import db, bcrypt
from sqlalchemy.sql import func


class OrderitemModel(db.Model):

    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'),nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'),nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_medicine = db.Column(db.Float, nullable=False)

    def __init__(self, data):
        self.order_id = data.get('order_id')
        self.medicine_id = data.get('medicine_id')
        self.quantity = data.get('quantity')
        self.price_per_medicine = data.get('price_per_medicine')

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
        return OrderitemModel.query.get(id)

    
    @staticmethod
    def total_item_count(order_id):
        return db.session.query(func.count(OrderitemModel.id)).filter(OrderitemModel.order_id==order_id).scalar()

    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class OrderitemSchema(Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int(required=True)
    medicine_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    price_per_medicine = fields.Float(required=True)
    