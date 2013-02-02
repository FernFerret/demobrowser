from demobrowser import db

class Demo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_tf_id = db.Column(db.String(8))
    demo_size = db.Column(db.String(12))
    demo_path = db.Column(db.String(512))
    map_name = db.Column(db.String(80))
    map_date = db.Column(db.Date())
    
    @staticmethod
    def get_all():
        return User.query.all()
        
    @staticmethod
    def create(map_name, demopath, demo_size, map_date, tflog=None):
        # Make sure the user isn't already registered.
        demo = User.query.filter_by(demo_path=demopath).first()
        if demo:
            return (False, "Error, demo already exists!")
        new_demo = User()
        new_demo.demo_size = "X"
        new_demo.demo_path = demopath
        new_demo.map_name = map_name
        db.session.add(new_demo)
        return (True, "Success! Demo '%s' was uploaded!" % name)

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