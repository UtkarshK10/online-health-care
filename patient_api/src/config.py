import os


class Development(object):
    """
    Development Environment Configuration
    """
    DEBUG = True
    TESTING = False
    JWT_SECRET_KEY = ''
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = ''
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class Production(object):
    """
    Production Environment Configurations
    """
    DEBUG = False
    TESTING = False
    MAIL_SUPPRESS_SEND = False
    SQLALCHEMY_DATABASE_URI = os.getenv('HEROKU_POSTGRESQL_NAVY_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_EXTENSIONS = [ 
        ".mp4",
        ".mkv",
        ".m4v",
        ".wmv",
        ".jpg",
        ".png",
        ".gif",
    ]
    MAIL_SERVER=os.getenv('MAIL_SERVER')
    MAIL_PORT=os.getenv('MAIL_PORT')
    MAIL_USE_TLS= True
    MAIL_USERNAME=os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
    SESSION_TYPE = os.getenv('SESSION_TYPE')
    CORS_HEADERS = os.getenv('CORS_HEADERS')
    SECRET_KEY = os.getenv('SECRET_KEY')
    TZ = os.getenv('TZ')



app_config = {
    'development': Development,
    'production': Production,
}
