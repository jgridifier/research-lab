import sys,json,base64,re,os
# decode connector download_file outputs (JSON with base64) into data/raw
for p in sys.argv[1:]:
    t=open(p).read(); m=re.search(r'\{"name".*\}',t,re.S); d=json.loads(m.group(0))
    out=os.path.join('/workspace/relbench-own/data/raw',d['name']); open(out,'wb').write(base64.b64decode(d['base64'])); print(out,os.path.getsize(out))
