activate_this = '/opt/venv/demobrowser/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/opt/sw/demobrowser')

from demobrowser import app as application
