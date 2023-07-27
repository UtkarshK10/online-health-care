from marshmallow import fields, Schema
from sqlalchemy import asc
from . import db,bcrypt
import datetime
from .PatientRecordsModel import PatientRecordsSchema,PatientRecordsModel
from .PatientRegistrationModel import PatientRegistrationSchema,PatientRegistrationModel
from .PrescriptionModel import PrescriptionModel,PrescriptionSchema


class DoctorModel(db.Model):
  __tablename__='dregistration'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(200),nullable=False)
  email = db.Column(db.String(50),nullable=False)
  password = db.Column(db.String(500),nullable=False)
  phone = db.Column(db.String(20),unique=True,nullable=False)
  username = db.Column(db.String(40),nullable=False)
  speciality = db.Column(db.String(100),nullable=False)
  experience = db.Column(db.String(50),nullable=False)
  profile_url = db.Column(db.String(1000), nullable=False, default="https://upload.wikimedia.org/wikipedia/commons/6/67/User_Avatar.png")
  rating = db.Column(db.Float,nullable=False,default=0)
  created_at = db.Column(db.DateTime)
  consultation_fee = db.Column(db.Float,nullable=False)
  reset_token = db.Column(db.String(500), nullable=True)
  reset_token_exp = db.Column(db.DateTime, nullable=True)
  verified = db.Column(db.String(10), nullable=False, default="0")
  otp = db.Column(db.Integer,nullable=True)
  patient_records = db.relationship("PatientRecordsModel",
                              backref="dregistration", lazy=True)

  def __init__(self,data):
    self.name = data.get('name')
    self.email = data.get('email')
    self.password = self.__generate_hash(data.get('password'))
    self.phone = data.get('phone')
    self.username = data.get('username')
    self.speciality = data.get('speciality')
    self.experience = data.get('experience')
    self.profile_url = data.get('profile_url')
    self.rating = data.get('rating')
    self.created_at = datetime.datetime.utcnow()
    self.consultation_fee = data.get('consultation_fee')
    self.verified = data.get('verified')
    self.reset_token = data.get('reset_token')
    self.reset_token_exp = data.get('reset_token_exp')
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
  def get_all_users():
    return DoctorModel.query.all()

  @staticmethod
  def get_user_by_username(value):
    return DoctorModel.query.filter_by(username=value).first()

  @staticmethod
  def get_user_by_email(value):
    return DoctorModel.query.filter_by(email=value).first()
  
  @staticmethod
  def get_user_by_ph_no(value):
    return DoctorModel.query.filter_by(phone=value).first()

  @staticmethod
  def get_other_user_by_ph_no(phone,id):
    return db.session.query(DoctorModel.id).filter(DoctorModel.phone == phone,DoctorModel.id != id).scalar()

  @staticmethod
  def get_one_user(id):
    return DoctorModel.query.get(id)
  
  @staticmethod
  def patient_details(id):
    results = db.session.query(DoctorModel,PatientRecordsModel,PatientRegistrationModel). \
      select_from(DoctorModel).join(PatientRecordsModel).join(PatientRegistrationModel).filter(DoctorModel.id==id).order_by(PatientRecordsModel.attended.asc())
    return results

  @staticmethod
  def record_details(record_id):
    return db.session.query(DoctorModel,PatientRecordsModel,PatientRegistrationModel). \
      select_from(DoctorModel).join(PatientRecordsModel).join(PatientRegistrationModel).filter(PatientRecordsModel.id==record_id,DoctorModel.id==PatientRecordsModel.doctor_id,PatientRecordsModel.user_id==PatientRegistrationModel.id)


  def __generate_hash(self, password):
    return bcrypt.generate_password_hash(password, rounds=10).decode("utf-8")

  def check_hash(self, password):
    return bcrypt.check_password_hash(self.password, password)

  @staticmethod
  def get_user_by_reset_token(value):
    return DoctorModel.query.filter_by(reset_token=value).first()

  @staticmethod
  def get_all_prescriptions(patient_id):
    return db.session.query(DoctorModel,PatientRecordsModel,PrescriptionModel). \
      select_from(DoctorModel).join(PatientRecordsModel).join(PrescriptionModel).filter(PatientRecordsModel.user_id==patient_id)

  def __repr__(self):
    return '<id {}>'.format(self.id)
  
class DoctorSchema(Schema):
  id = fields.Int(dump_only=True)
  name = fields.Str(required=True)
  email = fields.Str(required=True)
  password = fields.Str(required=True,load_only=True)
  phone = fields.Str(required=True)
  username=fields.Str(required=True)
  speciality = fields.Str(required=True)
  experience = fields.Str(required=True)
  profile_url = fields.Str(required=False)
  rating = fields.Float(required=False)
  created_at = fields.DateTime(dump_only=True)
  consultation_fee = fields.Float(required=True)
  verified = fields.Str(required=False)
  reset_token = fields.Str(required=False)
  reset_token_exp = fields.DateTime(required=False)
  otp = fields.Int(required=False)
  patient_records = fields.Nested(PatientRecordsSchema, many=True)
  