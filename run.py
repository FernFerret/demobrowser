#!/usr/bin/env python

from demobrowser import app, db
#db.drop_all()
db.create_all()
app.debug = app.config.get('DEBUG', False)

# This is required.
app.secret_key = app.config.get('SECRET_KEY', None)

if app.secret_key is None:
    print "ERROR: SECRET_KEY not found in settings.cfg. Please see README.md for help!"
else:
    app.run(host=app.config.get('ADDRESS', '0.0.0.0'))
