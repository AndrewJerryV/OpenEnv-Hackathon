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
    # UPDATED: Keys now use underscores to match openenv.yaml tasks
    SCENARIOS = {
        "payment_failure": {
            "initial_logs": ["[Alert] user_checkout_error: payment gateway latency spike detected at cluster-504"],
            "keywords": ["payment", "gateway", "latency"],
            "resolution_paths": {
                "admin": {"update_crm": "refund", "send_slack": "user"},
                "technical": {"run_command": "restart_service", "send_slack": "devops"}
            }
        },
        "deployment_crash": {
            "initial_logs": ["[Alert] pod_crash_loop: FATAL signal 9 in pod-32-deploy-manager during sync"],
            "keywords": ["crash", "pod", "deploy"],
            "resolution_paths": {
                "rollback": {"run_command": "rollback_deploy", "send_slack": "devops"},
                "restart": {"run_command": "restart_cluster", "send_slack": "devops"}
            }
        },
        "customer_complaint": {
            "initial_logs": ["[Ticket#993] User states unable to login, site returns constant 500 error on auth endpoint"],
            "keywords": ["complaint", "login", "auth", "500"],
            "resolution_paths": {
                "standard": {"update_crm": "resolved", "send_slack": "customer"},
                "technical": {"run_command": "flush_cache", "send_slack": "devops"}
            }
        }
    }

    def reset(self, scenario_name=None):
        # UPDATED: Allow resetting to a specific scenario provided by the orchestrator
        if scenario_name and scenario_name in self.SCENARIOS:
            self.scenario_name = scenario_name
        else:
            self.scenario_name = random.choice(list(self.SCENARIOS.keys()))
            
        self.scenario = self.SCENARIOS[self.scenario_name]
        
        path_scores = []
        for path in self.scenario["resolution_paths"].values():
            steps = 1 + len(path) + 1
            path_scores.append(-steps + (len(path) + 1) * 5 + 10 + 3)
        self.max_score = float(max(path_scores)) if path_scores else 24.0

        self.state = {
            "task": self.scenario_name,
            "logs": self.scenario["initial_logs"].copy(),
            "action_history": [],
            "observations": [],
            "root_found": False,
            "mitigated": False,
            "mitigation_path": None,
            "notified": False,
            "done": False,
            "noise_level": 0,
            "max_score": self.max_score
        }
        return self.state

    def add_observation(self, msg_type, content):
        if self.state["noise_level"] > 2 and random.random() < 0.3:
            noisy_additions = [
                "[WARNING] Transient network jitter detected.",
                "[INFO] Unrelated background process sync triggered.",
                "[WARNING] Partial data corruption reported."
            ]
            if self.state["noise_level"] > 5 and random.random() < 0.5:
                noisy_additions.append("[CRITICAL] Ghost processes overriding state. Recalibration advised.")
            self.state["observations"].append(random.choice(noisy_additions))
        self.state["observations"].append(f"[{msg_type}] {content}")

    def step(self, action):
        reward = -1  
        error = None
        done = False
        
        action_repr = f"{action.type} {action.value}".strip()
        
        if action_repr in self.state["action_history"]:
            reward -= 2
            self.state["noise_level"] += 1
            self.add_observation("ERROR", "Sequence violation detected: Redundant duplicate action.")
            if self.state["noise_level"] > 3: reward -= 1
            return {"reward": reward, "done": done, "error": error}
            
        self.state["action_history"].append(action_repr)

        if action.type == "search_logs":
            matched = False
            for kw in self.scenario["keywords"]:
                if action.value == kw:
                    self.state["root_found"] = True
                    reward += 5
                    self.add_observation("INFO", "Root cause confirmed, mitigation recommended.")
                    self.state["logs"].append(f"[System] Root cause confirmed: {action.value}")
                    matched = True
                    break
                elif action.value in kw or kw in action.value:
                    if len(action.value) >= 3:
                        reward += 2
                        self.add_observation("WARNING", "Partial match, consider refining query.")
                        self.state["logs"].append(f"[System] Partial diagnostic signal detected for '{action.value}'")
                        matched = True
                        break
            if not matched:
                reward -= 1
                self.state["noise_level"] += 1
                self.add_observation("WARNING", f"Action ineffective, refine approach. No log results found for '{action.value}'.")

        elif action.type in ["update_crm", "run_command"]:
            if not self.state["root_found"]:
                reward -= 5
                self.state["noise_level"] += 1
                self.add_observation("ERROR", f"Sequence violation detected: Cannot execute '{action.type}' before root cause is found.")
            else:
                valid_resolution = False
                for path_name, path_data in self.scenario["resolution_paths"].items():
                    if action.type in path_data and path_data[action.type] == action.value:
                        self.state["mitigated"] = True
                        self.state["mitigation_path"] = path_name
                        reward += 5
                        self.add_observation("INFO", f"System state stabilized post-action: '{action.value}' applied.")
                        
                        if action.type == "run_command":
                            if action.value == "restart_service" or action.value == "restart_cluster":
                                self.state["logs"].append("[System] Service restarted successfully, latency normalized")
                            elif action.value == "rollback_deploy":
                                self.state["logs"].append("[System] Deployment rolled back to stable version")
                            elif action.value == "flush_cache":
                                self.state["logs"].append("[System] Cache cleared, authentication flow restored")
                            else:
                                self.state["logs"].append(f"[System] Command '{action.value}' executed successfully")
                        elif action.type == "update_crm":
                            self.state["logs"].append(f"[System] System state updated, issue stabilized via CRM status '{action.value}'")
                        
                        valid_resolution = True
                        break
                if not valid_resolution:
                    reward -= 2
                    self.state["noise_level"] += 1
                    self.add_observation("WARNING", f"Action ineffective, refine approach. Invalid parameters for {action.type}: '{action.value}'.")

        elif action.type == "send_slack":
            if not self.state["root_found"] or not self.state["mitigated"]:
                reward -= 5
                self.state["noise_level"] += 1
                self.add_observation("ERROR", "Sequence violation detected: Cannot notify prior to mitigation.")
            else:
                valid_slack = False
                path_data = self.scenario["resolution_paths"][self.state["mitigation_path"]]
                if "send_slack" in path_data and path_data["send_slack"] == action.value:
                    self.state["notified"] = True
                    reward += 5
                    self.add_observation("INFO", f"Notification dispatched to '{action.value}'.")
                    self.state["logs"].append(f"[System] Team notified via '{action.value}'")
                    valid_slack = True
                
                if not valid_slack:
                    reward -= 2
                    self.state["noise_level"] += 1
                    self.add_observation("WARNING", f"Action ineffective, refine approach. Invalid slack recipient '{action.value}'.")

        elif action.type == "finish_task":
            done = True
            is_complete = self.state["root_found"] and self.state["mitigated"] and self.state["notified"]

            if is_complete:
                reward += 10
                if len(self.state["action_history"]) <= 4:
                    reward += 3
                self.add_observation("INFO", "Task correctly completed and closed.")
            else:
                reward -= 10
                self.add_observation("ERROR", "Sequence violation detected: Task abandoned prematurely.")

        else:
            reward -= 5
            self.state["noise_level"] += 1
            error = f"Unknown action type: {action.type}"
            self.add_observation("ERROR", f"Sequence violation detected: Unknown tool attempt.")

        if self.state["noise_level"] > 3:
            reward -= 1

        self.state["done"] = done
        return {
            "reward": reward,
            "done": done,
            "error": error,
            "score": self.compute_score() if done else None
        }

    def close(self):
        pass

    def compute_score(self):
        score = 0.0

        if self.state["root_found"]:
            score += 0.3
        if self.state["mitigated"]:
            score += 0.3
        if self.state["notified"]:
            score += 0.3

        steps = len(self.state["action_history"])
        if steps <= 4:
            score += 0.1

        # This clamping ensures scores are strictly (0, 1)
        return min(max(score, 0.01), 0.99)