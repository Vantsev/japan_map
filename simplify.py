#!/usr/bin/env python3
"""Simplify raw Japan prefectures GeoJSON -> compact japan.min.json.
Ring-aware Douglas-Peucker (closed rings split at farthest vertex so they
don't collapse to 2 points). Usage: python3 simplify.py [eps]
Download raw first:
  curl -sL -o japan.geojson https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson
"""
import json, re, os, sys

EPS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0015
COORD_DP = 4  # coordinate decimal places

def rdp(pts, eps):
    if len(pts) < 3: return pts
    keep = [False]*len(pts); keep[0] = keep[-1] = True; st = [(0, len(pts)-1)]
    while st:
        s, e = st.pop(); dmax = 0; idx = -1
        ax, ay = pts[s]; bx, by = pts[e]; dx, dy = bx-ax, by-ay
        dd = (dx*dx+dy*dy)**.5 or 1e-9
        for i in range(s+1, e):
            px, py = pts[i]
            dist = abs(dx*(ay-py) - dy*(ax-px))/dd
            if dist > dmax: dmax = dist; idx = i
        if dmax > eps and idx != -1:
            keep[idx] = True; st += [(s, idx), (idx, e)]
    return [p for p, k in zip(pts, keep) if k]

def rdp_ring(pts, eps):
    # closed ring: split at vertex farthest from pts[0], rdp each arc
    if len(pts) < 5: return pts
    a = pts[0]; fd = -1; k = 0
    for i in range(1, len(pts)-1):
        dx = pts[i][0]-a[0]; dy = pts[i][1]-a[1]; dd = dx*dx+dy*dy
        if dd > fd: fd = dd; k = i
    return rdp(pts[:k+1], eps)[:-1] + rdp(pts[k:], eps)

def ring(r):
    r = [[round(x, COORD_DP), round(y, COORD_DP)] for x, y in r]
    r = rdp_ring(r, EPS)
    return r if len(r) >= 4 else None

def main():
    d = json.load(open('japan.geojson'))
    out = []
    for f in d['features']:
        g = f['geometry']
        polyset = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        polys = []; areas = []
        for poly in polyset:
            rr = ring(poly[0])
            if not rr: continue
            xs = [p[0] for p in rr]; ys = [p[1] for p in rr]
            a = (max(xs)-min(xs))*(max(ys)-min(ys))
            polys.append(rr); areas.append(a)
        if not polys: continue
        big = max(areas)
        kept = [p for p, a in zip(polys, areas) if a >= big*0.02 or a > 0.02]
        out.append({
            "id": f['properties']['id'],
            "en": f['properties']['nam'],
            "ja": f['properties']['nam_ja'],
            "poly": kept,
        })
    out.sort(key=lambda x: x['id'])
    json.dump(out, open('japan.min.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    kb = os.path.getsize('japan.min.json')/1024
    pts = sum(len(r) for x in out for r in x['poly'])
    print(f"eps={EPS} dp={COORD_DP} -> {len(out)} feats, {pts} pts, {kb:.0f} KB")

if __name__ == '__main__':
    main()
