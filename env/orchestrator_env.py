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
            "expected_keyword": "payment",
            "expected_crm": "refund",
            "expected_slack": "user",
            "requires_crm": True
        },
        "deployment crash": {
            "initial_logs": ["FATAL error in pod 32 deployment manager"],
            "expected_keyword": "crash",
            "expected_crm": None,
            "expected_slack": "devops",
            "requires_crm": False
        },
        "customer complaint": {
            "initial_logs": ["user ticket: unable to login, site returns 500 error"],
            "expected_keyword": "complaint",
            "expected_crm": "resolved",
            "expected_slack": "customer",
            "requires_crm": True
        }
    }

    def reset(self):
        self.scenario_name = random.choice(list(self.SCENARIOS.keys()))
        self.scenario = self.SCENARIOS[self.scenario_name]
        
        self.state = {
            "task": self.scenario_name,
            "logs": self.scenario["initial_logs"].copy(),
            "crm_status": "open",
            "slack_messages": [],
            "action_history": [],
            "observations": [],
            "root_found": False,
            "crm_updated": False,
            "notified": False,
            "done": False,
        }
        return self.state

    def step(self, action):
        reward = -1  # Base cost per step
        error = None
        done = False
        
        action_repr = f"{action.type} {action.value}".strip()
        
        if action_repr in self.state["action_history"]:
            reward -= 2  # Redundant action
            self.state["observations"].append(f"[Error] Redundant action '{action_repr}'")
            return {"reward": reward, "done": done, "error": error}
            
        self.state["action_history"].append(action_repr)

        if action.type == "search_logs":
            if action.value == self.scenario["expected_keyword"]:
                self.state["root_found"] = True
                reward += 5
                self.state["observations"].append(f"[Success] Found root cause for {action.value}")
            else:
                self.state["observations"].append(f"[Error] No result for keyword '{action.value}'")

        elif action.type == "update_crm":
            if not self.state["root_found"]:
                reward -= 5
                self.state["observations"].append("[Error] Cannot update CRM before finding root cause")
            elif not self.scenario["requires_crm"]:
                reward -= 5
                self.state["observations"].append("[Error] CRM update not required for this task")
            elif action.value == self.scenario["expected_crm"]:
                self.state["crm_updated"] = True
                self.state["crm_status"] = action.value
                reward += 5
                self.state["observations"].append(f"[Success] CRM updated to '{action.value}'")
            else:
                self.state["observations"].append(f"[Error] Invalid CRM status '{action.value}'")

        elif action.type == "send_slack":
            if self.scenario["requires_crm"] and not self.state["crm_updated"]:
                reward -= 5
                self.state["observations"].append("[Error] Cannot send slack before updating CRM")
            elif not self.scenario["requires_crm"] and not self.state["root_found"]:
                reward -= 5
                self.state["observations"].append("[Error] Cannot send slack before finding root cause")
            elif action.value == self.scenario["expected_slack"]:
                self.state["notified"] = True
                self.state["slack_messages"].append(action.value)
                reward += 5
                self.state["observations"].append(f"[Success] Slack sent to '{action.value}'")
            else:
                self.state["observations"].append(f"[Error] Invalid Slack recipient '{action.value}'")

        elif action.type == "finish_task":
            done = True
            is_complete = False
            if self.scenario["requires_crm"]:
                is_complete = self.state["root_found"] and self.state["crm_updated"] and self.state["notified"]
                ideal_steps = 4
            else:
                is_complete = self.state["root_found"] and self.state["notified"]
                ideal_steps = 3

            if is_complete:
                reward += 10 # Task complete
                if len(self.state["action_history"]) <= ideal_steps:
                    reward += 3 # Efficient steps
                self.state["observations"].append("[Success] Task correctly completed.")
            else:
                reward -= 10 # Wrong final answer
                self.state["observations"].append("[Error] Task finished prematurely with incomplete steps.")

        else:
            reward -= 5
            error = f"Unknown action type: {action.type}"
            self.state["observations"].append(f"[Error] Unknown action '{action.type}'")

        self.state["done"] = done
        return {
            "reward": reward,
            "done": done,
            "error": error
        }

    def close(self):
        pass