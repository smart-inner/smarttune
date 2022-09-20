from flask import Blueprint, request, Response
from app.models import *
from app.types import AlgorithmType
from app import db
from app.workflow import flow
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pytz import timezone
from app.parser import parser
import json

result = Blueprint('result', __name__)
pool = ThreadPoolExecutor(max_workers=30)
TIME_ZONE = 'Asia/Shanghai'

@result.route('/generate/<session_name>', methods=['POST', 'GET'])
def generate_result(session_name):
    req = json.loads(request.stream.read())
    metrics_before = req.get('metrics_before', None)
    metrics_after = req.get('metrics_after', None)
    knobs = req.get('knobs', None)
    summary = req.get('summary', None)
    if metrics_before is None or metrics_after is None or knobs is None or summary is None:
        return Response("Request 'metrics_before' or 'metrics_after' or 'knobs' or 'summary' is null", status=500)
    
    session = Session.query.filter(Session.name == session_name).first()
    if session is None:
        return Response("Invalid session: '%s'" % session_name, status=404)

    summary = json.loads(summary)
    filters = {
        SystemCatalog.type == summary['system_type'], 
        SystemCatalog.version == summary['version']
    }
    actual = SystemCatalog.query.filter(*filters).first()
    if actual is None or actual.id != session.system_id:
        expected = SystemCatalog.query.filter(SystemCatalog.id == session.system_id).first()
        return Response("The system must match the type and version, expected=%s:%s, actual=%s:%s" \
        % (expected.type, expected.version, summary['system_type'], summary['version']), status=500)
    start_time = datetime.fromtimestamp(int(float(summary['start_time']) / 1000), timezone(TIME_ZONE))
    end_time = datetime.fromtimestamp(int(float(summary['end_time']) / 1000), timezone(TIME_ZONE))
    # load, process, and store the knobs in the system's configuration
    knob_dict = parser.parse_system_knobs(json.loads(knobs))
    knob_to_convert = KnobCatalog.query.filter(KnobCatalog.system_id == session.system_id)
    converted_knob_dict = parser.convert_dbms_knobs(knob_dict, knob_to_convert)

    # load, process, and store the runtime metrics exposed by the system
    metrics_before = json.loads(metrics_before)
    metrics_after = json.loads(metrics_after)
    initial_metric_dict = parser.parse_system_metrics(metrics_before)
    final_metric_dict = parser.parse_system_metrics(metrics_after)
    metric_dict = parser.calculate_change_in_metrics(initial_metric_dict, final_metric_dict)
    numeric_metric_dict = parser.convert_system_metrics(metric_dict, summary['observation_time'], session.target_objective)

    # save the result
    db.session.add(Result(
        knob_data=json.dumps(converted_knob_dict), 
        metric_data=json.dumps(numeric_metric_dict), 
        observation_start_time=start_time, 
        observation_end_time=end_time, 
        session_id=session.id))
    db.session.commit()

    result = Result.query.filter(Result.session_id == session.id).order_by(Result.id.desc()).first()
    if session.algorithm == AlgorithmType.GPB.value:
        pool.submit(flow.gaussian_process_bandits, result.id)
    
    return Response("Result stored successfully! Running tunner with result id: %s" % result.id, status=200)

@result.route('/query/<session_name>', methods=['GET'])
def query_result(session_name):
    return flow.gaussian_process_bandits("123")