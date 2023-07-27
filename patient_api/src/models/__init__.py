from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# initialize our db
db = SQLAlchemy()
bcrypt = Bcrypt()

from .PatientRegistrationModel import PatientRegistrationModel, PatientRegistrationSchema
from .PatientRecordsModel import PatientRecordsModel, PatientRecordsSchema
from .MedicineModel import MedicineModel,MedicineSchema
from .TransactionModel import TransactionModel,TransactionSchema