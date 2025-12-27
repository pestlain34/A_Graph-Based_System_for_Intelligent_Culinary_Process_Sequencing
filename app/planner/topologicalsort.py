from collections import defaultdict, deque

class Step:
    def __init__(self, id, name, time, active=True, prev=None, description=''):
        self.id = id
        self.name = name
        self.time = int(time)
        self.active = bool(active)
        self.prev = [] if prev is None else list(prev)
        self.description = description

    def __repr__(self):
        return f"Step({self.id}, {self.name}, {self.time}m, {'A' if self.active else 'P'})"



def normalize_steps_prev(steps):
    id_map = {s.id: s for s in steps}
    for s in steps:
        normalized = []
        for p in s.prev:
            if isinstance(p, Step):
                normalized.append(p)
            else:
                if p not in id_map:
                    raise ValueError(f"prev содержит неизвестный id: {p}")
                normalized.append(id_map[p])
        s.prev = normalized
    return steps


def build_graph(steps):
    adj = defaultdict(list)
    nodes = set()
    for s in steps:
        nodes.add(s.id)
        for p in s.prev:
            nodes.add(p.id)
            adj[p.id].append(s.id)
    for n in list(nodes):
        adj.setdefault(n, [])
    return adj, nodes


def topo_sort(nodes, adj):
    indeg = {n: 0 for n in nodes}
    for u in adj:
        for v in adj[u]:
            indeg[v] += 1
    q = deque(n for n, d in indeg.items() if d == 0)
    topo = []
    while q:
        u = q.popleft()
        topo.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if len(topo) != len(nodes):
        return None, False
    return topo, True


def compute_critical_times(steps):
    normalize_steps_prev(steps)
    id_map = {s.id: s for s in steps}
    adj, nodes = build_graph(steps)
    topo, ok = topo_sort(nodes, adj)
    if not ok:
        raise RuntimeError("Graph has a cycle")
    critical = {}
    for nid in reversed(topo):
        dur = id_map[nid].time if nid in id_map else 0
        if not adj[nid]:
            critical[nid] = dur
        else:
            critical[nid] = dur + max(critical[child] for child in adj[nid])
    return critical



def simulate_schedule_full(steps, active_order):
    normalize_steps_prev(steps)
    id_map = {s.id: s for s in steps}

    if not active_order:
        active_ids = []
    else:
        if isinstance(active_order[0], Step):
            active_ids = [s.id for s in active_order]
        else:
            active_ids = list(active_order)

    active_finish = {}
    t = 0
    for aid in active_ids:
        step = id_map[aid]
        t_start = t
        t_end = t_start + step.time
        active_finish[aid] = t_end
        t = t_end

    def compute_passive_finish(active_finish_local):
        finish = dict(active_finish_local)
        adj, nodes = build_graph(steps)
        indeg = {n: 0 for n in nodes}
        for u in adj:
            for v in adj[u]:
                indeg[v] += 1
        q = deque(n for n, d in indeg.items() if d == 0)
        topo = []
        while q:
            u = q.popleft()
            topo.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        for nid in topo:
            if nid in finish or nid not in id_map:
                continue
            step = id_map[nid]
            if step.active:
                continue
            t_start = 0
            for p in step.prev:
                t_start = max(t_start, finish.get(p.id, 0))
            finish[nid] = t_start + step.time
        return finish

    passive_finish = compute_passive_finish(active_finish)
    active_finish_final = {}
    t = 0
    for aid in active_ids:
        step = id_map[aid]
        t_start = t
        for p in step.prev:
            if p.active:
                t_start = max(t_start, active_finish_final.get(p.id, 0))
            else:
                t_start = max(t_start, passive_finish.get(p.id, 0))
        t_end = t_start + step.time
        active_finish_final[aid] = t_end
        t = t_end

    passive_finish_final = compute_passive_finish(active_finish_final)

    max_active = max(active_finish_final.values()) if active_finish_final else 0
    max_passive = 0
    for s in steps:
        if not s.active:
            max_passive = max(max_passive, passive_finish_final.get(s.id, 0))
    return max(max_active, max_passive)


def build_schedule_from_active_order(steps, active_order):
    normalize_steps_prev(steps)
    id_map = {s.id: s for s in steps}

    if not active_order:
        active_ids = []
    else:
        if isinstance(active_order[0], Step):
            active_ids = [s.id for s in active_order]
        else:
            active_ids = list(active_order)

    finished = {}
    schedule = []
    active_time = 0

    def schedule_ready_passives():
        made_progress = True
        while made_progress:
            made_progress = False
            for s in steps:
                if s.active or s.id in finished:
                    continue
                if all(p.id in finished for p in s.prev):
                    start = 0 if not s.prev else max(finished[p.id] for p in s.prev)
                    end = start + s.time
                    finished[s.id] = end
                    schedule.append({
                        'id': s.id,
                        'name': s.name,
                        'start': start,
                        'end': end,
                        'type_of': 'passive'
                    })
                    made_progress = True

    schedule_ready_passives()

    for aid in active_ids:
        if aid not in id_map:
            raise ValueError(f"Unknown active id in order: {aid}")
        s = id_map[aid]
        earliest_from_preds = 0 if not s.prev else max(finished.get(p.id, 0) for p in s.prev)
        start = max(active_time, earliest_from_preds)
        end = start + s.time
        finished[s.id] = end
        schedule.append({
            'id': s.id,
            'name': s.name,
            'start': start,
            'end': end,
            'type_of': 'active'
        })
        active_time = end
        schedule_ready_passives()

    schedule_ready_passives()

    schedule.sort(key=lambda x: (x['start'], 0 if x['type_of'] == 'active' else 1))
    return schedule




def optimal_schedule(steps):
    normalize_steps_prev(steps)
    id_map = {s.id: s for s in steps}
    active_ids = [s.id for s in steps if s.active]

    crit = compute_critical_times(steps)

    done = set()
    greedy_order = []
    while len(greedy_order) < len(active_ids):
        ready = []
        for s in steps:
            if not s.active or s.id in done:
                continue
            if all((p.id in done or not p.active) for p in s.prev):
                ready.append(s.id)
        if not ready:
            break
        next_id = max(ready, key=lambda x: crit.get(x, 0))
        greedy_order.append(next_id)
        done.add(next_id)

    best_order = greedy_order.copy()
    best_time = simulate_schedule_full(steps, best_order)

    def dfs(done_set, elapsed, seq):
        nonlocal best_time, best_order
        if len(done_set) == len(active_ids):
            total_time = simulate_schedule_full(steps, seq)
            if total_time < best_time:
                best_time = total_time
                best_order = seq.copy()
            return
        rem = sum(id_map[i].time for i in active_ids if i not in done_set)
        if elapsed + rem >= best_time:
            return
        ready = []
        for s in steps:
            if not s.active or s.id in done_set:
                continue
            if any(p.active and p.id not in done_set for p in s.prev):
                continue
            skip = False
            for p in s.prev:
                if not p.active:
                    for ap in p.prev:
                        if ap.active and ap.id not in done_set:
                            skip = True
                            break
                    if skip:
                        break
            if skip:
                continue
            ready.append(s.id)
        ready.sort(key=lambda x: crit.get(x, 0), reverse=True)
        for aid in ready:
            done_set.add(aid)
            seq.append(aid)
            dfs(done_set, elapsed + id_map[aid].time, seq)
            done_set.remove(aid)
            seq.pop()

    dfs(set(), 0, [])

    order_steps = [id_map[i] for i in best_order]
    plan = build_schedule_from_active_order(steps, best_order)
    makespan = simulate_schedule_full(steps, best_order)
    return {'order_steps': order_steps, 'plan': plan, 'time': makespan}

#пример
if __name__ == "__main__":
    s1 = Step(1, "Порезать овощи", 10, active=True)
    s2 = Step(2, "Мариновать", 30, active=False, prev=[1])
    s3 = Step(3, "Разогреть духовой шкаф", 5, active=True)
    s4 = Step(4, "Запечь", 25, active=False, prev=[3, 2])
    s5 = Step(5, "Подача", 2, active=True, prev=[4])

    steps = [s1, s2, s3, s4, s5]

    res = optimal_schedule(steps)
    print("Makespan:", res['time'])
    print("Order of active steps:", res['order_steps'])
    print("Plan:")
    for item in res['plan']:
        print(item)
