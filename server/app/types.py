from enum import Enum

class SystemType(Enum):
    TIDB = "TiDB"
    MYSQL = "MySQL"
    MONGODB = "MongoDB"


class VarType(Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    REAL = "REAL"
    ENUM = "ENUM"
    TIMESTAMP = "TIMESTAMP"

class UnitType(Enum):
    BYTES = "bytes"
    MILLISECONDS = "milliseconds"
    OTHER = "other"

class ResourceType(Enum):
    MEMORY = "Memory"
    CPU = "CPU"
    STORAGE = "Storage"
    OTHER = "Other"

class AlgorithmType(Enum):
    GPB = "GPB"
    DDPG = "DDPG"
    DNN = "DNN"

    def is_valid(algo):
        return algo in [AlgorithmType.GPB.value, AlgorithmType.DDPG.value, AlgorithmType.DNN.value]

class MetricType(Enum):
    COUNTER = "COUNTER"
    INFO = "INFO"
    STATISTICS = "STATISTICS"

class WorkloadStatusType(Enum):
    MODIFIED = "MODIFIED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"

class PipelineTaskType(Enum):
    PRUNED_METRICS = "Pruned Metrics"
    RANKED_KNOBS = "Ranked Knobs"
    KNOB_DATA = "Knob Data"
    METRIC_DATA = "Metric Data"
