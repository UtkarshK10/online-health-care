from marshmallow import fields, Schema
from . import db, bcrypt
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')


class AddDoctorModel(db.Model):

    __tablename__ = 'addition'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200),nullable=False)
    username = db.Column(db.String(40),nullable=True)
    addition_date = db.Column(db.DateTime)
    


    def __init__(self, data):
        self.name = data.get('name')
        self.username = data.get('username')
        self.addition_date = datetime.utcnow()


    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        for key, item in data.items():
            setattr(self, key, item)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return AddDoctorModel.query.all()


    @staticmethod
    def get_one(id):
        return AddDoctorModel.query.get(id)

    @staticmethod
    def get_one_by_name(name):
        return AddDoctorModel.query.filter_by(name=name).first()

    @staticmethod
    def admin_provided_username(username):
        return AddDoctorModel.query.filter_by(username=username).first()

    def __repr__(self):
        return '<id {}>'.format(self.id)
    


class AddDoctorSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    username=fields.Str(required=False)
    addition_date = fields.DateTime(dump_only=True)
    