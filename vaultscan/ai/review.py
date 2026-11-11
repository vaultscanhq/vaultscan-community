from vaultscan.ai.summary import offline_summary


def review(decision, warn=lambda message: None):
    """Placeholder until the model-backed reviewer lands; uses the offline summary."""
    return offline_summary(decision), decision
