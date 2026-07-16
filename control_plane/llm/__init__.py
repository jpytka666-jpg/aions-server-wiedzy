"""AIONS control_plane.llm -- klient HTTP do rezydentnego llama-server.

Nowy, opcjonalny kanal przyspieszenia ust (Bielik-4.5B). Nic tu nie zmienia
istniejacego mechanizmu wrapper/generate.py (llama-cli subprocess) -- to
tylko dodatkowy, szybszy transport probowany NAJPIERW przez konsumentow
(operator/mouth.py, skills/goal_planner.py), z pelnym fallbackiem do
starej sciezki gdy serwer nie odpowiada.
"""
