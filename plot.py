import json, matplotlib.pyplot as plt
from datetime import datetime

points = []
with open("results.json", encoding="utf-8") as f:
    for line in f:
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "Point" and o.get("metric") == "http_reqs":
            t = datetime.fromisoformat(o["data"]["time"].replace("Z", "+00:00"))
            points.append(t)

if not points:
    print("no http_reqs found")
    raise SystemExit

points.sort()
t0 = points[0]
per_sec = {}
for t in points:
    s = int((t - t0).total_seconds())
    per_sec[s] = per_sec.get(s, 0) + 1

xs = sorted(per_sec)
ys = [per_sec[x] for x in xs]

# real values observed from kubectl get hpa -w during this run
rep_x = [0, 30, 60, 90, 120, 180, 240]
rep_y = [2, 2, 3, 5, 5, 5, 5]

fig, ax1 = plt.subplots(figsize=(8, 4))
ax1.plot(rep_x, rep_y, 'b-o', label='replicas')
ax1.set_xlabel('seconds since load start')
ax1.set_ylabel('replicas', color='b')
ax1.tick_params(axis='y', labelcolor='b')

ax2 = ax1.twinx()
ax2.plot(xs, ys, 'r-', alpha=0.6, label='requests/sec')
ax2.set_ylabel('requests/sec', color='r')
ax2.tick_params(axis='y', labelcolor='r')

plt.title('Replicas vs offered load')
plt.tight_layout()
plt.savefig('docs/evidence/replicas-vs-load.png', dpi=150)
print("saved")