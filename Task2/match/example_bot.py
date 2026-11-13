"""Example plugin: select this file for a tank in the temporary UI."""
from Task2.core.rules import GameRules
from Task2.search.algorithms import predicted_action


def choose_action(state, tank_id, draft, deadline):
    # Replace with another group's implementation. Use state, not live intents.
    return predicted_action(GameRules(), state, tank_id, draft)
