from flask import Blueprint, request, Response
from app.types import AlgorithmType
from app.models import *
from app import db
import json

session = Blueprint('session', __name__)

@session.route('/create', methods=['POST'])
def create_session():
    req = json.loads(request.stream.read())
    system_type = req.get('system_type', None)
    version = req.get('version', None)
    session = req.get('session', None)
    if system_type is None or version is None:
        return Response("Request 'system_type' or 'version' is null", status=500)
    if session is None:
        return Response("Request 'session' is null", status=500)
    filters = {
        Session.name == session['name']
    }
    got = Session.query.filter(*filters).first()
    if got is not None:
        return Response("Session '%s' has been created" % session['name'], status=500)

    filters = {
        SystemCatalog.type == system_type, 
        SystemCatalog.version == version
    }
    got = SystemCatalog.query.filter(*filters).first()
    if got is None:
        return Response('%s:%s has not been registered' % (system_type, version), status=500)
    db.session.add(Session(
        system_id=got.id,
        name=session['name'],
        description=session['description'],
        algorithm=session.get('algorithm', AlgorithmType.GPB.value),
        target_objective='global.' + session['target_objective'],
        hyper_parameters=session['hyper_parameters']))
    db.session.commit()
    return Response("Success to create session '%s' for %s:%s" % (session['name'], system_type, version), status=200)
