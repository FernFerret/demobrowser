from demobrowser import app, oid, db
from demobrowser.helpers import get_steam_userinfo, get_my_ip, do_upload_log
from demobrowser.models import User, Demo
from flask import render_template, session, redirect, url_for, request, g, flash, get_flashed_messages
from werkzeug import secure_filename
from functools import wraps
from pyfile import write_pyfile
import re
from glob import glob
import os
import json

_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

if app.config.get('TEST', False):
    session['user_admin'] = True
    session['user_id'] = 'TEST_ID'
## Route Helpers ##
def admin_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        if session.get('user_admin', None) is None:
            flash('Error, please login through Steam to view this page.', category='error')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return decorated

def login_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        print session
        if session.get('user_id', None) is None:
            flash('Error, please login through Steam to view this page.', category='error')
            return redirect(url_for('index'))
        return function(*args, **kwargs)
    return decorated

## Routes ##

@app.route('/')
def index():
    return render_template('demos.html', demos=Demo.get_page(1, app.config['DEMO_PER_PAGE']))

@app.route('/page/<page>/')
def demopage(page=1):
    try:
        page = int(page)
    except ValueError:
        return redirect(url_for('index'))
    if page == 1:
        return redirect(url_for('index'))
    return render_template('demos.html', demos=Demo.get_page(page, app.config['DEMO_PER_PAGE']))

@app.route('/login/')
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')

@oid.after_login
def check_login(resp):
    match = _steam_id_re.search(resp.identity_url)
    g.user = User.get(match.group(1))
    if not g.user:
        flash("Error, Could not log in. You don't have an account.", category='error')
        return redirect(url_for('index'))
    steamdata = get_steam_userinfo(g.user.steam_id, app.config['STEAM_API_KEY'])
    g.user.nickname = steamdata['personaname']
    db.session.commit()
    session['user_id'] = g.user.id
    session['user_admin'] = g.user.admin
    session['user_nick'] = g.user.nickname
    session['avatar'] = steamdata['avatar']
    flash('You are logged in as %s' % g.user.nickname, category='success')
    return redirect(oid.get_next_url())

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_nick', None)
    session.pop('user_admin', None)
    flash('You\'ve been logged out.', category='info')
    return redirect(url_for('index'))

@app.route('/users/')
@admin_required
def users():
    return render_template('users.html', users=User.get_all())

@app.route('/users/delete/', methods=['POST'])
@admin_required
def delete_user():
    try:
        if int(request.form['delete']) == session['user_id']:
            return "You cannot delete yourself!", 403
    except ValueError:
        return "Fail.", 403
    if User.delete(int(request.form['delete'])):
        return "Success."
    return "Fail.", 403

@app.route('/users/add/', methods=['GET', 'POST'])
@admin_required
def add_user():
    errors = []
    values = {}
    if request.method == 'POST':
        values['name'] = request.form['name']
        values['steamid'] = request.form['steamid']
        values['admin'] = request.form.get('admin', None) is not None
        for key, value in values.items():
            if value == '':
                errors.append(key)
        if not errors:
            success, msg = User.create(values['name'], values['steamid'], values['admin'])
            if success:
                flash(msg, category='success')
                db.session.commit()
            else:
                flash(msg, category='error')
            return redirect(url_for('add_user'))
    return render_template('add_user.html', errors=errors, values=values)

@app.route('/users/makeadmin/', methods=['POST'])
@admin_required
def make_admin():
    try:
        if int(request.form['userid']) == session['user_id']:
            return "You cannot modify your own admin privs.", 403
    except ValueError:
        return "Fail.", 403
    user = User.get_from_id(int(request.form['userid']))
    admin = request.form['admin'].lower() == 'true'
    if user:
        user.make_admin(admin)
        return "Success"
    return "Fail.", 403

@app.route('/settings/', methods=['GET', 'POST'])
@admin_required
def settings():
    values = {}
    if request.method == 'POST':
        # These 4 cannot be changed in settings
        values['STEAM_API_KEY'] = str(app.config['STEAM_API_KEY'])
        values['SECRET_KEY'] = str(app.config['SECRET_KEY'])
        values['ADDRESS'] = str(app.config['ADDRESS'])
        values['SQLALCHEMY_DATABASE_URI'] = str(app.config['SQLALCHEMY_DATABASE_URI'])
        # The rest of these can
        values['TITLE'] = str(request.form['title'])
        values['DEMO_STORAGE_DIR'] = str(request.form.get('storage', None))
        values['DEBUG'] = request.form.get('debug', None) is not None
        values['DEMO_DOWNLOAD_DIR'] = str(request.form.get('download', None))
        values['DEMO_PUBLIC'] = request.form.get('public', None) is not None
        try:
            values['DEMO_PER_PAGE'] = int(request.form.get('perpage', 12))
        except ValueError:
            flash("Warning: Defaulting Demos Per Page to 12 because you didn't put a number in that textbox, idiot.", category='warn')
        #if request.form.get('cleardb', None) is not None and values['DEBUG'] is True:
        #    db.drop_all()
        #    db.create_all()
        write_pyfile(app.config['CFG_FILE'], values)
        # Now set our config values properly
        for key, value in values.iteritems():
            app.config[key] = value
        flash('Success! Your settings were updated.', category='success')
    return render_template('settings.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == "dem"

def allowed_log_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == "log"

@app.route('/upload/', methods=['GET', 'POST'])
@admin_required
def upload_demo():
    values = {}
    if request.method == 'POST':
        async = False
        if request.form.get('async', '0') == '1':
            async = True
        #log_file = request.files['log_file']
        the_file = request.files['demo_file']
        # Returns a demo on success, none if fail.
        demo, msg, cat = _do_upload_demo_file(the_file)
        if demo and async:
            flash(msg, category=cat)
            return "Good"
        elif async:
            return json.dumps({'msg':msg, 'cat':cat}), 403
        #     # If the log file was present, and we had a successful upload, try the log file.
        #     _do_upload_log_file(log_file, demo)
        flash(msg, category=cat)
    return render_template('upload_demo.html', values=values)

@app.route('/demo/check/', methods=['POST'])
@admin_required
def check_filename():
    filename = request.form.get('filename', None)
    if filename is not None:
        print "Checking %s" % filename
        file_exists, total_path, category = _is_file_on_disk(filename)
        if file_exists:
            return json.dumps({'success':False,'msg':total_path,'cat':category})
        return json.dumps({'success':True})
    return json.dumps({'success':False, 'msg':"No filename provided.", 'cat':'error'})

def _is_file_on_disk(filename):
    total_path = os.path.join(app.config['DEMO_STORAGE_DIR'], filename)
    if os.path.exists(total_path):
        demo = Demo.get_from_filename(filename)
        if demo:
            msg = "<strong>Whoops!</strong> <a href='%s'>That Demo already exists</a>!" % \
                  (url_for('view_demo', demo=demo.id))
            category = 'warning'
        else:
            msg = "<strong>Whoops!</strong> That Demo <strong>file</strong> already exists, but hasn't been added to the repository. " \
                  "Perhaps you'd like to <a href='%s'>import it</a>?" % (url_for("import_demo"))
            category = 'warning'
        return True, msg, category
    return False, total_path, "success"

def _do_upload_demo_file(the_file):
    '''
    Returns: Demo Object/False, Message, Message Type (to be passed to flash)
    '''
    if not the_file:
        return False, "You must select a demo to upload!", "error"
    if not allowed_file(the_file.filename):
        return False, "DOH! Only .dem files are allowed!", "error"

    filename = secure_filename(the_file.filename)
    file_exists, total_path, category = _is_file_on_disk(filename)
    if file_exists:
        # NOTE: total_path here will be the message!
        return False, total_path, category

    success, msg = Demo.create_from_name(filename)
    if success:
        category = 'success'
        the_file.save(total_path)
        db.session.commit()
        demo = Demo.get_from_filename(filename)
    else:
        category = 'error'
    return demo, msg, category

def _do_upload_log_file(the_file, demo):
    if not allowed_log_file(the_file.filename):
        flash("DOH! Your logfile should be named X.log!", category='error')
        return False, "DOH! Your logfile should be named X.log!", 'error'
    filename = secure_filename(the_file.filename)
    # We'll store the demo files in the STORAGE dir
    total_path = os.path.join(app.config['DEMO_STORAGE_DIR'], filename)
    if os.path.exists(total_path):
        flash("<strong>Whoops!</strong> That Logfile already exists, Not sure what to do here...(%s)!" % total_path, category='warning')
        return False, "<strong>Whoops!</strong> That Logfile already exists, Not sure what to do here...(%s)!" % total_path, 'warning'
    the_file.save(total_path)
    success, log_id, msg = do_upload_log(total_path, app.config.get('LOGSTF_API_KEY', ''), title=demo.title, map=demo.name)
    if success:
        flash(msg, category='success')
        demo.logfile = log_id
        db.session.commit()
    else:
        flash(msg, category='error')
        return "Demo uploaded successfully <strong>without</strong> logs! <a href='%s'>Click here to see it</a>!" % url_for("view_demo", demo=demo.id)
    try:
        os.unlink(total_path)
    except EnvironmentError:
        # Already gone.
        pass
    return "Demo uploaded successfully with logs! <a href='%s'>Click here to see it</a>!" % url_for("view_demo", demo=demo.id)

@app.route('/import/', methods=['GET', 'POST'])
@admin_required
def import_demo():
    values = {}
    if request.method == 'POST':
        for demo_name in request.form:
            success, msg = Demo.create_from_name(demo_name)
            if success:
                flash(msg, category='success')
                db.session.commit()
            else:
                flash(msg, category='error')

    demos_raw = glob(os.path.join(app.config.get('DEMO_STORAGE_DIR', '.'), "*.dem"))
    demos = []
    for demo in demos_raw:
        if not Demo.demo_exists(os.path.basename(demo)):
            demos.append(os.path.basename(demo))
    return render_template('import_demo.html', demos=demos)

@app.route('/view/<demo>', methods=['GET'])
def view_demo(demo=None):
    # This renders the permalink
    if demo is None:
        return redirect(url_for('index'))
    demo = Demo.get_from_id(demo)
    if demo is None:
        flash('Sorry I couldn\'t find that demo...', category='warning')
        return redirect(url_for('index'))
    # TODO: Do SQL magic to get this down to 1 query, too late tonight...
    return render_template('view_demo.html', demo=demo, next=demo.next_by_date(), prev=demo.previous_by_date())

@app.route('/demos/delete/', methods=['POST'])
@admin_required
def delete_demo():
    if request.method == 'POST':
        demoid = request.form.get("demoid", None)
        Demo.delete(int(demoid))
    return "Yay."

@app.route('/demos/field/<demo>', methods=['POST'])
@admin_required
def edit_demo_field(demo=None):
    demo = Demo.get_from_id(demo)
    if request.method == 'POST':
        name = request.form.get("name", '')
        value = request.form.get("value", '')
        if name == "delete":
            # special case,  we need to redirect
            flash('Success! Demo %s was deleted!' % demo.title, category='success')
            return redirect(url_for('index'))
        if name == "summary":
            value = value.replace("\n", "<br />")
        setattr(demo, name, value)
        db.session.commit()
        return "Yep."
    return "Nope."
