from enum import Enum
from tkinter.tix import INTEGER

class SystemType(Enum):
    TIDB = "TiDB"
    MYSQL = "MySQL"
    MONGODB = "MongoDB"


class VarType(Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BOOL = "BOOL"
    ENUM = "ENUM"
    TIEMSTAMP = "TIEMSTAMP"

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
    GPB = "Gaussian Process Bandits"
    DDPG = "Deep Deterministic Policy Gradients"
    DNN = "Deep Neural Network"

class MetricType(Enum):
    COUNTER = "COUNTER"
    INFO = "INFO"
    STATISTICS = "STATISTICS"

class WorkloadStatusType(Enum):
    MODIFIED = "MODIFIED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
