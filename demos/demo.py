import json,tempfile,pathlib
from agent_trace_lite.cli import main
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'events.jsonl'; p.write_text(json.dumps({'type':'tool','name':'read_file','token':'hidden'})+'\n'+json.dumps({'type':'result','message':'done'})+'\n')
 print('Agent Trace Lite demo: two events, zero secrets')
 main(['view',str(p),'--html',str(pathlib.Path(d)/'trace.html')])
