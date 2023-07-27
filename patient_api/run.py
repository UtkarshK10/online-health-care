
import os
from flask_cors import CORS

from src.app import create_app
env_name = os.getenv('FLASK_ENV')
app = create_app(env_name)

if __name__ == '__main__':
  CORS(app,resources={r"/api/*": {"origins": "https://medico-health-care.herokuapp.com"}} )
  port = os.getenv('PORT')
  app.run(host='0.0.0.0', port=port)