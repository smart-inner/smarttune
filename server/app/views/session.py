from flask import Blueprint, request, Response
from app.types import AlgorithmType
from app.models import *
from app.utils import *
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
    filters = {
        SystemCatalog.type == system_type, 
        SystemCatalog.version == version
    }
    system = SystemCatalog.query.filter(*filters).first()
    if system is None:
        return Response("%s@%s has not been registered" % (system_type, version), status=500)
    
    if session is None:
        return Response("Request 'session' is null", status=500)
    got = Session.query.filter(Session.name == session['name']).first()
    if got is not None:
        return Response("Session '%s' has been created" % session['name'], status=200)
    sess = Session(
        system_id=system.id,
        name=session['name'],
        description=session['description'],
        algorithm=session.get('algorithm', AlgorithmType.GPB.value),
        target_objective='global.' + session['target_objective'],
        more_is_better=session.get('more_is_better', True),
        hyper_parameters=session['hyper_parameters'])
    db.session.add(sess)
    db.session.flush()

    tuning_knobs = session.get('tuning_knobs', None)
    if tuning_knobs is None:
        return Response("Request 'tuning_knobs' is null", status=500)
    global_knobs = tuning_knobs.get('global', None)
    local_knobs = tuning_knobs.get('local', None)
    if global_knobs is None and local_knobs is None:
        return Response("Request 'global' and 'local' knobs is null", status=500)
    input_knobs = []
    if global_knobs is not None:
        input_knobs += ['global.' + value for value in global_knobs]
    if local_knobs is not None:
        input_knobs += ['local.' + value for value in local_knobs]
    
    knobs_catalog = KnobCatalog.query.filter(KnobCatalog.system_id == system.id).all()
    knobs_tuning_list = []
    for knob in knobs_catalog:
        if knob.name in input_knobs:
            knobs_tuning_list.append(SessionKnob(session_id=sess.id, knob_id=knob.id))
    db.session.add_all(knobs_tuning_list)
    
    db.session.commit()
    return Response("Success to create session '%s' for %s@%s" % (session['name'], system_type, version), status=200)


@session.route('/modify', methods=['POST'])
def modify_session():
    req = json.loads(request.stream.read())
    name = req.get('name', None)
    algorithm = req.get('algorithm', None)
    target_objective = req.get('target_objective', None)
    more_is_better = req.get('more_is_better', None)
    tuning_knobs = req.get('tuning_knobs', None)

    if name is None:
        return Response("Request 'session_name' is null", status=500)
    session = Session.query.filter(Session.name == name).first()
    system = SystemCatalog.query.filter(SystemCatalog.id == session.system_id).first()
    if session is None:
        return Response("Not found session '%s'" % name, status=404)
    
    # modify algorithm
    if algorithm is not None:
        if AlgorithmType.is_valid(algorithm):
            session.algorithm = algorithm
        else:
            return Response("Algorithm '%s' is invalid" % algorithm, status=500)
    
    # modify target objective
    metric_catalog = MetricCatalog.query.filter(MetricCatalog.system_id == session.system_id).all()
    if target_objective is not None:
        for metric in metric_catalog:
            if metric.name[len('global.'):] == target_objective:
                session.target_objective = 'global.' + target_objective
                session.more_is_better = more_is_better
                break
        if session.target_objective != 'global.' + target_objective:
            return Response("Target objective '%s' is invalid" % target_objective, status=500)
    
    # modify tuning knobs
    if tuning_knobs is not None:
        exist_session_knobs = []
        session_knob_infos = DataProcess.get_knobs_for_session(session.id)
        for knob_info in session_knob_infos:
            if knob_info['name'].startswith('global.') and knob_info['name'][len('global.'):] in tuning_knobs:
                exist_session_knobs.append(knob_info['name'][len('global.'):])
                continue
            if knob_info['name'].startswith('local.') and knob_info['name'][len('local.'):] in tuning_knobs:
                exist_session_knobs.append(knob_info['name'][len('local.'):])
                continue
            session_knob = SessionKnob.query.filter(SessionKnob.id == knob_info['id']).first()
            db.session.delete(session_knob)
        knob_catalog = KnobCatalog.query.filter(KnobCatalog.system_id == session.system_id).all()
        knob_catalog_names = {knob.name: knob.id for knob in knob_catalog}
        for knob in tuning_knobs:
            if knob in exist_session_knobs:
                continue
            if ('global.' + knob) in knob_catalog_names:
                db.session.add(SessionKnob(session_id=session.id, knob_id=knob_catalog_names['global.' + knob]))
            elif ('local.' + knob) in knob_catalog_names:
                db.session.add(SessionKnob(session_id=session.id, knob_id=knob_catalog_names['local.' + knob]))
            else:
                return Response("Knob '%s' is invalid" % knob, status=500)
    db.session.commit()
    return Response("Success to modify session '%s' for '%s@%s'" % (session.name, system.type, system.version), status=200)

@session.route('/show/<session_name>', methods=['GET'])
def show_session(session_name):
    session = Session.query.filter(Session.name == session_name).first()
    if session is None:
        return Response("Not found session '%s'" % session_name, status=404)
    system = SystemCatalog.query.filter(SystemCatalog.id == session.system_id).first()
    resp = {
        "name": session_name,
        "system": system.type + "@" + system.version,
        "description": session.description,
        "algorithm": session.algorithm,
        "creation_time": session.creation_time,
        "target_objective": session.target_objective,
        "more_is_better": session.more_is_better,
        "creation_time": session.creation_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return Response(json.dumps(resp), status=200)