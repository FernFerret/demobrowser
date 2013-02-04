from demobrowser import db
from pprint import pprint
from datetime import datetime
import re

class Demo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logfile = db.Column(db.String(8))
    size = db.Column(db.String(12))
    path = db.Column(db.String(512))
    name = db.Column(db.String(80))
    date = db.Column(db.Date())
    summary = db.Column(db.Text())
    title = db.Column(db.String(80))
    
    @staticmethod
    def get_all():
        return Demo.query.all()
        
    @staticmethod
    def get_page(page, per_page=12):
        pageobj = Demo.query.order_by(Demo.date.desc()).paginate(page, per_page=per_page)
        return pageobj
    
    def good_date(self):
        # Maybe I like "%B %d, %Y" better...
        return self.date.strftime("%d %B %Y")
    
    @staticmethod
    def demo_exists(demo_name):
    	return (Demo.query.filter_by(path=demo_name).first() != None)

    @staticmethod
    def create_from_name(demo_name):
        match = re.match('auto-(?P<date>[0-9]{8})-.*-(?P<map>.*)\.dem', demo_name)
        if match:
            strdate = match.groupdict()['date']
            thedate = datetime(int(strdate[0:4]), int(strdate[4:6]), int(strdate[6:8]))
            return Demo.create(match.groupdict()['map'], demo_name, "27.45 MB", thedate)
        return (False, "Whoops, something went wrong... :( %s" % demo_name)
    @staticmethod
    def create(map_name, demopath, demo_size, map_date, tflog=None):
        # Make sure the user isn't already registered.
        demo = Demo.query.filter_by(path=demopath).first()
        if demo:
            return (False, "Error, demo already exists!")
        new_demo = Demo()
        new_demo.size = demo_size
        new_demo.path = demopath
        new_demo.name = map_name
        new_demo.date = map_date
        # Init the title to the map_name
        new_demo.title = map_name
        db.session.add(new_demo)
        return (True, "Success! Demo '%s' was uploaded!" % demopath)
        
    @staticmethod
    def get_from_id(id):
        return Demo.query.filter_by(id=id).first()

    @staticmethod
    def delete(id):
        demo = Demo.query.filter_by(id=id).first()
        if not demo:
            return False
        db.session.delete(demo)
        db.session.commit()
        return True

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(40))
    # this is so we know whos steam id is whos
    name = db.Column(db.String(40))
    nickname = db.String(80)
    admin = db.Column(db.Boolean)

    def make_admin(self, admin):
        self.admin = admin
        db.session.commit()

    @staticmethod
    def get(steam_id):
        # Always create the first user that logs in.
        if not User.query.count():
            user = User()
            user.steam_id = steam_id
            user.name = 'FernFerret'
            user.admin = True
            db.session.add(user)
            print "Creating initial user - %s" % steam_id
            return user 
        user = User.query.filter_by(steam_id=steam_id).first()
        if not user:
            return False
        return user

    @staticmethod
    def get_from_id(id):
        return User.query.filter_by(id=id).first()

    @staticmethod
    def get_all():
        return User.query.all()

    @staticmethod
    def create(name, steamid, admin):
        # Make sure the user isn't already registered.
        user = User.query.filter_by(steam_id=steamid).first()
        if user:
            return (False, "Error, user already exists!")
        new_user = User()
        new_user.steam_id = steamid
        new_user.name = name
        new_user.admin = admin
        db.session.add(new_user)
        return (True, "Success! User '%s' was created!" % name)

    @staticmethod
    def delete(id):
        user = User.query.filter_by(id=id).first()
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True