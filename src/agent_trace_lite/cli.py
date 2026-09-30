import argparse,html,json,pathlib

def main(argv=None):
 p=argparse.ArgumentParser(prog='agent-trace'); p.add_argument('command',choices=['view']); p.add_argument('events'); p.add_argument('--html',default='trace.html'); a=p.parse_args(argv); rows=[]
 for line in open(a.events):
  if line.strip():
   x=json.loads(line); rows.append({k:('[REDACTED]' if any(s in k.lower() for s in ('token','secret','password')) else v) for k,v in x.items()})
 body='\n'.join(f"<tr><td>{html.escape(str(x.get('type','event')))}</td><td>{html.escape(str(x.get('name',x.get('message',''))))}</td></tr>" for x in rows); pathlib.Path(a.html).write_text('<html><body><h1>Agent trace</h1><table>'+body+'</table></body></html>'); print(json.dumps({'schema':'agent-trace/v1','events':len(rows),'html':a.html},indent=2)); return 0
