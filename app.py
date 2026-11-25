import os, secrets, io, re, math
from datetime import date
from flask import Flask,render_template,request,redirect,url_for,abort,jsonify,session,send_file
from dotenv import load_dotenv
from database import SCHEMA,connect,init,data
from ai_provider import generate
from prompts import SYSTEM,context
load_dotenv()
app=Flask(__name__); app.secret_key=os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=16384,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict')
DEMO=os.getenv('AI_PROVIDER','ollama').lower()=='demo' or os.getenv('RENDER')=='true'
init()
def stats(d):
 occupied={s['room'] for s in d['students']}; capacity=sum(int(r['capacity']) for r in d['rooms']); return {'Students':len(d['students']),'Rooms':len(d['rooms']),'Occupied rooms':len(occupied),'Vacant rooms':sum(r['number'] not in occupied for r in d['rooms']),'Available beds':capacity-len(d['students']),'Open complaints':sum(r['status']!='Resolved' for r in d['complaints']),'Paid fees':sum(float(r['amount']) for r in d['fees'] if r['status']=='Paid'),'Pending fees':sum(float(r['amount']) for r in d['fees'] if r['status']=='Pending')}
@app.get('/')
def index():
 session.setdefault('csrf',secrets.token_hex(24)); d=data(); return render_template('index.html',d=d,schemas=SCHEMA,stats=stats(d),demo=DEMO,csrf=session['csrf'])
@app.post('/change/<table>')
def change(table):
 if DEMO: abort(403)
 if table not in SCHEMA or not secrets.compare_digest(request.form.get('csrf',''),session.get('csrf','!')): abort(400)
 action=request.form.get('action'); fields=SCHEMA[table]
 with connect() as c:
  c.execute('BEGIN IMMEDIATE')
  rid=request.form.get('id','0')
  if not rid.isdigit(): abort(400)
  if action=='delete':
   if table=='rooms' and c.execute('SELECT 1 FROM students WHERE room=(SELECT number FROM rooms WHERE id=?)',(rid,)).fetchone(): abort(400,'Room is occupied')
   c.execute(f'DELETE FROM {table} WHERE id=?',(rid,))
  elif action in ('add','edit'):
   v=[request.form.get(f,'').strip() for f in fields]; x=dict(zip(fields,v))
   if any(not a or len(a)>200 for a in v): abort(400,'Invalid fields')
   if table=='rooms':
    if not x['capacity'].isdigit() or not 1<=int(x['capacity'])<=20: abort(400,'Capacity must be 1–20')
    if c.execute('SELECT 1 FROM rooms WHERE number=? AND id!=?',(x['number'],rid)).fetchone(): abort(400,'Duplicate room')
    old=c.execute('SELECT number FROM rooms WHERE id=?',(rid,)).fetchone()
    if old and old['number']!=x['number'] and c.execute('SELECT 1 FROM students WHERE room=?',(old['number'],)).fetchone(): abort(400,'Cannot rename occupied room')
    if c.execute('SELECT COUNT(*) FROM students WHERE room=?',(x['number'],)).fetchone()[0]>int(x['capacity']): abort(400,'Capacity below occupancy')
   if table=='students':
    room=c.execute('SELECT capacity FROM rooms WHERE number=?',(x['room'],)).fetchone()
    if not room or c.execute('SELECT COUNT(*) FROM students WHERE room=? AND id!=?',(x['room'],rid)).fetchone()[0]>=int(room['capacity']): abort(400,'Room unavailable')
   if table=='fees':
    try: amount=float(x['amount']); assert math.isfinite(amount) and 0<=amount<=10000000
    except (ValueError,AssertionError): abort(400,'Invalid amount')
   allowed={'fees':('Paid','Pending'),'complaints':('Open','In progress','Resolved'),'leave':('Pending','Approved','Rejected')}
   if table in allowed and x['status'] not in allowed[table]: abort(400,'Invalid status')
   if table=='complaints' and x['priority'] not in ('Low','Medium','High'): abort(400,'Invalid priority')
   if table=='leave':
    try: date.fromisoformat(x['date'])
    except ValueError: abort(400,'Use YYYY-MM-DD')
   if action=='add': c.execute(f'INSERT INTO {table} ({",".join(fields)}) VALUES ({",".join("?" for _ in fields)})',v)
   else: c.execute(f'UPDATE {table} SET '+','.join(f'{f}=?' for f in fields)+' WHERE id=?',v+[rid])
  else: abort(400)
 return redirect(url_for('index')+'#'+table)
def question():
 body=request.get_json(silent=True); q=body.get('question','') if isinstance(body,dict) else ''; q=q.strip()[:500] if isinstance(q,str) else ''
 if not q or not re.search(r'hostel|room|fee|mess|complaint|leave|notice|student|bed|occupancy|khana',q,re.I): abort(400,'Ask a hostel-related question')
 return q
def fallback(q,s):
 keys=[k for k in s if any(w in q.lower() for w in k.lower().split())]; return '; '.join(f'{k}: {s[k]}' for k in (keys or list(s)))+'. Check the relevant module for details. No actions are taken by the assistant.'
@app.post('/chat')
def chat():
 q=question(); s=stats(data())
 if not DEMO:
  try: return jsonify(answer=generate(SYSTEM,context(s,q)),mode='Local Ollama')
  except Exception: pass
 return jsonify(answer=fallback(q,s),mode='Rule-based demo / fallback')
@app.post('/playground')
def playground():
 q=question(); s=stats(data()); p=context(s,q)
 if not DEMO:
  try: return jsonify(basic=generate('Answer hostel questions briefly.',q),engineered=generate(SYSTEM,p),prompt=p,mode='Local Ollama')
  except Exception: pass
 return jsonify(basic='Check hostel records and contact the hostel office.',engineered=fallback(q,s),prompt=p,mode='Illustrative comparison — not AI-generated')
@app.get('/report')
def report():
 from reportlab.pdfgen import canvas
 b=io.BytesIO(); c=canvas.Canvas(b); c.setFont('Helvetica-Bold',20); c.drawString(50,790,'HostelEase AI | Summary'); c.setFont('Helvetica',12)
 for i,(k,v) in enumerate(stats(data()).items()): c.drawString(50,750-i*25,f'{k}: {v}')
 c.drawString(50,480,'Educational demo; not an official hostel record.'); c.save(); b.seek(0); return send_file(b,mimetype='application/pdf',as_attachment=True,download_name='hostel-summary.pdf')
if __name__=='__main__': app.run(host='127.0.0.1',port=5000)
