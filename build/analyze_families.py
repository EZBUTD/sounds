# Family vs sound-similarity analysis + UPGMA clustering + heatmap ordering.
# Tests: language family != sound-system similarity.
# Emits docs/analysis.js (families, heatmap order, headline stats).
import json
import statistics
from itertools import combinations

FAMILIES = {
    "English": "Indo-European", "German": "Indo-European", "Dutch": "Indo-European",
    "French": "Indo-European", "Spanish": "Indo-European", "Portuguese": "Indo-European",
    "Italian": "Indo-European", "Russian": "Indo-European", "Ukrainian": "Indo-European",
    "Polish": "Indo-European", "Greek": "Indo-European", "Persian": "Indo-European",
    "Hindi": "Indo-European", "Bengali": "Indo-European",
    "Marathi": "Indo-European", "Punjabi": "Indo-European",
    "Arabic (MSA)": "Afro-Asiatic",
    "Hebrew": "Afro-Asiatic", "Amharic": "Afro-Asiatic", "Hausa": "Afro-Asiatic",
    "Mandarin Chinese": "Sino-Tibetan", "Cantonese": "Sino-Tibetan",
    "Telugu": "Dravidian", "Tamil": "Dravidian",
    "Indonesian": "Austronesian", "Tagalog": "Austronesian",
    "Swahili": "Niger-Congo", "Yoruba": "Niger-Congo", "Zulu": "Niger-Congo",
    "Japanese": "Japonic", "Korean": "Koreanic", "Turkish": "Turkic",
    "Vietnamese": "Austroasiatic", "Thai": "Kra-Dai",
}


def load():
    raw = open("docs/data.js", encoding="utf-8").read()
    return json.loads(raw[len("const DATA = "):-2])


def build_tree(names, merges):
    """Turn UPGMA's merge list into a nested tree for the dendrogram.

    Each internal node records the average similarity at which its two children
    joined, so the renderer can place it at that exact x-position. Leaves are
    {"name": ...}; internal nodes are {"sim": float, "children": [a, b],
    "leaves": [...]}. Emitting the real merge similarity (rather than a tree
    depth) is what makes the drawing lossless: no projection step, so nothing to
    misread. Children are ordered to keep the drawn leaf order stable.
    """
    node_of = {n: {"name": n, "leaves": [n]} for n in names}
    root = None
    for a, b, s in merges:
        # Child order must stay exactly as upgma_order merged them (a then b).
        # Reordering for visual tidiness desynchronises the tree's leaf order
        # from `heatmapOrder`, which is derived from the same merge sequence — and
        # then the two visuals silently disagree about which languages are
        # adjacent. Any future tree renderer should assert the orders agree.
        na, nb = node_of[a[0]], node_of[b[0]]
        node = {"sim": round(s, 4),
                "children": [na, nb],
                "leaves": na["leaves"] + nb["leaves"]}
        for leaf in node["leaves"]:
            node_of[leaf] = node
        root = node
    return root


def upgma_order(names, sim):
    """UPGMA clustering on similarity (higher=closer). Returns leaf order
    (for heatmap) and the merge list [(membersA, membersB, similarity)]."""
    clusters = [[n] for n in names]

    def avg_sim(ca, cb):
        vals = [sim[frozenset((a, b))] for a in ca for b in cb]
        return sum(vals) / len(vals)

    merges = []
    while len(clusters) > 1:
        best, bi, bj = -1, 0, 1
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                s = avg_sim(clusters[i], clusters[j])
                if s > best:
                    best, bi, bj = s, i, j
        a, b = clusters[bi], clusters[bj]
        merges.append((list(a), list(b), best))
        clusters = [c for k, c in enumerate(clusters) if k not in (bi, bj)] + [a + b]
    return clusters[0], merges


def main():
    D = load()
    names = sorted(l["name"] for l in D["languages"])
    sim = {}
    for key, (shared, jac) in D["pairOverlap"].items():
        a, b = key.split("|")
        sim[frozenset((a, b))] = jac

    # --- family vs cross-family stats ---
    same, cross = [], []
    for a, b in combinations(names, 2):
        j = sim[frozenset((a, b))]
        (same if FAMILIES[a] == FAMILIES[b] else cross).append(j)
    same_med, cross_med = statistics.median(same), statistics.median(cross)
    print(f"same-family pairs:  n={len(same)}  median jaccard={same_med:.3f} mean={statistics.mean(same):.3f}")
    print(f"cross-family pairs: n={len(cross)} median jaccard={cross_med:.3f} mean={statistics.mean(cross):.3f}")

    # % of cross-family pairs MORE similar than the median same-family pair
    beat = sum(1 for j in cross if j > same_med) / len(cross)
    print(f"cross-family pairs beating same-family median: {100*beat:.0f}%")

    # for each language: is its nearest neighbor in its own family?
    nn_same = []
    for n in names:
        others = [(sim[frozenset((n, o))], o) for o in names if o != n]
        top = max(others)
        nn_same.append((n, top[1], FAMILIES[n] == FAMILIES[top[1]]))
    n_same_family_nn = sum(1 for _, _, s in nn_same if s)
    print(f"languages whose closest sound-relative is in their OWN family: "
          f"{n_same_family_nn}/{len(names)}")
    for n, buddy, s in nn_same:
        if not s:
            print(f"   {n:<18} closest: {buddy} ({FAMILIES[buddy]})")

    # --- UPGMA leaf order for heatmap ---
    order, merges = upgma_order(names, sim)

    # sound-clusters at a fixed similarity cut (union-find over merges >= CUT)
    CUT = 0.60
    parent = {n: n for n in names}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, s in merges:
        if s >= CUT:
            ra, rb = find(a[0]), find(b[0])
            if ra != rb:
                parent[rb] = ra
    groups = {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    clusters = sorted((sorted(g) for g in groups.values() if len(g) >= 2),
                      key=len, reverse=True)

    # --- 2D sound map (MDS embedding, best of several restarts) ---
    def stress(c):
        import math
        return sum((math.dist(c[a], c[b]) - (1 - sim[frozenset((a, b))])) ** 2
                   for a, b in combinations(names, 2))
    coords = min((mds_2d(names, sim, iters=6000, seed=s) for s in range(8)),
                 key=stress)
    # sanity: embedded distance should correlate with target distance
    import math
    def corr():
        ds, ts = [], []
        for a, b in combinations(names, 2):
            pa, pb = coords[a], coords[b]
            ds.append(math.dist(pa, pb))
            ts.append(1 - sim[frozenset((a, b))])
        mx, my = sum(ds)/len(ds), sum(ts)/len(ts)
        cov = sum((x-mx)*(y-my) for x, y in zip(ds, ts))
        vx = sum((x-mx)**2 for x in ds) ** 0.5
        vy = sum((y-my)**2 for y in ts) ** 0.5
        return cov / (vx * vy)
    print(f"MDS embedding correlation with true distances: r={corr():.2f}")

    # cluster membership per language for bubble drawing
    cluster_of = {}
    for ci, c in enumerate(clusters):
        for n in c:
            cluster_of[n] = ci

    # --- UPGMA tree, exported for the dendrogram ---
    # The MDS scatter that used to render this section only preserved r=0.67 of
    # the true pairwise distances, and MDS axes carry no interpretable meaning,
    # so readers reported it as looking random. The tree below is the same
    # clustering the heatmap order and the cluster cut already come from, but
    # drawn losslessly: every node sits at the exact similarity where its two
    # children merged, so the x-position IS the number, not a projection of it.
    # It is also the same shape as a family tree, which is the section's point.
    tree = build_tree(names, merges)
    out_tree = {"root": tree, "cut": CUT}

    out = {
        "families": FAMILIES,
        "soundMap": coords,
        "clusterOf": cluster_of,
        "tree": out_tree,
        "heatmapOrder": order,
        "sameFamilyMedian": round(same_med, 3),
        "crossFamilyMedian": round(cross_med, 3),
        "crossBeatingSameMedianPct": round(100 * beat),
        "nnSameFamilyCount": n_same_family_nn,
        "nLanguages": len(names),
        "soundClusters": clusters,
    }
    with open("docs/analysis.js", "w", encoding="utf-8") as f:
        f.write("const ANALYSIS = ")
        json.dump(out, f, ensure_ascii=False)
        f.write(";\n")
    print(f"\nheatmap order: {' '.join(order[:8])} ...")
    print(f"sound clusters at cut {CUT}: {clusters}")
    print("wrote docs/analysis.js")


def mds_2d(names, sim, iters=3000, lr=0.05, seed=7):
    """Simple stress-minimizing 2D embedding (no numpy dependency).
    target distance = 1 - jaccard. Returns {name: (x, y)} normalized 0..1."""
    import random
    rnd = random.Random(seed)
    pos = {n: [rnd.uniform(0, 1), rnd.uniform(0, 1)] for n in names}
    pairs = [(a, b, 1 - sim[frozenset((a, b))])
             for i, a in enumerate(names) for b in names[i + 1:]]
    for it in range(iters):
        step = lr * (1 - it / iters)
        for a, b, target in pairs:
            pa, pb = pos[a], pos[b]
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            d = (dx * dx + dy * dy) ** 0.5 or 1e-9
            f = step * (d - target) / d
            pa[0] += f * dx; pa[1] += f * dy
            pb[0] -= f * dx; pb[1] -= f * dy
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    lo_x, hi_x = min(xs), max(xs); lo_y, hi_y = min(ys), max(ys)
    return {n: [round((p[0] - lo_x) / (hi_x - lo_x), 4),
                round((p[1] - lo_y) / (hi_y - lo_y), 4)] for n, p in pos.items()}


if __name__ == "__main__":
    main()
