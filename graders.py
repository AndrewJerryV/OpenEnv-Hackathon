import math

def clamp_score(score: float) -> float:
    """
    Hackathon Requirement: The grader score must strictly be 
    between 0.01 and 0.99. Exactly 0.0 or 1.0 will fail validation.
    """
    return max(0.01, min(0.99, float(score)))

class PaymentFailureGrader:
    def grade(self, env, *args, **kwargs) -> float:
        raw_score = 0.01
        
        # safely access the environment state
        state = getattr(env, 'state', {})
        if isinstance(state, dict):
            action_history = state.get("action_history", [])
            
            # Example logic: If the agent used the "finish_task" tool, give it a high score.
            # You can customize this to check for specific commands or Slack messages!
            if any("finish_task" in str(action).lower() for action in action_history):
                raw_score = 0.99
            elif len(action_history) > 0:
                raw_score = 0.50 # Partial credit for trying actions
                
        return clamp_score(raw_score)

class DeploymentCrashGrader:
    def grade(self, env, *args, **kwargs) -> float:
        raw_score = 0.01
        
        state = getattr(env, 'state', {})
        if isinstance(state, dict):
            action_history = state.get("action_history", [])
            
            if any("finish_task" in str(action).lower() for action in action_history):
                raw_score = 0.99
            elif len(action_history) > 0:
                raw_score = 0.50
                
        return clamp_score(raw_score)

class CustomerComplaintGrader:
    def grade(self, env, *args, **kwargs) -> float:
        raw_score = 0.01
        
        state = getattr(env, 'state', {})
        if isinstance(state, dict):
            action_history = state.get("action_history", [])
            
            if any("finish_task" in str(action).lower() for action in action_history):
                raw_score = 0.99
            elif len(action_history) > 0:
                raw_score = 0.50
                
        return clamp_score(raw_score)

class LatencySpikeGrader:
    def grade(self, env, *args, **kwargs) -> float:
        raw_score = 0.01
        
        state = getattr(env, 'state', {})
        if isinstance(state, dict):
            action_history = state.get("action_history", [])
            
            if any("finish_task" in str(action).lower() for action in action_history):
                raw_score = 0.99
            elif len(action_history) > 0:
                raw_score = 0.50
                
        return clamp_score(raw_score)