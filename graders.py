def grade_payment_failure(trajectory) -> float:
    return _grade(trajectory)

def grade_deployment_crash(trajectory) -> float:
    return _grade(trajectory)

def grade_customer_complaint(trajectory) -> float:
    return _grade(trajectory)

def grade_latency_spike(trajectory) -> float:
    return _grade(trajectory)

def _grade(trajectory) -> float:
    logs = " ".join(str(s) for s in trajectory)
    score = 0.0
    if "root_found" in logs or "Root cause confirmed" in logs:
        score += 0.3
    if "mitigated" in logs or "System state stabilized" in logs:
        score += 0.3
    if "notified" in logs or "Notification dispatched" in logs:
        score += 0.3
    if logs.count("[STEP]") <= 4:
        score += 0.1
    return min(max(score, 0.01), 0.99)