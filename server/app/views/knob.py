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
    return "success02"