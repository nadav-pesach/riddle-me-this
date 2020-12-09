import csv


import peewee
from peewee import AutoField, BooleanField, ForeignKeyField, IntegerField, Model, PostgresqlDatabase, TextField
import private
# SqliteDatabase

database = PostgresqlDatabase(
    private.DATABASE,
    user=private.USER,
    password=private.PASSWORD,
    host=private.HOST,
    port=private.PORT,
)

# database = SqliteDatabase('riddles_db')

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Riddles(BaseModel):
    answer = TextField()
    difficulty = IntegerField(null=True)
    riddle = TextField()

    class Meta:
        table_name = 'riddles'

class Users(BaseModel):
    email = TextField(null=True)
    password = TextField()
    user_name = TextField(unique=True)
    level = IntegerField()

    class Meta:
        table_name = 'users'

class Games(BaseModel):
    game_id = AutoField()
    user_name = ForeignKeyField(column_name='user_name', field='user_name', model=Users)

    class Meta:
        table_name = 'games'

class GameResulte(BaseModel):
    game = ForeignKeyField(column_name='game_id', field='game_id', model=Games)
    game_result = BooleanField()
    riddle = ForeignKeyField(column_name='riddle_id', model=Riddles)

    class Meta:
        table_name = 'game_resulte'

TABLES = [Users, Games, GameResulte, Riddles]
with database.connection_context():
    database.create_tables(TABLES, safe=True)
    database.commit()
# Riddles.create_table()
# Users.create_table()
# Games.create_table()
# GameResulte.create_table()

# credit: falsetru
# link: https://stackoverflow.com/a/21572244
with open('riddles.csv') as f:
    data = [{k: v for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]
try:
    with database.atomic():
        # https://github.com/sqlalchemy/sqlalchemy/issues/4656#issuecomment-489233090
        # solution for: No value for argument 'database' in method callpylint(no-value-for-parameter)
        # noqa pylint: disable=E1120
        # noqa pylint: disable=no-value-for-parameter
        Riddles.insert_many(data).execute()
        database.commit()
except peewee.IntegrityError as err:
    print(err, 'riddle db alreay updated')

