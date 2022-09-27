from flask import Blueprint, request, Response
from app.models import *
from app.types import AlgorithmType
from app import db, executor
from app.workflow import flow
from datetime import datetime
from pytz import timezone
from app.parser import KnobParser, MetricParser
from app.types import VarType, WorkloadStatusType
import json

result = Blueprint('result', __name__)
TIME_ZONE = 'Asia/Shanghai'

@result.route('/generate/<session_name>', methods=['POST'])
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
    observation_time = float(summary['observation_time'])

    # load, process, and store the knobs in the system's configuration
    parser = KnobParser(session.system_id)
    knob_dict = parser.parse_system_knobs(json.loads(knobs))
    filters = {
        KnobCatalog.system_id == session.system_id,
        KnobCatalog.var_type != VarType.STRING.value,
        KnobCatalog.var_type != VarType.TIEMSTAMP.value,
        KnobCatalog.tunable == True
    }
    knob_to_convert = KnobCatalog.query.filter(*filters).all()
    converted_knob_dict = parser.convert_system_knobs(knob_dict, knob_to_convert)

    # load, process, and store the runtime metrics exposed by the system
    metrics_before = json.loads(metrics_before)
    metrics_after = json.loads(metrics_after)
    parser = MetricParser(session.system_id)
    initial_metric_dict = parser.parse_system_metrics(metrics_before)
    final_metric_dict = parser.parse_system_metrics(metrics_after)
    metric_dict = parser.calculate_change_in_metrics(initial_metric_dict, final_metric_dict)
    numeric_metric_dict = parser.convert_system_metrics(metric_dict, session.target_objective)

    # create a new workload if this one does not already exist
    filters = {
        Workload.name == summary['workload'],
        Workload.system_id == session.system_id
    }
    workload = Workload.query.filter(*filters).first()
    if workload is None:
        workload = Workload(name=summary['workload'], 
            status=WorkloadStatusType.MODIFIED.value, system_id=session.system_id)
        db.session.add(workload)
        db.session.flush()
        workload_id = workload.id
    else:
        workload.status = WorkloadStatusType.MODIFIED.value
        workload_id = workload.id
    db.session.commit()

    result = Result(
        knob_data=json.dumps(converted_knob_dict), 
        metric_data=json.dumps(numeric_metric_dict), 
        observation_start_time=start_time, 
        observation_end_time=end_time,
        observation_time=observation_time, 
        workload_id = workload_id,
        session_id=session.id)
    db.session.add(result)
    db.session.flush()
    result_id = result.id
    db.session.commit()

    if session.algorithm == AlgorithmType.GPB.value:
        executor.submit(flow.gaussian_process_bandits, result_id)
    
    return Response("Result stored successfully! Running tunner with result id: %s" % result.id, status=200)

@result.route('/query/<session_name>', methods=['GET'])
def query_result(session_name):
    return flow.gaussian_process_bandits("123")