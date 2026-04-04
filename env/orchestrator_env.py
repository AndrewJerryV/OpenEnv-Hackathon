class Action:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    @staticmethod
    def parse(text):
        if "database" in text:
            return Action("search_logs", "database")
        return Action("noop", "")

class OrchestratorEnv:

    def reset(self):
        self.state = {
            "logs": ["ERROR database timeout"],
            "root_found": False,
            "done": False
        }
        return self.state

    def step(self, action):
        reward = 0
        done = False
        error = None

        if action.type == "search_logs":
            if "database" in action.value:
                self.state["root_found"] = True
                reward = 5
            else:
                reward = -1

        if self.state["root_found"]:
            reward += 10
            done = True

        return {
            "reward": reward,
            "done": done,
            "error": error
        }

    def close(self):
        pass