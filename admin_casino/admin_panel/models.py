# models_gino.py
import gino
from gino import Gino

# Инициализация Gino
db = Gino()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer(), primary_key=True)
    login = db.Column(db.String(), unique=True)
    password = db.Column(db.String())
    hidden_login = db.Column(db.String())
    hall_id = db.Column(db.Integer(), nullable=True)
    project_id = db.Column(db.Integer(), db.ForeignKey('project.id'), nullable=True)

    def __repr__(self):
        return f"<User login={self.login}>"

class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer(), primary_key=True)
    project_name = db.Column(db.String())
    project_link = db.Column(db.String())
    hall_id = db.Column(db.Integer(), unique=True)
    mac = db.Column(db.String(), unique=True)
    bot_token = db.Column(db.String(), nullable=True)
    webapp_url = db.Column(db.String(), nullable=True)

    def __repr__(self):
        return f"<Project name={self.project_name}>"
