# src/algorithms/repair_swap.py
def border_swaps(G, assignment, geoid_to_pop, target, tol, max_iters=5000):
    """
    Greedy boundary swap: move a border node from the largest-over target district
    to the smallest-under target neighbor if it reduces max deviation and keeps contiguity.
    """
    from collections import defaultdict
    def district_pop():
        acc = defaultdict(int)
        for n, d in assignment.items(): acc[d] += geoid_to_pop[n]
        return acc
    def deviation(p): return abs(p - target)/target

    region_pop = district_pop()
    for _ in range(max_iters):
        # find worst-offender (highest deviation)
        worst = max(region_pop, key=lambda d: deviation(region_pop[d]))
        # candidate border nodes in 'worst'
        border = [n for n in G.nodes if assignment[n]==worst and any(assignment[m]!=worst for m in G.neighbors(n))]
        improved = False
        for n in border:
            # neighbors’ districts
            nbr_ds = {assignment[m] for m in G.neighbors(n) if assignment[m]!=worst}
            # try moving to the neighbor district with lowest pop
            target_d = min(nbr_ds, key=lambda d: region_pop[d])
            new_pop_worst = region_pop[worst] - geoid_to_pop[n]
            new_pop_target = region_pop[target_d] + geoid_to_pop[n]
            old_max = max(deviation(p) for p in region_pop.values())
            new_max = max(max(deviation(new_pop_worst), deviation(new_pop_target)),
                          *[deviation(p) for d,p in region_pop.items() if d not in (worst,target_d)])
            if new_max < old_max:
                assignment[n] = target_d
                region_pop[worst] = new_pop_worst
                region_pop[target_d] = new_pop_target
                improved = True
                break
        if not improved: break
    return assignment
