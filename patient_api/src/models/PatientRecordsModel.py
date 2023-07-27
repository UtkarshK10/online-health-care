from marshmallow import fields, Schema
from . import db
from sqlalchemy.sql import func
import datetime
from .PrescriptionModel import PrescriptionSchema,PrescriptionModel
import pytz


IST = pytz.timezone('Asia/Kolkata')

class PatientRecordsModel(db.Model):
  __tablename__='records'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('registration.id'),nullable=False)
  doctor_id = db.Column(db.Integer, db.ForeignKey('dregistration.id'),nullable=False)
  temperature=db.Column(db.String(10),nullable=False)
  symptoms=db.Column(db.String(20),nullable=False)
  contact=db.Column(db.String(20),nullable=False)
  difficulty=db.Column(db.String(20),nullable=False)
  travel=db.Column(db.String(10),nullable=False)
  disease=db.Column(db.String(100),nullable=False)
  apply=db.Column(db.String(120),nullable=False)

  oxy_level=db.Column(db.Float,nullable=False,default=0)
  heart_rate=db.Column(db.Float,nullable=False,default=0)
  created_at = db.Column(db.DateTime)
  attended = db.Column(db.Integer,nullable=True,default=0)
  doc_rating = db.Column(db.Float,nullable=False,default=0)
  meeting_url = db.Column(db.String(200),nullable=True,default='https://medico-videocall.herokuapp.com')
  meeting_time=db.Column(db.DateTime,nullable=True)
  room_id=db.Column(db.String(200),nullable=True)
  transaction_id = db.Column(db.Integer, db.ForeignKey('transaction_history.id'),nullable=False)
  prescription = db.relationship("PrescriptionModel",
                              backref="records", lazy=True)
  
  def __init__(self,data):
    self.user_id = data.get('user_id')
    self.doctor_id = data.get('doctor_id')
    self.temperature=data.get('temperature')
    self.symptoms=data.get('symptoms')
    self.contact=data.get('contact')
    self.difficulty=data.get('difficulty')
    self.travel=data.get('travel')
    self.disease=data.get('disease')
    self.apply=data.get('apply')
    self.oxy_level = data.get('oxy_level')
    self.heart_rate = data.get('heart_rate')
    self.created_at = datetime.datetime.utcnow()
    self.attended = data.get('attended')
    self.doc_rating = data.get('doc_rating')
    self.transaction_id = data.get('transaction_id')
    self.meeting_url = data.get('meeting_url')
    self.meeting_time = data.get('meeting_time')
    self.room_id = data.get('room_id')

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

  def __repr__(self):
    return '<id {}>'.format(self.id)


  @staticmethod
  def get_one_record(id):
    return PatientRecordsModel.query.get(id)

  @staticmethod
  def get_one_prescription_record(prescription_id):
    return db.session.query(PatientRecordsModel.user_id,PrescriptionModel).join(PrescriptionModel).filter(PrescriptionModel.id==prescription_id).scalar()

  @staticmethod
  def get_all_record_of_patient(patient_id):
    return db.session.query(PatientRecordsModel).filter(PatientRecordsModel.user_id==patient_id)
  
  @staticmethod
  def avg_rating(doc_id):
    return db.session.query(func.avg(PatientRecordsModel.doc_rating)).filter(PatientRecordsModel.doctor_id==doc_id,PatientRecordsModel.doc_rating > 0).scalar()
  
  @staticmethod
  def total_pat_count(doc_id):
    return db.session.query(func.count(PatientRecordsModel.id)).filter(PatientRecordsModel.doctor_id==doc_id).scalar()

  @staticmethod
  def att_pat_count(doc_id):
    return db.session.query(func.count(PatientRecordsModel.id)).filter(PatientRecordsModel.doctor_id==doc_id,PatientRecordsModel.attended == 1).scalar()

  @staticmethod
  def check_room_id_patient(patient_id,room_id):
    return PatientRecordsModel.query.filter_by(user_id=patient_id,room_id=room_id).first()

class PatientRecordsSchema(Schema):
  id = fields.Int(dump_only=True)
  temperature = fields.Str(required=True)
  symptoms = fields.Str(required=True)
  contact = fields.Str(required=True)
  difficulty = fields.Str(required=True)
  travel = fields.Str(required=True)
  disease = fields.Str(required=True)
  apply = fields.Str(required=True)
  oxy_level = fields.Float(required=False)
  heart_rate = fields.Float(required=False)
  created_at = fields.DateTime(dump_only=True)
  user_id = fields.Int(required=True)
  doctor_id = fields.Int(required=True)
  attended = fields.Int(required=False)
  doc_rating = fields.Float(required=False)
  transaction_id = fields.Int(required=True)
  meeting_url = fields.Str(required=False)
  meeting_time = fields.DateTime(required=False)
  room_id = fields.Str(required=False)
  presciption = fields.Nested(PrescriptionSchema,many=True)

  