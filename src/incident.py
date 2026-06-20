"""Domain model: incidents, actions, observations, phases."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional


class Severity(IntEnum):
    SEV3 = 3
    SEV2 = 2
    SEV1 = 1   # highest


class Environment(Enum):
    STAGING = "staging"
    PROD = "prod"


class Phase(Enum):
    INVESTIGATE = "investigate"
    ACT = "act"


@dataclass(frozen=True)
class Incident:
    incident_id: str
    title: str
    severity: Severity
    environment: Environment
    signals: tuple[str, ...]        # alert symptoms, e.g. ("pod_crashloop",)


@dataclass(frozen=True)
class Action:
    """A proposed action. ``grounded_in`` is the runbook step / prior incident id
    it is based on; ``confidence`` is recorded for audit but never gates."""

    type: str
    environment: Environment
    grounded_in: Optional[str] = None
    target: Optional[str] = None
    confidence: float = 1.0          # audit metadata only — never read by the gate


@dataclass(frozen=True)
class Observation:
    action_type: str
    finding: str
