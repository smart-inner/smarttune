from flask import Blueprint, request, Response
from app.models import *
from app import db
import json

system = Blueprint('system', __name__)

@system.route('/register', methods=['POST'])
def register_system():
    req = json.loads(request.stream.read())
    system_type = req.get('system_type', None)
    version = req.get('version', None)
    if system_type is None or version is None:
        return Response("Request 'system_type' or 'version' is null", status=500)
    filters = {
        SystemCatalog.type == system_type, 
        SystemCatalog.version == version
    }
    got = SystemCatalog.query.filter(*filters).first()
    if got is None:
        db.session.add(SystemCatalog(type=system_type, version=version))
        db.session.commit()
        return Response('Success to register %s:%s' % (system_type, version), status=200)
    else:
        return Response('%s:%s has been registered' % (system_type, version), status=200)