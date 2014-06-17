# all the imports
import os
import sqlite3
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from passlib.apps import custom_app_context as pwd_context

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select name, last_update, user from keys order by last_update desc')
    keys = cur.fetchall()
    return render_template('show_entries.html', keys=keys)

@app.route('/new_key', methods=['GET'])
def new_key():
    if not session.get('logged_in'):
        abort(401)

    return render_template('new_key.html')

@app.route('/add_key', methods=['POST'])
def add_key():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into keys (name, user, last_update) values (?, ?, ?)',
               [request.form['name'], request.form['user'],
               datetime.datetime.now()])
    db.commit()
    flash('New key was successfully submitted')
    return redirect(url_for('show_entries'))

@app.route('/new_user', methods=['GET'])
def new_user():
    if not session.get('logged_in'):
        abort(401)

    return render_template('new_user.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'):
        abort(401)

    password = pwd_context.encrypt(request.form['password'])

    db = get_db()
    db.execute('insert into user (name, password, mail, phone) values (?, ?, ?, ?)',
               [request.form['name'], password,
               request.form['mail'], request.form['phone']])
    db.commit()
    flash('New user was successfully submitted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/install')
def install():
    init_db()


if __name__ == '__main__':
    app.run()
