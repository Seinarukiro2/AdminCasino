from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    login = fields.CharField(max_length=100, unique=True)
    password = fields.CharField(max_length=255)
    hidden_login = fields.CharField(max_length=100)
    hall_id = fields.IntField(null=True)
    project = fields.ForeignKeyField('models.Project', related_name='users', null=True)

    def __str__(self):
        return self.login


class Project(Model):
    id = fields.IntField(pk=True)
    project_name = fields.CharField(max_length=255)
    project_link = fields.CharField(max_length=255)
    hall_id = fields.IntField(unique=True)
    mac = fields.CharField(max_length=17, unique=True)
    bot_token = fields.CharField(max_length=255, null=True, blank=True)
    webapp_url = fields.CharField(max_length=255, null=True, blank=True)
    bot_username = fields.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return self.project_name
