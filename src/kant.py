# all the imports
import os
import sqlite3
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from flask.ext.babel    import Babel
from passlib.apps       import custom_app_context as pwd_context
from config             import LANGUAGES

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'kant.db'),
    DEBUG=True,
    SECRET_KEY='development key',
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
    return request.accept_languages.best_match(LANGUAGES.keys())

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

    cur = db.execute('SELECT name, user FROM keys WHERE id = ?', [id])
    key = cur.fetchall()

    return render_template('show_key_history.html', history=history, key=key)

@app.route('/users')
def show_users():
    db = get_db()
    cur = db.execute('SELECT id, name, mail, phone FROM users ORDER BY name')
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

@app.route('/edit_key/<int:id>', methods=['GET'])
def edit_key(id):
    if not session.get('logged_in'):
        abort(401)

    db   = get_db()
    cur  = db.execute('SELECT id, name, user FROM keys WHERE id = ?', [id])
    key = cur.fetchone()

    cur  = db.execute('SELECT id, name FROM users')
    users = cur.fetchall()

    return render_template('edit_key.html', key=key, users=users)

@app.route('/save_key', methods=['POST'])
def save_key():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()

    if 'id' in request.form.keys():
        key = {
            'id':   int(request.form['id']),
            'name': str(request.form['name']),
            'user': int(request.form['user'])
        }

        cur = db.execute('SELECT user, name FROM keys WHERE id = ?',
                         [request.form['id']])

        old = cur.fetchone()

        db.execute('INSERT INTO key_history (key, user_before, user_after, '+
                   'name_before, name_after, change_user) ' +
                   'VALUES (?, ?, ?, ?, ?, ?)',
                  [key['id'], old['user'], key['user'], old['name'], key['name'], 0])
        db.commit()

        db.execute('UPDATE keys SET name = ?, user = ? WHERE id = ?',
                   [key['name'], key['user'], key['id']])
        db.commit()
    else:
        db.execute('INSERT INTO keys (name, user, last_update) VALUES (?, ?, ?)',
                   [request.form['name'], request.form['user'],
                   datetime.datetime.now()])
        db.commit()

    flash('Changes to the user where saved successfully!')
    return redirect(url_for('show_keys'))


@app.route('/new_user', methods=['GET'])
def new_user():
    if not session.get('logged_in'):
        abort(401)

    return render_template('new_user.html')

@app.route('/save_user', methods=['POST'])
def save_user():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()

    if 'id' in request.form.keys():
        db.execute('UPDATE users SET name = ?, mail = ?, phone = ? WHERE id = ?',
                   [request.form['name'], request.form['mail'],
                    request.form['phone'], request.form['id']])
    else:
        db.execute('INSERT INTO users (name, mail, phone) VALUES (?, ?, ?)',
                   [request.form['name'], request.form['mail'],
                    request.form['phone']])

    db.commit()

    flash('Changes to the user where saved successfully!')
    return redirect(url_for('show_users'))


@app.route('/edit_user/<int:id>', methods=['GET'])
def edit_user(id):
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute('SELECT id, name, mail, phone FROM users WHERE id = ?', [id])

    user = cur.fetchone()
    return render_template('edit_user.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        cur = db.execute('SELECT password FROM admins WHERE name = ?',
                         [request.form['username']])

        res = cur.fetchone()

        if res == None:
            error = 'Invalid username'
        elif pwd_context.verify(request.form['password'], res['password']) == True:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_keys'))
    return render_template('login.html', error=error)

@app.route('/new_admin', methods=['GET'])
def new_admin():
    if not session.get('logged_in'):
        abort(401)

    return render_template('new_admin.html')

@app.route('/edit_admin/<int:id>', methods=['GET'])
def edit_admin(id):
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute('SELECT id, name, mail FROM users WHERE id = ?', [id])

    admin = cur.fetchone()
    return render_template('edit_admin.html', admin=admin)

@app.route('/save_admin', methods=['POST'])
def save_admin():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    password = pwd_context.encrypt(request.form['password'])

    if 'id' in request.form.keys():
        if request.form['password'] == '******':
            db.execute('UPDATE adminss SET name = ?, mail = ?, password = ? WHERE id = ?',
                       [request.form['name'], request.form['mail'],
                        request.form['password'], request.form['id']])
        else:
            db.execute('UPDATE users SET name = ?, mail = ? WHERE id = ?',
                       [request.form['name'], request.form['mail'],
                        request.form['id']])
    else:
        db.execute('INSERT INTO admins (name, mail, password) VALUES (?, ?, ?)',
                   [request.form['name'], request.form['mail'],
                    request.form['password']])

    db.commit()

    flash('Changes to the admin where saved successfully!')
    return redirect(url_for('show_admins'))

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
