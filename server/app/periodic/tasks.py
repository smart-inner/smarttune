from app import db
from app.models import *
from app.types import *
from app.utils import *
from loguru import logger
from .aggregate_data import *
from .knob_identification import *
from .workload_characterization import *
import time

def run_background_tasks():
    start_ts = time.time()
    logger.info("Starting background tasks...")
    # Find modified and not modified workloads, we only have to calculate for the
    # modified workloads.
    modified_workloads = Workflow.query.filter(Workload.status == WorkloadStatusType.MODIFIED.value).all()
    num_modified = len(modified_workloads)
    non_modified_workloads = Workload.query.filter(Workload.status == WorkloadStatusType.PROCESSED.value).all()
    non_modified_workloads = [workload.id for workload in non_modified_workloads]

    last_pipeline_run = PipelineRun.query.filter(PipelineRun.end_time != None).order_by(PipelineRun.id.desc()).first()

    if num_modified == 0:
        # No previous workload data yet. Try again later.
        logger.info("No modified workload data yet. Ending background tasks.")
        return

    # Create new entry in PipelineRun table to store the output of each of
    # the background tasks
    pipeline_run = PipelineRun(start_time=time.now(), end_time=None)
    db.session.add(pipeline_run)
    db.session.flush()
    pipeline_run_id = pipeline_run.id
    db.session.commit()

    for i, workload in enumerate(modified_workloads):
        workload.status = WorkloadStatusType.PROCESSING.value
        db.session.commit()
        wkld_results = Result.query.filter(Result.workload_id == workload.id).all()
        num_wkld_results = len(wkld_results)
        workload_name = '{}.{}'.format(workload.system_id, workload.name)

        logger.info("Starting workload %s (%s/%s, # results: %s)..." % (workload_name,
                    i + 1, num_modified, num_wkld_results))

        if num_wkld_results == 0:
            # delete the workload
            logger.info("Deleting workload %s because it has no results." % workload_name)
            db.session.delete(workload)
            db.session.commit()
            continue

        if num_wkld_results < MIN_WORKLOAD_RESULTS_COUNT:
            # Check that there are enough results in the workload
            logger.info("Not enough results in workload %s (# results: %s, # required: %s)." % \
                        (workload_name, num_wkld_results, MIN_WORKLOAD_RESULTS_COUNT))
            workload.status = WorkloadStatusType.PROCESSED.value
            db.session.commit()
            continue

        logger.info("Aggregating data for workload %s..." % workload_name)
        # Aggregate the knob & metric data for this workload
        knob_data, metric_data = aggregate_knobs_metrics_data(wkld_results)
        logger.info("Done aggregating data for workload %s." % workload_name)

        num_valid_results = knob_data['data'].shape[0]  # pylint: disable=unsubscriptable-object
        if num_valid_results < MIN_WORKLOAD_RESULTS_COUNT:
            # Check that there are enough valid results in the workload
            logger.info("Not enough valid results in workload %s (# valid results: "
                        "%s, # required: %s)." % (workload_name, num_valid_results,
                        MIN_WORKLOAD_RESULTS_COUNT))
            workload.status = WorkloadStatusType.PROCESSED.value
            db.session.commit()
            continue

        # Knob_data and metric_data are 2D numpy arrays. Convert them into a
        # JSON-friendly (nested) lists and then save them as new PipelineData
        # objects.
        knob_data_copy = copy.deepcopy(knob_data)
        knob_data_copy['data'] = knob_data_copy['data'].tolist()
        knob_data_copy = json.dumps(knob_data_copy)
        knob_entry = PipelineData(pipeline_run_id=pipeline_run_id,
                                  task_type=PipelineTaskType.KNOB_DATA.value,
                                  workload_id=workload.id,
                                  data=knob_data_copy,
                                  creation_time=time.now())
        db.session.add(knob_entry)

        metric_data_copy = copy.deepcopy(metric_data)
        metric_data_copy['data'] = metric_data_copy['data'].tolist()
        metric_data_copy = json.dumps(metric_data_copy)
        metric_entry = PipelineData(pipeline_run_id=pipeline_run_id,
                                    task_type=PipelineTaskType.METRIC_DATA.value,
                                    workload_id=workload.id,
                                    data=metric_data_copy,
                                    creation_time=time.now())
        db.session.add(metric_entry)
        db.session.commit()

        # Execute the Workload Characterization task to compute the list of
        # pruned metrics for this workload and save them in a new PipelineData
        # object.
        logger.info("Pruning metrics for workload %s..." % workload_name)
        system = SystemCatalog.query.filter(SystemCatalog.id == workload.system_id).first()
        pruned_metrics = run_workload_characterization(metric_data=metric_data, system=system)
        logger.info("Done pruning metrics for workload %s (# pruned metrics: %s).\n\n"
                    "Pruned metrics: %s\n" % (workload_name, len(pruned_metrics),
                    pruned_metrics))
        pruned_metrics_entry = PipelineData(pipeline_run_id=pipeline_run_id,
                                            task_type=PipelineTaskType.PRUNED_METRICS.value,
                                            workload=workload,
                                            data=json.dumps(pruned_metrics),
                                            creation_time=time.now())
        db.session.add(pruned_metrics_entry)
        db.session.commit()

        # Workload target objective data
        ranked_knob_metrics = sorted(wkld_results.distinct('session').values_list(
            'session__target_objective', flat=True).distinct())

        if KNOB_IDENT_USE_PRUNED_METRICS:
            ranked_knob_metrics = sorted(set(ranked_knob_metrics) + set(pruned_metrics))

        # Use the set of metrics to filter the metric_data
        metric_idxs = [i for i, metric_name in enumerate(metric_data['columnlabels'])
                       if metric_name in ranked_knob_metrics]
        ranked_metric_data = {
            'data': metric_data['data'][:, metric_idxs],
            'rowlabels': copy.deepcopy(metric_data['rowlabels']),
            'columnlabels': [metric_data['columnlabels'][i] for i in metric_idxs]
        }

        # Execute the Knob Identification task to compute an ordered list of knobs
        # ranked by their impact on the System's performance. Save them in a new
        # PipelineData object.
        logger.info("Ranking knobs for workload %s (use pruned metric data: %s)..." % \
                    (workload_name, KNOB_IDENT_USE_PRUNED_METRICS))
        session_ids = []
        for result in wkld_results:
            if result.session_id not in session_ids:
                session_ids.append(result.session_id)
        sessions = []
        for id in session_ids:
            session = Session.query.filter(Session.id == id).first()
            sessions.append(session)
        rank_knob_data = copy.deepcopy(knob_data)
        rank_knob_data['data'], rank_knob_data['columnlabels'] = clean_knob_data(knob_data['data'], knob_data['columnlabels'], sessions)
        ranked_knobs = run_knob_identification(knob_data=rank_knob_data,
                                               metric_data=ranked_metric_data,
                                               system=system)
        logger.info("Done ranking knobs for workload %s (# ranked knobs: %s).\n\n"
                    "Ranked knobs: %s\n" % (workload_name, len(ranked_knobs), ranked_knobs))
        ranked_knobs_entry = PipelineData(pipeline_run_id=pipeline_run_id,
                                          task_type=PipelineTaskType.RANKED_KNOBS.value,
                                          workload_id=workload.id,
                                          data=json.dumps(ranked_knobs),
                                          creation_time=time.now())
        db.session.add(ranked_knobs_entry)
        db.session.commit()

        workload.status = WorkloadStatusType.PROCESSED.value
        db.session.commit()
        logger.info("Done processing workload %s (%s/%s)." % (workload_name, i + 1,
                    num_modified))

    logger.info("Finished processing %s modified workloads." % num_modified)

    non_modified_workloads = Workload.query.filter(Workflow.id.in_(non_modified_workloads)).all()
    # Update the latest pipeline data for the non modified workloads to have this pipeline run
    PipelineData.query.filter(workload__in=non_modified_workloads,
                              pipeline_run=last_pipeline_run)\
        .update(pipeline_run=pipeline_run)

    # Set the end_timestamp to the current time to indicate that we are done running
    # the background tasks
    pipeline_run.end_time = time.now()
    db.session.commit()
    exec_time = TaskUtil.save_execution_time('periodic_task', start_ts, "run_background_tasks")
    logger.info("Finished background tasks (%.0f seconds)." % exec_time)
