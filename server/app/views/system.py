from flask import Blueprint, request, Response
from app.models import *
from app.utils import *
from app import db
from app.commons import *
import json

system = Blueprint('system', __name__)

@system.route('/register', methods=['POST'])
def register_system():
    req = json.loads(request.stream.read())
    system_type = req.get('system_type', None)
    version = req.get('version', None)
    conversion = req.get('conversion', DEFAULT_CONVERSION)
    knobs = req.get('knobs', [])
    metrics = req.get('metrics', [])
    if system_type is None or version is None:
        return Response("Request 'system_type' or 'version' is null", status=500)
    filters = {
        SystemCatalog.type == system_type, 
        SystemCatalog.version == version
    }
    got = SystemCatalog.query.filter(*filters).first()
    if got is not None:
        return Response("%s@%s has been registered" % (system_type, version), status=200)
    system_catalog = SystemCatalog(type=system_type, version=version, conversion=conversion)
    db.session.add(system_catalog)
    db.session.flush()
    
    # register knobs catalog
    knobs_catalog_list = []
    for knob in knobs:
        knobs_catalog_list.append(KnobCatalog(
            system_id=system_catalog.id, 
            name=knob['scope'] + '.' + knob['name'], 
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

    metrics_catalog_list = []
    for metric in metrics:
        metrics_catalog_list.append(MetricCatalog(
            system_id=system_catalog.id, 
            name=metric['scope'] + '.' + metric['name'], 
            var_type=metric['var_type'],
            unit=metric['unit'],
            description=metric['description'],
            metric_type=metric['metric_type'],
            scope=metric['scope']))
    db.session.add_all(metrics_catalog_list)

    db.session.commit()
    return Response("Success to register %s@%s" % (system_type, version), status=200)
