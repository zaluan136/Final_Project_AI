"""Per-tank search configuration and nemesis selection."""
from random import Random
from task_2.search.algorithms import Searcher, SearchConfig
from task_2.memory.memory import MovementMemory

CONFIGURATIONS={
    'minimax':(False,False),
    'alpha_beta':(True,False),
    'heuristic_minimax':(False,True),
    'heuristic_alpha_beta':(True,True),
}

class SearchAgent:
    def __init__(self,rules,tank_id,mode='heuristic_alpha_beta',depth=2,seed=None,use_nemesis=True):
        ab,heuristic=CONFIGURATIONS[mode]
        self.searcher=Searcher(rules,SearchConfig(depth,ab,heuristic))
        self.tank_id=tank_id
        self.rng=Random(seed)
        self.use_nemesis=use_nemesis
        self.nemesis=None
        self.last_result=None
        self.cancel_event=None
        self.memory=MovementMemory(tank_id)

    def observe_turn(self,before,action,after):
        self.memory.observe(before,action,after)

    def choose_action(self,state,draft,deadline=None):
        enemies=[t.id for t in state.alive if t.team!=state.tank(self.tank_id).team]
        if self.use_nemesis and len(state.alive)>=3 and enemies:
            if self.nemesis not in enemies: self.nemesis=self.rng.choice(enemies)
        else: self.nemesis=None
        self.last_result=self.searcher.choose(state,self.tank_id,draft,deadline,self.nemesis,self.cancel_event,self.memory)
        if self.last_result.action is None: raise ValueError('Game is over')
        return self.last_result.action
