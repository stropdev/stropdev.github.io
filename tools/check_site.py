"""Check the built site: python3 tools/check_site.py .

Parses every HTML page with the standard-library parser (balanced tags,
unique ids, no raw `<`), resolves every internal link and `#anchor`, and
prints the contrast ratio of each palette's text tokens against its planes.
Exit status is nonzero when a page or link is broken.
"""
import html.parser, pathlib, re, sys, urllib.parse
ROOT = pathlib.Path(sys.argv[1]).resolve()
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}

class Check(html.parser.HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=False); self.name=name; self.stack=[]; self.ids=set(); self.links=[]; self.errors=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if "id" in a:
            if a["id"] in self.ids: self.errors.append(f"duplicate id {a['id']}")
            self.ids.add(a["id"])
        for k in ("href","src"):
            if k in a and a[k]: self.links.append(a[k])
        if tag not in VOID: self.stack.append(tag)
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs); 
    def handle_endtag(self, tag):
        if tag in VOID: return
        if not self.stack or self.stack[-1]!=tag:
            self.errors.append(f"mismatched </{tag}> (open: {self.stack[-3:]}) at line {self.getpos()[0]}")
            if tag in self.stack:
                while self.stack and self.stack[-1]!=tag: self.stack.pop()
        if self.stack: self.stack.pop()
    def handle_entityref(self, name):
        if name not in ("amp","lt","gt","quot","apos","nbsp"): self.errors.append(f"entity &{name};")
    def handle_data(self, data):
        if "<" in data and self.stack and self.stack[-1] not in ("script","style"): self.errors.append(f"raw < in text near line {self.getpos()[0]}: {data.strip()[:40]!r}")

pages = {p.resolve(): Check(str(p)) for p in ROOT.rglob("*.html") if ".git" not in p.parts}
for p,c in pages.items():
    c.feed(p.read_text(encoding="utf-8")); c.close()
    if c.stack: c.errors.append(f"unclosed {c.stack}")
bad=0
for p,c in pages.items():
    for e in c.errors: bad+=1; print(f"{p.relative_to(ROOT)}: {e}")
    for link in c.links:
        if link.startswith(("http:","https:","mailto:")): continue
        url=urllib.parse.urlsplit(link); path=url.path; frag=url.fragment
        if path=="" : target=p
        else:
            target=(ROOT/path.lstrip("/")) if path.startswith("/") else (p.parent/path)
            target=target.resolve()
            if target.is_dir(): target=target/"index.html"
        if not target.exists(): bad+=1; print(f"{p.relative_to(ROOT)}: broken link {link}"); continue
        if frag and target.suffix==".html":
            ids = pages[target].ids if target in pages else set()
            if frag not in ids: bad+=1; print(f"{p.relative_to(ROOT)}: missing anchor {link}")
print(f"{len(pages)} pages, {bad} problems")
exit_code = 1 if bad else 0

# contrast
def lum(h):
    r,g,b=(int(h[i:i+2],16)/255 for i in (1,3,5))
    f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def ratio(a,b):
    la,lb=lum(a),lum(b); return round((max(la,lb)+0.05)/(min(la,lb)+0.05),2)
css=(ROOT/"assets/site.css").read_text()
for m in re.finditer(r"(:root[^{]*|\[data-palette=\"([a-z-]+)\"\])\s*\{([^}]*)\}", css):
    body=m.group(3)
    if "--bg-base" not in body: continue
    t=dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-f]{6})", body))
    name=m.group(2) or m.group(1).strip()[:40]
    rows=[("text/base",ratio(t["fg-text"],t["bg-base"])),("secondary/base",ratio(t["fg-secondary"],t["bg-base"])),("secondary/surface",ratio(t["fg-secondary"],t["bg-surface"])),("muted/base",ratio(t["fg-muted"],t["bg-base"])),("muted/surface",ratio(t["fg-muted"],t["bg-surface"])),("accent/base",ratio(t["accent"],t["bg-base"])),("accent/raised",ratio(t["accent"],t["bg-raised"])),("on-accent/accent",ratio(t["on-accent"],t["accent"])),("text/selection",ratio(t["fg-text"],t["bg-selection"]))]
    print(f"{name:28}", "  ".join(f"{k}={v}" for k,v in rows))
sys.exit(exit_code)
