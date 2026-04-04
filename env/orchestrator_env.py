import random

class Action:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    @staticmethod
    def parse(text):
        parts = text.strip().split(" ", 1)
        if len(parts) == 2:
            return Action(parts[0], parts[1])
        elif len(parts) == 1 and parts[0]:
            return Action(parts[0], "")
        return Action("noop", "")

class OrchestratorEnv:
    SCENARIOS = {
        "payment failure": {
            "initial_logs": ["payment gateway timeout 504 on user checkout"],
            "expected_steps": [
                {"action": "search_logs", "value": "payment"},
                {"action": "update_crm", "value": "refund"},
                {"action": "send_slack", "value": "user"},
                {"action": "finish_task", "value": ""}
            ]
        },
        "deployment crash": {
            "initial_logs": ["FATAL error in pod 32 deployment manager"],
            "expected_steps": [
                {"action": "search_logs", "value": "crash"},
                {"action": "send_slack", "value": "devops"},
                {"action": "finish_task", "value": ""}
            ]
        },
        "customer complaint": {
            "initial_logs": ["user ticket: unable to login, site returns 500 error"],
            "expected_steps": [
                {"action": "search_logs", "value": "complaint"},
                {"action": "update_crm", "value": "resolved"},
                {"action": "send_slack", "value": "customer"},
                {"action": "finish_task", "value": ""}
            ]
        }
    }

    def reset(self):
        self.scenario_name = random.choice(list(self.SCENARIOS.keys()))
        scenario = self.SCENARIOS[self.scenario_name]
        
        self.state = {
            "task": self.scenario_name,
            "logs": scenario["initial_logs"].copy(),
            "crm_status": "open",
            "slack_messages": [],
            "action_history": [],
            "step_index": 0,
            "done": False,
            "expected_steps": scenario["expected_steps"]
        }
        return self.state

    def step(self, action):
        reward = 0
        error = None
        done = False
        
        action_repr = f"{action.type} {action.value}".strip()
        
        if action_repr in self.state["action_history"]:
            reward -= 2  # Redundant action
        else:
            self.state["action_history"].append(action_repr)
            
            expected_steps = self.state["expected_steps"]
            current_idx = self.state["step_index"]
            
            if current_idx < len(expected_steps):
                expected_act = expected_steps[current_idx]
                if action.type == expected_act["action"] and action.value == expected_act["value"]:
                    reward += 5
                    self.state["step_index"] += 1
                else:
                    if action.type in ["search_logs", "update_crm", "send_slack", "finish_task"]:
                        reward -= 5
                        error = f"Wrong step. Expected: {expected_act['action']} {expected_act['value']}".strip()
                    else:
                        reward -= 1
                        error = f"Unknown action type: {action.type}"
            else:
                reward -= 5

        if action.type == "finish_task":
            done = True

        if done:
            if self.state["step_index"] == len(self.state["expected_steps"]):
                reward += 10 # task complete
                if len(self.state["action_history"]) == len(self.state["expected_steps"]):
                    reward += 3 # efficient steps

        self.state["done"] = done
        return {
            "reward": reward,
            "done": done,
            "error": error
        }

    def close(self):
        pass