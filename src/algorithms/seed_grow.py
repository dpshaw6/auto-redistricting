import math, random
import networkx as nx
import pandas as pd

def seed_nodes(G: nx.Graph, geoid_to_pop: dict, k: int):
    # pick k seeds weighted by population clusters (naive: random heavy nodes)
    nodes = list(G.nodes())
    weights = [max(geoid_to_pop[n],1) for n in nodes]
    seeds = set()
    while len(seeds) < k:
        seeds.add(random.choices(nodes, weights=weights, k=1)[0])
    return list(seeds)

def grow_regions(G: nx.Graph, geoid_to_pop: dict, k: int, target_pop: float, tol: float):
    # region assignment via BFS expansion from seeds until near target_pop
    seeds = seed_nodes(G, geoid_to_pop, k)
    assignment = {n: None for n in G.nodes()}
    region_pop = [0]*k
    frontiers = [set([s]) for s in seeds]
    for r, s in enumerate(seeds):
        assignment[s] = r
        region_pop[r] += geoid_to_pop[s]

    # Pre-build neighbor order for speed
    nbrs = {n: list(G.neighbors(n)) for n in G.nodes()}

    changed = True
    while changed:
        changed = False
        for r in range(k):
            # expand until within tolerance
            if region_pop[r] >= target_pop*(1-tol):
                continue
            # frontier = unassigned neighbors of any assigned node in region r
            frontier = set()
            for n in list(assignment):
                if assignment[n]==r:
                    for m in nbrs[n]:
                        if assignment[m] is None:
                            frontier.add(m)
            # pick the heaviest node first (greedy) to converge faster
            frontier = sorted(frontier, key=lambda n: geoid_to_pop[n], reverse=True)
            for cand in frontier:
                if assignment[cand] is None and region_pop[r] + geoid_to_pop[cand] <= target_pop*(1+tol):
                    assignment[cand] = r
                    region_pop[r] += geoid_to_pop[cand]
                    changed = True
                    if region_pop[r] >= target_pop*(1 - tol):
                        break

    # Repair pass: assign any leftover nodes to adjacent region with lowest pop that keeps contiguity
    leftovers = [n for n,a in assignment.items() if a is None]
    for n in leftovers:
        options = [assignment[m] for m in nbrs[n] if assignment[m] is not None]
        if not options:
            options = list(range(k))
        # choose region with smallest pop
        r = min(set(options), key=lambda r_: region_pop[r_])
        assignment[n] = r
        region_pop[r] += geoid_to_pop[n]

    return assignment, region_pop
