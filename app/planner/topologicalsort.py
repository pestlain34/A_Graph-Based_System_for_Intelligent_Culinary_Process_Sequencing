import heapq
from collections import deque, defaultdict
from typing import List


class Step:
    def __init__(self, id, name, time, active=True, prev=None):
        self.id = id
        self.name = name
        self.time = int(time)
        self.active = bool(active)
        self.prev = [] if prev is None else list(prev)

    def __repr__(self):
        return f"{self.name}({self.time}m, {'active' if self.active else 'passive'})"


def build_adj_and_nodes(steps: List[Step]):
    adj = defaultdict(list)
    nodes = set()
    for s in steps:
        nodes.add(s.id)
        for p in s.prev:
            nodes.add(p.id)
            adj[p.id].append(s.id)
    for nid in list(nodes):
        adj.setdefault(nid, [])
    return adj, nodes


def topologicalsort(steps: List[Step]):
    adj, nodes = build_adj_and_nodes(steps)
    for s in steps:
        nodes.add(s.id)
        adj.setdefault(s.id, [])
    indegree = {nid: 0 for nid in nodes}
    for st in adj:
        for end in adj[st]:
            indegree[end] += 1
    q = deque([nid for nid, d in indegree.items() if d == 0])
    result = []
    while q:
        cur = q.popleft()
        result.append(cur)
        for nb in adj.get(cur, []):
            indegree[nb] -= 1
            if indegree[nb] == 0:
                q.append(nb)
    if len(result) != len(nodes):
        return [], adj
    return result, adj


def calc_all_critical_times(steps: List[Step]):
    memo = {}
    def dfs(s: Step):
        if s.id in memo:
            return memo[s.id]
        if not s.prev:
            memo[s.id] = s.time
            return memo[s.id]
        longest = 0
        for p in s.prev:
            longest = max(longest, dfs(p))
        memo[s.id] = s.time + longest
        return memo[s.id]

    for s in steps:
        dfs(s)
    return memo


def schedule_improved(steps: List[Step]):
    if not steps:
        return []

    id_map = {s.id: s for s in steps}
    adj, _ = build_adj_and_nodes(steps)
    indegree = {s.id: 0 for s in steps}
    for st in adj:
        for end in adj[st]:
            indegree[end] += 1

    critical = calc_all_critical_times(steps)
    prev_end = {s.id: 0 for s in steps}
    done = set()
    plan = []

    def get_ready_nodes():
        ready = []
        for s in steps:
            if s.id in done:
                continue
            if all(p.id in done for p in s.prev):
                ready.append(s)
        return ready

    active_time = 0

    while len(done) < len(steps):
        ready = get_ready_nodes()
        if not ready:
            raise RuntimeError("Поймали цикл в графе, очень плохо")

        passive_ready = [s for s in ready if not s.active]
        passive_ready.sort(key=lambda s: s.time)

        for s in passive_ready:
            start = 0 if not s.prev else max(prev_end[p.id] for p in s.prev)
            end = start + s.time
            prev_end[s.id] = end
            plan.append({"id": s.id, "name": s.name, "start": start, "end": end, "type_of": "passive"})
            done.add(s.id)

        ready = get_ready_nodes()
        active_ready = [s for s in ready if s.active]

        active_heap = []
        for s in active_ready:
            heapq.heappush(active_heap, (-critical[s.id], s.time, s.id))

        while active_heap:
            _, duration, sid = heapq.heappop(active_heap)
            s = id_map[sid]
            earliest_from_preds = 0 if not s.prev else max(prev_end[p.id] for p in s.prev)
            start = max(active_time, earliest_from_preds)
            end = start + duration
            plan.append({"id": s.id, "name": s.name, "start": start, "end": end, "type_of": "active"})
            done.add(s.id)
            prev_end[s.id] = end
            active_time = end

            for succ in adj.get(s.id, []):
                succ_step = id_map[succ]
                if succ_step.id in done:
                    continue
                if all(p.id in done for p in succ_step.prev):
                    if succ_step.active:
                        heapq.heappush(active_heap, (-critical[succ_step.id], succ_step.time, succ_step.id))
                    else:
                        st = 0 if not succ_step.prev else max(prev_end[p.id] for p in succ_step.prev)
                        ed = st + succ_step.time
                        prev_end[succ_step.id] = ed
                        plan.append(
                            {"id": succ_step.id, "name": succ_step.name, "start": st, "end": ed, "type_of": "passive"})
                        done.add(succ_step.id)

    plan.sort(key=lambda x: x["start"])
    return plan

