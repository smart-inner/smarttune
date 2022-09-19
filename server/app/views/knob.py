from flask import Blueprint, request, Response
from app.models import *
from app import db
import json

knob = Blueprint('knob', __name__)

@knob.route('/register/catalog', methods=['POST'])
def register_knobs_catalog():
    req = json.loads(request.stream.read())
    system_type = req.get('system_type', None)
    version = req.get('version', None)
    knobs = req.get('knobs', [])
    if system_type is None or version is None:
        return Response("Request 'system_type' or 'version' is null", status=500)
    filters = {
        SystemCatalog.type == system_type, 
        SystemCatalog.version == version
    }
    got = SystemCatalog.query.filter(*filters).first()
    if got is None:
        return Response('%s:%s has not been registered' % (system_type, version), status=500)
    knobs_catalog_list = []
    for knob in knobs:
        knobs_catalog_list.append(KnobCatalog(
            system_id=got.id, 
            name=knob['name'], 
            var_type=knob['var_type'],
            unit=knob['unit'],
            category=knob['category'],
            description=knob['description'],
            scope=knob['scope'],
            min_val=knob['min_val'],
            max_val=knob['max_val'],
            default=knob['default'],
            enum_vals=knob['enum_vals'],
            tunable=knob['tunable'],
            resource=knob['resource']))
    db.session.add_all(knobs_catalog_list)
    db.session.commit()
    return Response("Success to register knobs for %s:%s" % (system_type, version), status=200)

@knob.route('/tuning', methods=['POST'])
def register_knobs_tuning():
    req = json.loads(request.stream.read())
    session_name = req.get('session_name', None)
    tuning_knobs = req.get('tuning_knobs', [])
    if session_name is None:
        return Response("Request 'session_name' is null", status=500)
    if len(tuning_knobs) == 0:
        return Response("Request 'tuning_knobs' is empty", status=500)

    got = Session.query.filter(Session.name == session_name).first()
    session_id = got.id
    system_id = got.system_id
    knobs_catalog = KnobCatalog.query.filter(KnobCatalog.system_id == system_id).all()
    knobs_tuning_list = []
    for knob in knobs_catalog:
        if knob.name in tuning_knobs:
            knobs_tuning_list.append(SessionKnob(session_id=session_id, knob_id=knob.id))
    db.session.add_all(knobs_tuning_list)
    db.session.commit()
    return Response("Success to register tuning knobs for session '%s'" % session_name, status=200)
