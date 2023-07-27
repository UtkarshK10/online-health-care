from marshmallow import fields, Schema
import datetime
import pytz
from . import db, bcrypt
from .PatientRecordsModel import PatientRecordsSchema,PatientRecordsModel
from .OrderModel import OrderSchema,OrderModel
from .CartModel import CartSchema
from .AddressModel import AddressSchema,AddressModel
from .TransactionModel import TransactionSchema,TransactionModel

IST = pytz.timezone('Asia/Kolkata')


class PatientRegistrationModel(db.Model):

    __tablename__ = 'registration'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(13), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    profile_url = db.Column(db.String(1000), nullable=False,
                            default="https://upload.wikimedia.org/wikipedia/commons/6/67/User_Avatar.png")
    verified = db.Column(db.String(10), nullable=False, default="0")
    total_credit = db.Column(db.Float, nullable=False, default=100)
    reset_token = db.Column(db.String(500), nullable=True)
    reset_token_exp = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime)
    otp = db.Column(db.Integer,nullable=True)
    records = db.relationship("PatientRecordsModel",
                              backref="registration", lazy=True)
    order = db.relationship("OrderModel",backref="registration", lazy=True)
    cart = db.relationship("CartModel",backref="registration", lazy=True)
    address = db.relationship("AddressModel",backref="registration", lazy=True)
    transaction = db.relationship("TransactionModel",backref="registration", lazy=True)

    def __init__(self, data):
        self.name = data.get('name')
        self.email = data.get('email')
        self.phone = data.get('phone')
        self.username = data.get('username')
        self.password = self.__generate_hash(data.get('password'))
        self.age = data.get('age')
        self.gender = data.get('gender')
        self.profile_url = data.get('profile_url')
        self.verified = data.get('verified')
        self.total_credit = data.get('total_credit')
        self.reset_token = data.get('reset_token')
        self.reset_token_exp = data.get('reset_token_exp')
        self.created_at = datetime.datetime.utcnow()
        self.otp = data.get('otp')

    def save(self):
        db.session.add(self)
        db.session.flush()

    def update(self, data):
        for key, item in data.items():
            if key == 'password':
                item = self.__generate_hash(item)
            setattr(self, key, item)
        db.session.flush()

    def delete(self):
        db.session.delete(self)
        db.session.flush()


    @staticmethod
    def get_user_by_email(value):
        return PatientRegistrationModel.query.filter_by(email=value).first()

    @staticmethod
    def get_user_by_username(value):
        return PatientRegistrationModel.query.filter_by(username=value).first()
    
    @staticmethod
    def get_user_by_ph_no(value):
        return PatientRegistrationModel.query.filter_by(phone=value).first()

    @staticmethod
    def get_other_user_by_ph_no(phone,id):
        return db.session.query(PatientRegistrationModel.id).filter(PatientRegistrationModel.phone == phone,PatientRegistrationModel.id != id).scalar()

    @staticmethod
    def get_one_user(id):
        return PatientRegistrationModel.query.get(id)

    def __generate_hash(self, password):
        return bcrypt.generate_password_hash(password, rounds=10).decode("utf-8")

    def check_hash(self, password):
        return bcrypt.check_password_hash(self.password, password)


    @staticmethod
    def get_all_orders():
        return db.session.query(PatientRegistrationModel,OrderModel).join(OrderModel).filter(OrderModel.patient_id==PatientRegistrationModel.id)

    def __repr__(self):
        return '<id {}>'.format(self.id)
    
    @staticmethod
    def get_user_by_reset_token(value):
        return PatientRegistrationModel.query.filter_by(reset_token=value).first()

    


class PatientRegistrationSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    phone = fields.Str(required=True)
    username = fields.Str(required=True)
    gender = fields.Str(required=True)
    age = fields.Int(required=True)
    profile_url = fields.Str(required=False)
    verified = fields.Str(required=False)
    total_credit = fields.Int(required=False)
    password = fields.Str(required=True, load_only=True)
    reset_token = fields.Str(required=False)
    reset_token_exp = fields.DateTime(required=False)
    created_at = fields.DateTime(dump_only=True)
    otp = fields.Int(required=False)
    records = fields.Nested(PatientRecordsSchema, many=True)
    cart = fields.Nested(CartSchema, many=True)
    order = fields.Nested(OrderSchema, many=True)
    address = fields.Nested(AddressSchema,many=True)
    transaction = fields.Nested(TransactionSchema,many=True)
