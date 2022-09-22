from flask import Blueprint, request, Response
from app.models import *
from app import db
import json

metric = Blueprint('metric', __name__)

@metric.route('/register/catalog', methods=['POST'])
def register_metrics_catalog():
    req = json.loads(request.stream.read())
    system_type = req.get('system_type', None)
    version = req.get('version', None)
    metrics = req.get('metrics', [])
    if system_type is None or version is None:
        return Response("Request 'system_type' or 'version' is null", status=500)
    filters = {
        SystemCatalog.type == system_type, 
        SystemCatalog.version == version
    }
    got = SystemCatalog.query.filter(*filters).first()
    if got is None:
        return Response('%s:%s has not been registered' % (system_type, version), status=500)
    metrics_catalog_list = []
    for metric in metrics:
        metrics_catalog_list.append(MetricCatalog(
            system_id=got.id, 
            name=metric['scope'] + '.' + metric['name'], 
            var_type=metric['var_type'],
            unit=metric['unit'],
            description=metric['description'],
            metric_type=metric['metric_type'],
            scope=metric['scope']))
    db.session.add_all(metrics_catalog_list)
    db.session.commit()
    return Response("Success to register metrics for %s:%s" % (system_type, version), status=200)
