from .parser import Parser
from app.models import MetricCatalog
from app.types import VarType, MetricType

class MetricParser(Parser):
    def __init__(self, system_id):
        super().__init__(system_id)

    def parse_system_metrics(self, metrics):
        valid_metrics = self.parse_system_variables(metrics)
        for key in valid_metrics.keys():
            assert len(valid_metrics[key]) == 1
            valid_metrics[key] = valid_metrics[key][0]
        metric_catalog = {metric.name: metric for metric in MetricCatalog.query.filter(MetricCatalog.system_id == self.system_id)}
        return self.extract_valid_variables(valid_metrics, metric_catalog, default_value='0')

    def calculate_change_in_metrics(self, metrics_start, metrics_end):
        adjusted_metrics = {}

        metric_catalog = {metric.name : metric for metric in MetricCatalog.query.filter(MetricCatalog.system_id == self.system_id)}
        for metric_name, start_val in metrics_start.items():
            end_val = metrics_end[metric_name]
            metric = metric_catalog[metric_name]

            if metric.var_type == VarType.INTEGER or metric.var_type == VarType.REAL:
                convert_fn = self.convert_integer if metric.var_type == VarType.INTEGER else self.convert_real
                start_val = convert_fn(start_val, metric)
                end_val = convert_fn(end_val, metric)
                if metric.metric_type == MetricType.COUNTER.value:
                    adj_val = end_val - start_val
                else:
                    adj_val = end_val
                assert adj_val >= 0, "'{}' wrong metric type: {}(start={}, end={}, diff={})".format(
                    metric_name, metric.metric_type, start_val, end_val, end_val - start_val)
                adjusted_metrics[metric_name] = adj_val
            else:
                adjusted_metrics[metric_name] = end_val

        return adjusted_metrics

    def convert_system_metrics(self, metrics, target_objective):
        numeric_metrics = {}
        filters = {
            MetricCatalog.metric_type != MetricType.INFO.value,
            MetricCatalog.system_id == self.system_id
        }
        numeric_metric_catalog = MetricCatalog.query.filter(*filters).all()

        for metric in numeric_metric_catalog:
            name = metric.name
            value = metrics[name]

            if metric.var_type == VarType.INTEGER.value:
                converted = float(self.convert_integer(value, metric))
            elif metric.var_type == VarType.REAL.value:
                converted = self.convert_real(value, metric)
            else:
                raise ValueError("Found non-numeric metric '{}' in the numeric metric "
                                 "catalog: value={}, type={}".format(name, value, metric.var_type))
            
            if metric.metric_type == MetricType.COUNTER.value:
                assert isinstance(converted, float)
                numeric_metrics[name] = converted
            elif metric.metric_type == MetricType.STATISTICS.value:
                assert isinstance(converted, float)
                numeric_metrics[name] = converted
            else:
                raise ValueError("Unknown metric type for {}: {}".format(name, metric.metric_type))

        if target_objective not in numeric_metrics:
            raise ValueError("Invalid target objective '{}', Expected one of: "
                             "{}.".format(target_objective, ', '.join(numeric_metrics.keys())))
        return numeric_metrics