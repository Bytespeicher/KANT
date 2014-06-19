# all the imports
import os
import sqlite3
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from flask.ext.babel import Babel
from passlib.apps    import custom_app_context as pwd_context

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'kant.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin',
    BABEL_DEFAULT_LOCALE='de',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

babel = Babel(app)

@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(['de', 'fr', 'en'])

@babel.timezoneselector
def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone

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
def show_keys():
    db = get_db()
    cur = db.execute('SELECT key.id, key.name, key.last_update, key.user, ' +
                     'user.name AS user_name ' +
                     'FROM keys AS key ' +
                     'JOIN users AS user ON key.user = user.id ' +
                     'ORDER BY key.last_update DESC')
    keys = cur.fetchall()

    return render_template('show_keys.html', keys=keys)

@app.route('/key_history/<int:id>')
def show_key_history(id):
    db = get_db()
    cur = db.execute('SELECT * FROM key_history WHERE key = ?', [id])
    history = cur.fetchall()

    cur = db.execute('SELECT name FROM keys WHERE id = ?', [id])
    key = cur.fetchall()

    return render_template('show_key_history.html', history=history, key=key)

@app.route('/users')
def show_users():
    db = get_db()
    cur = db.execute('SELECT name, mail, phone FROM users ORDER BY name')
    users = cur.fetchall()
    return render_template('show_users.html', users=users)


@app.route('/new_key', methods=['GET'])
def new_key():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute('SELECT id, name FROM users ORDER BY name')
    users = cur.fetchall()

    return render_template('new_key.html', users=users)

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
    return redirect(url_for('show_keys'))

@app.route('/new_user', methods=['GET'])
def new_user():
    if not session.get('logged_in'):
        abort(401)

    return render_template('new_user.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute('insert into users (name, mail, phone) values (?, ?, ?)',
               [request.form['name'], request.form['mail'],
                request.form['phone']])
    db.commit()
    flash('New user was successfully submitted')
    return redirect(url_for('show_users'))


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
            return redirect(url_for('show_keys'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_keys'))

@app.route('/install')
def install():
    init_db()
    return render_template('install.html')


if __name__ == '__main__':
    app.run()
