"""Simultaneous turns with explicit uniform lotteries and retry rounds."""
from dataclasses import dataclass,replace
from itertools import product
from Task2.core.state import Action,Bullet,Direction

@dataclass(frozen=True)
class Outcome:
    winner:int|None
    reason:str

@dataclass(frozen=True)
class Draft:
    accepted:tuple=()
    reserved:tuple=()
    pending:tuple=()

class GameRules:
    def __init__(self, priority_tank=None):
        self.priority_tank = priority_tank

    def outcome(self,s,check_limit=True):
        lost=[not any(b.team==team and b.hp>0 for b in s.bases) or not any(t.team==team and t.hp>0 for t in s.tanks) for team in (0,1)]
        if all(lost): return Outcome(None,'mutual_destruction')
        if any(lost):
            loser=lost.index(True)
            reason='base_destroyed' if any(b.team==loser and b.hp==0 for b in s.bases) else 'all_tanks_destroyed'
            return Outcome(1-loser,reason)
        if check_limit and s.turn>=s.max_turns:
            counts=[sum(t.team==team for t in s.alive) for team in (0,1)]
            return Outcome(None if counts[0]==counts[1] else int(counts[1]>counts[0]),'turn_limit')
        return None

    def begin(self,s):
        if self.outcome(s) is not None: raise ValueError('Game is over')
        return Draft(pending=tuple(t.id for t in s.alive))

    def destination(self,s,tid,action):
        if not action.name.startswith('MOVE_'): return None
        t=s.tank(tid)
        dx,dy=Direction[action.value].value
        dest=t.x+dx,t.y+dy
        occupied={(e.x,e.y) for e in (*s.alive,*s.bases,*s.walls) if e.hp>0}
        return dest if s.inside(*dest) and dest not in occupied else None

    def actions(self,s,tid,draft=None):
        if s.tank(tid).hp<=0: return ()
        reserved=() if draft is None else draft.reserved
        return tuple(a for a in Action if self.destination(s,tid,a) not in reserved)

    def resolve(self,s,draft,proposals):
        if set(proposals)!=set(draft.pending): raise ValueError('Supply every pending action')
        accepted=dict(draft.accepted)
        groups={}
        for tid,action in proposals.items():
            if action not in self.actions(s,tid,draft): raise ValueError('Invalid action/reserved destination')
            dest=self.destination(s,tid,action)
            if dest is None: accepted[tid]=action
            else: groups.setdefault(dest,[]).append(tid)
        choices=[([self.priority_tank] if self.priority_tank in ids else ids)
                 for ids in groups.values()]
        probability=1
        for ids in choices: probability/=len(ids)
        result=[]
        for winners in (product(*choices) if choices else [()]):
            chosen=dict(accepted)
            pending=[]
            for (dest,ids),winner in zip(groups.items(),winners):
                chosen[winner]=proposals[winner]
                pending.extend(tid for tid in ids if tid!=winner)
            result.append((probability,Draft(tuple(sorted(chosen.items())),draft.reserved+tuple(groups),tuple(sorted(pending)))))
        return result

    def sample(self,outcomes,rng):
        return rng.choices([d for _,d in outcomes],weights=[p for p,_ in outcomes],k=1)[0]

    def execute(self,s,draft):
        if self.outcome(s) is not None: raise ValueError('Game is over')
        if draft.pending or set(dict(draft.accepted))!={t.id for t in s.alive}: raise ValueError('Resolve all actions first')
        actions=dict(draft.accepted)
        tanks=[]
        for t in s.tanks:
            a=actions.get(t.id,Action.STAY)
            if t.hp>0 and a.name.startswith('MOVE_'):
                dest=self.destination(s,t.id,a)
                t=replace(t,direction=Direction[a.value])
                if dest is not None: t=replace(t,x=dest[0],y=dest[1])
            tanks.append(t)
        current=self._collisions(replace(s,tanks=tuple(tanks)),s.bullets)
        if self.outcome(current,False) is None:
            new=tuple(Bullet(t.x,t.y,t.direction,t.id) for t in current.alive if actions[t.id] is Action.FIRE)
            current=replace(current,bullets=current.bullets+new)
            for _ in range(3):
                moved=[]
                for b in current.bullets:
                    dx,dy=b.direction.value
                    if current.inside(b.x+dx,b.y+dy): moved.append(replace(b,x=b.x+dx,y=b.y+dy))
                current=self._collisions(current,moved)
                if self.outcome(current,False) is not None: break
        return replace(current,turn=s.turn+1)

    @staticmethod
    def _collisions(s,bullets):
        entities=(*s.tanks,*s.bases,*s.walls)
        occupied={(e.x,e.y):i for i,e in enumerate(entities) if e.hp>0}
        damage=[0]*len(entities)
        survivors=[]
        for b in bullets:
            i=occupied.get((b.x,b.y))
            if i is None: survivors.append(b)
            else: damage[i]+=1
        updated=[replace(e,hp=max(0,e.hp-damage[i])) for i,e in enumerate(entities)]
        n,m=len(s.tanks),len(s.bases)
        return replace(s,tanks=tuple(updated[:n]),bases=tuple(updated[n:n+m]),walls=tuple(e for e in updated[n+m:] if e.hp>0),bullets=tuple(survivors))
