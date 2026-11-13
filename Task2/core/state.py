"""Immutable snapshots; team 0/1, neutral tanks allowed only in setup."""
from dataclasses import dataclass
from enum import Enum

class Direction(Enum):
    UP=(0,-1)
    DOWN=(0,1)
    LEFT=(-1,0)
    RIGHT=(1,0)

class Action(Enum):
    MOVE_UP='UP'
    MOVE_DOWN='DOWN'
    MOVE_LEFT='LEFT'
    MOVE_RIGHT='RIGHT'
    FIRE='FIRE'
    STAY='STAY'

@dataclass(frozen=True)
class Tank:
    id:int
    x:int
    y:int
    direction:Direction
    team:int|None=None
    hp:int=6

@dataclass(frozen=True)
class Base:
    team:int
    x:int
    y:int
    hp:int=9

@dataclass(frozen=True)
class Wall:
    x:int
    y:int
    hp:int=3

@dataclass(frozen=True)
class Bullet:
    x:int
    y:int
    direction:Direction
    owner:int

@dataclass(frozen=True)
class GameState:
    width:int
    height:int
    tanks:tuple[Tank,...]
    bases:tuple[Base,...]
    walls:tuple[Wall,...]=()
    bullets:tuple[Bullet,...]=()
    turn:int=0
    max_turns:int=300

    def __post_init__(self):
        for name in ('tanks','bases','walls','bullets'):
            object.__setattr__(self,name,tuple(getattr(self,name)))
        if self.width<1 or self.height<1 or self.turn<0:
            raise ValueError('Invalid dimensions/turn')
        if type(self.max_turns) is not int or self.max_turns<1:
            raise ValueError('max_turns must be a positive integer')
        if len(self.tanks)>4 or len(self.bases)>2:
            raise ValueError('At most four tanks and two bases')
        if len({t.id for t in self.tanks})!=len(self.tanks):
            raise ValueError('Duplicate tank IDs')
        if any(t.team not in (None,0,1) for t in self.tanks):
            raise ValueError('Invalid tank team')
        if any(b.team not in (0,1) for b in self.bases) or len({b.team for b in self.bases})!=len(self.bases):
            raise ValueError('Each base creates a unique team')
        entities=(*self.tanks,*self.bases,*self.walls)
        if any(not self.inside(e.x,e.y) or e.hp<0 for e in entities):
            raise ValueError('Invalid entity position/HP')
        occupied=[(e.x,e.y) for e in entities if e.hp>0]
        if len(occupied)!=len(set(occupied)):
            raise ValueError('Entities overlap')
        if any(not self.inside(b.x,b.y) or b.owner not in {t.id for t in self.tanks} for b in self.bullets):
            raise ValueError('Invalid bullet')
        if any(not isinstance(t.direction,Direction) for t in self.tanks):
            raise ValueError('Invalid direction')

    def inside(self,x,y):
        return 0<=x<self.width and 0<=y<self.height

    def tank(self,tank_id):
        return next(t for t in self.tanks if t.id==tank_id)

    @property
    def alive(self):
        return tuple(t for t in self.tanks if t.hp>0)

    def validate_ready(self):
        if {b.team for b in self.bases}!={0,1} or len(self.tanks)<2:
            raise ValueError('Place two bases and two to four tanks')
        if any(t.team is None for t in self.tanks):
            raise ValueError('Assign every tank to a team')
        if any(not any(t.team==team and t.hp>0 for t in self.tanks) for team in (0,1)):
            raise ValueError('Each team needs a live tank')
        if any(e.hp<=0 for e in (*self.tanks,*self.bases)):
            raise ValueError('Cannot start with destroyed entities')
