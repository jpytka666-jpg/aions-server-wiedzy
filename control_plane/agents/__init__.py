"""AIONS Agent Engine — agents as CBMS blocks (role objects).

Same plug-and-play discovery mechanic as control_plane.skills: drop a
folder into agents_lib/ with an agent.json and the role is discovered
automatically, no core code changes required. An agent owns no execution
code of its own -- it is a declarative, risk-capped VIEW onto the existing
skill registry/executor/gate (control_plane.skills.*).
"""
