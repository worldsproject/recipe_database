from app import db
db.create_all()

from app import models, user_datastore
from config import ADMIN_PASSWORD

try:
    user_datastore.create_role(name="admin", description="Site Administrators.")
    user_datastore.create_user(email="tbutram@worldsproject.org", password=ADMIN_PASSWORD)

    user_datastore.add_role_to_user("tbutram@worldsproject.org", "admin")

    db.session.commit()
except:
    pass

# Import your application as:
# from app import application
# Example:

from app import app

# Import CherryPy
import cherrypy

if __name__ == '__main__':

    # Mount the application
    cherrypy.tree.graft(app, "/")

    # Unsubscribe the default server
    cherrypy.server.unsubscribe()

    # Instantiate a new server object
    server = cherrypy._cpserver.Server()

    # Configure the server object
    server.socket_host = "0.0.0.0"
    server.socket_port = 80
    server.thread_pool = 30

    # For SSL Support
    # server.ssl_module            = 'pyopenssl'
    # server.ssl_certificate       = 'ssl/certificate.crt'
    # server.ssl_private_key       = 'ssl/private.key'
    # server.ssl_certificate_chain = 'ssl/bundle.crt'

    # Subscribe this server
    server.subscribe()

    # Start the server engine (Option 1 *and* 2)

    cherrypy.engine.start()
    cherrypy.engine.block()
