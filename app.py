import os
import random

import bcrypt
import peewee
import requests
from flask import Flask, abort, render_template, request, session, url_for
from playhouse.shortcuts import model_to_dict
from werkzeug.utils import redirect

import models
from models import GameResulte, Games, Riddles, Users, database

app = Flask(__name__)
# app.secret_key = os.environ.get('SECRET_KEY')

@app.before_request
def before_request():
    database.connect()

@app.after_request
def after_request(response):
    database.close()
    return response



@app.route('/register', methods=['GET', 'POST'])
def register():
    # credit: Yam Mesicka
    # https://youtu.be/nl1R7MV8jB0
    if request.method == 'GET':
        return render_template('register.j2')

    salt = bcrypt.gensalt(prefix=b'2b', rounds=10)
    unhashed_password = request.form['password'].encode('utf-8')
    hashed_password = bcrypt.hashpw(unhashed_password, salt)
    fields = {
        **request.form,
        'password': hashed_password,
        'level': 1,
    }
    user = Users(**fields)
    user_name = request.form['user_name']
    try:
        user.save()
    except peewee.IntegrityError:
        return abort(403, f'User {user_name} exists, try something else')
    return 'Success!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    # credit: Yam Mesicka
    # https://youtu.be/nl1R7MV8jB0
    if request.method == 'GET':
        return render_template('login.j2')

    user_name = request.form['user_name']
    if user_name is None:
        return abort(400, 'No user_name supplied')

    try:
        user = Users.select().where(Users.user_name == user_name).get()
    except peewee.DoesNotExist:
        return abort(404, f'User {user_name} does not exists')

    password = request.form['password'].encode('utf-8')
    real_password = str(user.password).encode('utf-8')
    if not bcrypt.checkpw(password, real_password):
        return abort(403, 'user_name and password does not match')

    session['user_name'] = user.user_name
    session['level'] = user.level
    return render_template('profil.j2', user=user)



@app.route('/delete', methods=['GET', 'POST'])
def delete():
    # credit: Yam Mesicka
    # https://youtu.be/nl1R7MV8jB0
    if request.method == 'GET':
        return render_template('login.j2')

    user_name = request.form['user_name']
    if user_name is None:
        return abort(400, 'No user_name supplied')

    try:
        user = Users.select().where(Users.user_name == user_name).get()
    except peewee.DoesNotExist:
        return abort(404, f'User {user_name} does not exists')

    password = request.form['password'].encode('utf-8')
    real_password = str(user.password).encode('utf-8')
    if not bcrypt.checkpw(password, real_password):
        return abort(403, 'user_name and password does not match')
    Users.delete().where(Users.user_name == user_name).execute()
    return render_template('register.j2')



@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'GET':
        return render_template('login.j2')

    user_name = request.form['user_name']
    if user_name is None:
        return abort(400, 'No user_name supplied')

    try:
        user = Users.select().where(Users.user_name == user_name).get()
    except peewee.DoesNotExist:
        return abort(404, f'User {user_name} does not exists')

    password = request.form['password'].encode('utf-8')
    real_password = str(user.password).encode('utf-8')
    if not bcrypt.checkpw(password, real_password):
        return abort(403, 'user_name and password does not match')

    salt = bcrypt.gensalt(prefix=b'2b', rounds=10)
    password = request.form['new_password']
    if password is None:
        password = request.form['password']
    unhashed_password = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(unhashed_password, salt)
    email = request.form['email']
    fields = {
        'user_name': user_name,
        'email': email,
        'password': hashed_password,
        'level': 1,
    }
    Users.update(**fields).where(Users.user_name == user_name).execute()
    return render_template('profil.j2', user=user)

@app.route('/answer', methods=['GET', 'POST'])
def answer():
    if request.method == 'GET':
        return render_template('game.j2')
    if 'game_id' not in session and 'user_name' in session:
        filde = {'user_name': session['user_name']}
        game_play = Games(**filde)
        game_play.save()
        game_id = Games.select().order_by(Games.game_id.desc()).get()
        game_id = model_to_dict(game_id)['game_id']
        session['game_id'] = game_id
    answer = str(request.form['answer'])
    if 'riddle' in session:
        if answer.lower() == session['riddle']['answer'].lower():
            fields = {
                'game_result': True,
                'riddle': session['riddle']['id'],
                'game': session['game_id']
            }
            GameResulte(**fields).save()
            session.pop('riddle', None)
            return redirect(url_for('game'))
        else:
            try:
                resulte = GameResulte.select().where(GameResulte.game == session['game_id']).count()
            except:
                return render_template('index.j2', resulte='0')
            # resulte = model_to_dict(resulte)['id']
            session.pop('game_id', None)
            game_played = Games.select().order_by(Games.game_id.desc()).count()
            query = Users.select(Users.user_name, peewee.fn.COUNT().alias('total_points')).join(Games).join(GameResulte).group_by(Users.user_name).order_by(Users.user_name.desc()).limit(3)
            top_players = []
            for user in query:
                top_players += [user.user_name, user.total_points]
            return render_template('index.j2', game_played=game_played, top_players=top_players, resulte=resulte)
    return render_template('game.j2', )


@app.route('/game')
def game():
    # credit: Yam Mesicka
    # https://youtu.be/nl1R7MV8jB0
    if 'riddle' in session:
        return render_template('game.j2', **session['riddle'])
    riddle_number = random.randint(1, 377)
    try:
        riddle = Riddles.get_by_id(riddle_number)
    except peewee.DoesNotExist:
        abort(404, f'riddle {riddle_number} does not exsit')
    dict_riddle = model_to_dict(riddle)
    session['riddle'] = dict_riddle
    return render_template('game.j2', **session['riddle'])
    

@app.route('/find-us')
def find_us():
    return render_template('find-us.j2')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    for session_value in ('user_name', 'level', 'game', 'game_resulte', 'riddle'):
        session.pop(session_value, None)
    return render_template('login.j2')


@app.route('/index')
def index():
    # need to coppy this into answers as well to return when player make mistake
    game_played = Games.select().order_by(Games.game_id.desc()).count()
    query = Users.select(Users.user_name, peewee.fn.COUNT().alias('total_points')).join(Games).join(GameResulte).group_by(Users.user_name).order_by(Users.user_name.desc()).limit(3)
    top_players = []
    try:
        for user in query:
            top_players += [{'name': user.user_name, "total_points": user.total_points}]
    except peewee.ProgrammingError:
        print(None)

    return render_template('index.j2', game_played=game_played, top_players=top_players)


@app.route('/')
def home():
    # need to coppy this into answers as well to return when player make mistake
    game_played = Games.select().order_by(Games.game_id.desc()).count()
    query = Users.select(Users.user_name, peewee.fn.COUNT().alias('total_points')).join(Games).join(GameResulte).group_by(Users.user_name).order_by(Users.user_name.desc()).limit(3)
    top_players = []
    try:
        for user in query:
            top_players += [{'name': user.user_name, "total_points": user.total_points}]
    except peewee.ProgrammingError:
        print(None)

    return render_template('index.j2', game_played=game_played, top_players=top_players)


if __name__ == '__main__':
    app.run()


