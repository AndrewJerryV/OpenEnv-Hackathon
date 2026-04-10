"""
Grader functions for each task.
Each grader receives the environment interaction log and returns a score in [0.0, 1.0].

The Scaler platform discovers these via the `grader:` field in openenv.yaml,
which uses the Python import path format: `graders:grade_<task_name>`.
"""
import re


def _extract_end_score(stdout: str) -> float:
    """Parse the [END] log line to extract the score."""
    match = re.search(r"\[END\].*?score=([0-9.]+)", stdout)
    if match:
        return min(max(float(match.group(1)), 0.0), 1.0)
    return 0.0


def _extract_rewards(stdout: str) -> list:
    """Parse the [END] log line to extract individual step rewards."""
    match = re.search(r"\[END\].*?rewards=([0-9.,]+)", stdout)
    if match:
        return [float(r) for r in match.group(1).split(",") if r]
    return []


def grade_payment_failure(stdout: str, **kwargs) -> float:
    """Grade the payment_failure task. Returns score in [0.0, 1.0]."""
    score = _extract_end_score(stdout)
    return score


def grade_deployment_crash(stdout: str, **kwargs) -> float:
    """Grade the deployment_crash task. Returns score in [0.0, 1.0]."""
    score = _extract_end_score(stdout)
    return score


def grade_customer_complaint(stdout: str, **kwargs) -> float:
    """Grade the customer_complaint task. Returns score in [0.0, 1.0]."""
    score = _extract_end_score(stdout)
    return score
