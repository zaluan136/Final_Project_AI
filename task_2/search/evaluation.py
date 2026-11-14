"""Lecture 07 pp.27-29: cheap EVAL; terminal UTILITY always dominates."""
WIN_SCORE=100_000
from task_2.search.tactics import route, base_threats, bullet_cells

def terminal_value(outcome,team):
    return 0 if outcome.winner is None else (WIN_SCORE if outcome.winner==team else -WIN_SCORE)

def first_target(s,x,y,direction):
    occupied={(e.x,e.y):e for e in (*s.alive,*s.bases,*s.walls) if e.hp>0}
    dx,dy=direction.value
    while s.inside(x+dx,y+dy):
        x,y=x+dx,y+dy
        if (x,y) in occupied: return occupied[x,y]
    return None

def _score(s,team):
    tanks=[t for t in s.alive if t.team==team]
    base=next(b for b in s.bases if b.team==team)
    enemies=[e for e in (*s.alive,*s.bases) if e.team!=team and e.hp>0]
    urgency=1-max(0,s.max_turns-s.turn)/s.max_turns
    score=140*base.hp+(450+1000*urgency)*len(tanks)-200/(base.hp+1)
    for t in tanks:
        score+=100*t.hp-80/(t.hp+1)
        target=first_target(s,t.x,t.y,t.direction)
        if target in enemies: score+=80+100/(target.hp+1)
        if enemies: score-=4*min(abs(t.x-e.x)+abs(t.y-e.y) for e in enemies)
        # Weighted route cost rewards opening a useful wall, or taking a cheaper detour.
        cost, path = route(s,t.id)
        score-=10*min(cost,s.width+s.height+12)
        if (t.x,t.y) in bullet_cells(s,t.id): score-=120/(t.hp+1)
    threats,incoming=base_threats(s,team)
    if threats or incoming:
        score-=250/(base.hp+1)*(len(threats)+int(incoming))
        # Defense routes target the attacker instead of committing to demolition.
        for t in tanks:
            if threats:
                score-=8*min(abs(t.x-e.x)+abs(t.y-e.y) for e in threats)
    for b in s.bullets:
        target=first_target(s,b.x,b.y,b.direction)
        if target is not None and getattr(target,'team',None)==team:
            distance=abs(target.x-b.x)+abs(target.y-b.y)
            score-=(180 if distance<=3 else 50)/(target.hp+1)
    return score

def evaluate(s,team):
    return max(-WIN_SCORE/2,min(WIN_SCORE/2,_score(s,team)-_score(s,1-team)))
