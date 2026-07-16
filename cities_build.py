#!/usr/bin/env python3
"""Build per-prefecture municipality maps for the city-level page.
Fetches municipality GeoJSON from niiyz/JapanCityGeoJson (raw CDN), merges per
prefecture, simplifies (ring-aware Douglas-Peucker), writes public/geo/<id>.json.

Usage:
  python3 cities_build.py 13 27 26 01      # specific prefectures (2-digit codes)
  python3 cities_build.py all              # all 47
Also writes/updates public/geo/index.json (per-pref city counts).
"""
import json, os, sys, urllib.request, concurrent.futures

EPS = 0.0004            # municipalities are small -> finer than the country map
COORD_DP = 4
API = "https://api.github.com/repos/niiyz/JapanCityGeoJson/contents/geojson/{:02d}"
UA = {"User-Agent": "keikenchi-build"}

# JIS prefecture code (1..47) -> our prefecture id is the same number
PREF_JA = {1:"北海道",2:"青森県",3:"岩手県",4:"宮城県",5:"秋田県",6:"山形県",7:"福島県",8:"茨城県",9:"栃木県",10:"群馬県",11:"埼玉県",12:"千葉県",13:"東京都",14:"神奈川県",15:"新潟県",16:"富山県",17:"石川県",18:"福井県",19:"山梨県",20:"長野県",21:"岐阜県",22:"静岡県",23:"愛知県",24:"三重県",25:"滋賀県",26:"京都府",27:"大阪府",28:"兵庫県",29:"奈良県",30:"和歌山県",31:"鳥取県",32:"島根県",33:"岡山県",34:"広島県",35:"山口県",36:"徳島県",37:"香川県",38:"愛媛県",39:"高知県",40:"福岡県",41:"佐賀県",42:"長崎県",43:"熊本県",44:"大分県",45:"宮崎県",46:"鹿児島県",47:"沖縄県"}

def rdp(pts, eps):
    if len(pts) < 3: return pts
    keep=[False]*len(pts); keep[0]=keep[-1]=True; st=[(0,len(pts)-1)]
    while st:
        s,e=st.pop(); dmax=0; idx=-1; ax,ay=pts[s]; bx,by=pts[e]; dx,dy=bx-ax,by-ay
        dd=(dx*dx+dy*dy)**.5 or 1e-9
        for i in range(s+1,e):
            px,py=pts[i]; dist=abs(dx*(ay-py)-dy*(ax-px))/dd
            if dist>dmax: dmax=dist; idx=i
        if dmax>eps and idx!=-1: keep[idx]=True; st+=[(s,idx),(idx,e)]
    return [p for p,k in zip(pts,keep) if k]

def rdp_ring(pts, eps):
    if len(pts) < 5: return pts
    a=pts[0]; fd=-1; k=0
    for i in range(1,len(pts)-1):
        dx=pts[i][0]-a[0]; dy=pts[i][1]-a[1]; dd=dx*dx+dy*dy
        if dd>fd: fd=dd; k=i
    return rdp(pts[:k+1], eps)[:-1] + rdp(pts[k:], eps)

def ring(r):
    r=[[round(x,COORD_DP),round(y,COORD_DP)] for x,y in r]
    r=rdp_ring(r,EPS)
    return r if len(r)>=4 else None

def fetch_json(url, tries=4):
    last=None
    for _ in range(tries):
        try:
            req=urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            last=e
    raise last

def list_pref_files(pref):
    items=fetch_json(API.format(pref))
    return [(it["name"], it["download_url"]) for it in items if it["name"].endswith(".json")]

def process_city(name_url):
    fname, url = name_url
    try:
        gj=fetch_json(url)
    except Exception as e:
        print("  ! fetch fail", fname, e); return None
    feats=gj.get("features", [])
    if not feats: return None
    p0=feats[0]["properties"]
    code=p0.get("N03_007") or fname.split(".")[0]
    city=p0.get("N03_003") or ""
    ward=p0.get("N03_004") or ""
    name=(city+ward) if city and ward and city!=ward else (ward or city)
    polys=[]; areas=[]
    for f in feats:
        g=f["geometry"]; polyset=g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
        for poly in polyset:
            rr=ring(poly[0])
            if not rr: continue
            xs=[q[0] for q in rr]; ys=[q[1] for q in rr]
            areas.append((max(xs)-min(xs))*(max(ys)-min(ys))); polys.append(rr)
    if not polys: return None
    big=max(areas)
    kept=[p for p,a in zip(polys,areas) if a>=big*0.02 or a>0.01]
    return {"code":str(code), "name":name, "poly":kept}

def build_pref(pref):
    files=list_pref_files(pref)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        cities=[c for c in ex.map(process_city, files) if c]
    cities.sort(key=lambda c: c["code"])
    out={"id":pref, "ja":PREF_JA[pref], "cities":cities}
    os.makedirs("public/geo", exist_ok=True)
    path=f"public/geo/{pref}.json"
    json.dump(out, open(path,"w"), separators=(",",":"), ensure_ascii=False)
    kb=os.path.getsize(path)/1024
    print(f"pref {pref:02d} {PREF_JA[pref]}: {len(cities)} cities, {kb:.0f} KB")
    return len(cities)

def update_index():
    idx={}
    for f in sorted(os.listdir("public/geo")):
        if f.endswith(".json") and f!="index.json":
            d=json.load(open("public/geo/"+f))
            idx[str(d["id"])]={"ja":d["ja"],"n":len(d["cities"])}
    json.dump(idx, open("public/geo/index.json","w"), separators=(",",":"), ensure_ascii=False)
    print("index.json ->", len(idx), "prefectures")

def main():
    args=sys.argv[1:]
    prefs=list(range(1,48)) if (not args or args[0]=="all") else [int(a) for a in args]
    for p in prefs:
        try: build_pref(p)
        except Exception as e: print("pref",p,"FAILED",e)
    update_index()

if __name__=="__main__":
    main()
