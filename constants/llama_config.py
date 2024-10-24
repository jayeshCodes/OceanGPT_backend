import os
import json

script_dir = os.path.dirname(__file__)

# load all paths here
config_path = os.path.join(script_dir, "config.json")
tools_path = os.path.join(script_dir, "tools.json")

# load config variables here
with open(config_path, "r") as f:
    config = json.load(f)

with open(tools_path, "r") as f:
    tools = json.load(f)

# assign variables here
model = config[0]["model"]
system = config[1]["system_prompt"] + f"Here are the tools you have available:\n {tools}"