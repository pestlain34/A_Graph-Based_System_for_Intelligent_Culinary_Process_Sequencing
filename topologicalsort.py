from collections import deque
import heapq

class Step:
    def __init__(self, id , name , time , active = True , prev = None):
        self.id = id
        self.name = name
        self.time = time
        self.active = active
        self.prev = [] if prev is None else prev

    def __repr__(self):
        return f"{self.name}({self.time}m, {'active' if self.active else 'passive'})"


def schedule(steps):
    id_to_iterate = {s.id: s for s in steps}
    prevTimeEnd = {s.id: 0 for s in steps}
    edges = build_edges(steps)
    res , adj = topologicalsort(steps , edges)
    activetime = 0
    plan = []
    done = set()
    passive_tasks = []
    active_tasks = []
    critical_times = {s.id: calc_critical_times(s, {}) for s in steps}
    for indp_id in res:
        s = id_to_iterate[indp_id]
        if not s.prev:
            if s.active:
                heapq.heappush(active_tasks, (-critical_times[s.id], s.time, s))
            else:
                heapq.heappush(passive_tasks, (s.time , s))

    while len(done) < len(steps):

        for i in range(len(passive_tasks)):
            duration, s = heapq.heappop(passive_tasks)
            if not s.prev:
                start = 0
                end = duration
            else:
                start = max(prevTimeEnd[p.id] for p in s.prev)
                end = start + duration

            prevTimeEnd[s.id] = end
            plan.append((start , end, "passive" , s.name))
            done.add(s.id)
            for nxt in adj[s.id]:
                nxt_step = id_to_iterate[nxt]
                if all(p.id in done for p in nxt_step.prev):
                    if nxt_step.active:
                        heapq.heappush(active_tasks, (-critical_times[nxt_step.id], nxt_step.time, nxt_step))

                    else:
                        heapq.heappush(passive_tasks, (nxt_step.time, nxt_step))

        for i in range(len(active_tasks)):
            _, duration, s = heapq.heappop(active_tasks)
            start = activetime
            end = activetime + duration
            plan.append((start , end, "active" , s.name))
            done.add(s.id)
            activetime = end
            prevTimeEnd[s.id] = end
            for nxt in adj[s.id]:
                nxt_step = id_to_iterate[nxt]
                if all(p.id in done for p in nxt_step.prev):
                    if nxt_step.active:
                        heapq.heappush(active_tasks, (-critical_times[nxt_step.id], nxt_step , nxt_step.time))

                    else:
                        heapq.heappush(passive_tasks, (nxt_step.time, nxt_step))



    print("\n=== План приготовления ===")
    for start, end, kind, name in sorted(plan, key=lambda x: x[0]):
        if kind == "active":
            print(f"[{start:>3}–{end:<3}] выполняем активно: {name}")
        else:
            print(f"[{start:>3}–{end:<3}] пассивно идёт: {name}")


def build_edges(steps):
    edges = []
    for step in steps:
        for prev in step.prev:
            edges.append([prev.id , step.id])
    return edges


def constructadj(edges):
    adj = {}
    nodes = set()
    for st , end in edges:
        nodes.add(st)
        nodes.add(end)
        adj.setdefault(st , []).append(end)
        adj.setdefault(end, [])
    return adj , nodes

def topologicalsort(steps, edges):
    adj , nodes = constructadj(edges)
    for s in steps:
        nodes.add(s.id)
        adj.setdefault(s.id, [])
    indegree = {nid:0 for nid in nodes}

    for st in adj:
        for end in adj[st]:
            indegree[end] += 1

    q = deque([nid for nid, d in indegree.items() if d == 0])
    result = []
    while q:
        cur = q.popleft()
        result.append(cur)
        for neighbour in adj.get(cur , []):
            indegree[neighbour] -= 1
            if indegree[neighbour] == 0:
                q.append(neighbour)

    if len(result) != len(nodes):
        print("Ошибка: граф содержит цикл, нельзя составить план.")
        return [] , adj
    return result , adj

def calc_critical_times(step , memo):
    if step.id in memo:
        return memo[step.id]

    if not step.prev:
        memo[step.id] = step.time

    else:
        memo[step.id] = step.time + max(calc_critical_times(p , memo) for p in step.prev)
    return memo[step.id]

if __name__ == "__main__":
    step_spaghetti1 = Step(1 , "boil water" , 10 , active = False)
    step_spaghetti2 = Step(2 , "boil sphagetti", 8 , active = False)
    step_spaghetti2.prev.append(step_spaghetti1)
    step_spaghetti3 = Step(3 , "make a sauce" , 5 , active = True)
    step_bread1 = Step(4 , "make testo" , 15 , active = True)
    step_bread2 = Step(5 , "bake testo" , 20 , active = False)
    step_bread2.prev.append(step_bread1)
    steps = [step_spaghetti1, step_spaghetti2, step_spaghetti3, step_bread1, step_bread2]
    V = len(steps)
    edges = build_edges(steps)
    result , adj = topologicalsort(steps, edges)
    if result:
        print("Topological Order:", result)

    schedule(steps)





