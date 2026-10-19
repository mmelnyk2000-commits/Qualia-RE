import json, math, sys
src, out = sys.argv[1], sys.argv[2]
NAMES = {
 "14201":("Allentown / Lower West Side","city"),"14202":("Downtown","city"),"14203":("Downtown / Medical Campus","city"),
 "14204":("Broadway-Fillmore / Larkinville","city"),"14206":("Kaisertown / Lovejoy (part Cheektowaga)","city"),
 "14207":("Black Rock / Riverside","city"),"14208":("Hamlin Park / Masten","city"),"14209":("Elmwood / Delaware Park","city"),
 "14210":("South Buffalo / Seneca-Babcock","city"),"14211":("East Side / MLK Park","city"),"14212":("Lovejoy / Sloan line","city"),
 "14213":("West Side / Grant-Ferry","city"),"14214":("University Heights / Parkside","city"),
 "14215":("Kensington-Bailey (part Cheektowaga)","city"),"14216":("North Buffalo / Hertel","city"),
 "14220":("South Buffalo","city"),"14222":("Elmwood Village","city"),
 "14217":("Kenmore / Tonawanda","sub"),"14223":("Town of Tonawanda","sub"),"14150":("Tonawanda","sub"),
 "14120":("North Tonawanda (Niagara Co.)","sub"),"14218":("Lackawanna","sub"),"14219":("Blasdell / Hamburg","sub"),
 "14224":("West Seneca","sub"),"14225":("Cheektowaga","sub"),"14227":("Cheektowaga / Sloan","sub"),"14043":("Depew / Lancaster","sub"),
 "14226":("Amherst (Eggertsville / Snyder)","sub"),"14221":("Williamsville / Amherst","sub"),"14228":("Amherst","sub"),
 "14068":("Getzville / Amherst","sub"),"14051":("East Amherst","sub"),"14127":("Orchard Park","sub"),"14075":("Hamburg","sub"),
 "14086":("Lancaster","sub"),"14072":("Grand Island","sub"),
}
d = json.load(open(src))
feats = [f for f in d["features"] if f["properties"]["ZCTA5CE10"] in NAMES]
lat0 = 42.9; kx = math.cos(math.radians(lat0))
def proj(lon, lat): return lon * kx, -lat
def polys(g):
    if g["type"] == "Polygon": return [g["coordinates"]]
    return g["coordinates"]
pts = [proj(*p) for f in feats for poly in polys(f["geometry"]) for ring in poly for p in ring]
minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts); miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
W = 1000; s = W / (maxx - minx); H = round((maxy - miny) * s)
def xy(p): x, y = proj(*p); return ((x - minx) * s, (y - miny) * s)
def dp(points, eps):
    if len(points) < 3: return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1e-9
    i, dmax = 0, 0
    for k in range(1, len(points) - 1):
        px, py = points[k]
        dd = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / L
        if dd > dmax: i, dmax = k, dd
    if dmax > eps: return dp(points[: i + 1], eps)[:-1] + dp(points[i:], eps)
    return [points[0], points[-1]]
res = {}
for f in feats:
    z = f["properties"]["ZCTA5CE10"]; parts = []
    for poly in polys(f["geometry"]):
        for ring in poly:
            pr = [xy(p) for p in ring]
            far = max(range(len(pr)), key=lambda k: (pr[k][0]-pr[0][0])**2 + (pr[k][1]-pr[0][1])**2)
            r = dp(pr[: far + 1], 0.9)[:-1] + dp(pr[far:], 0.9)
            if len(r) < 4: continue
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in r) + "Z")
    cx, cy = xy((float(f["properties"]["INTPTLON10"]), float(f["properties"]["INTPTLAT10"])))
    res[z] = {"d": "".join(parts), "c": [round(cx, 1), round(cy, 1)], "n": NAMES[z][0], "k": NAMES[z][1]}
json.dump({"w": W, "h": H, "zips": res}, open(out, "w"), separators=(",", ":"))
print(W, H, len(res), sum(len(v["d"]) for v in res.values()))
