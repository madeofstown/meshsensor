from dataclasses import dataclass
from dataclass_wizard import JSONWizard, JSONFileWizard

@dataclass
class SensorDataBase(JSONWizard, JSONFileWizard, key_case='AUTO'):
    nodes: list['Node']

@dataclass
class Node(JSONWizard, JSONFileWizard, key_case='AUTO'):
    nodeID: int
    longName: str
    shortName: str
    telemetry: list['EnvTelemetry']

@dataclass
class EnvTelemetry(JSONWizard, JSONFileWizard, key_case='AUTO'):
    time: int
    environmentMetrics: dict