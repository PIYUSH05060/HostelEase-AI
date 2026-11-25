import sqlite3, os
from pathlib import Path
SCHEMA={'students':['name','room','course'],'rooms':['number','capacity'],'fees':['student','amount','status'],'mess':['day','meal','menu','feedback'],'complaints':['subject','priority','status'],'leave':['student','date','status'],'notices':['title','message']}
SEED={'students':[('Demo Student A','101','AI & DS'),('Demo Student B','102','CSE')],'rooms':[('101','2'),('102','3'),('103','2')],'fees':[('Demo Student A','12000','Paid'),('Demo Student B','12000','Pending')],'mess':[('Monday','Breakfast','Poha and fruit','Good'),('Tuesday','Dinner','Dal and rice','Good')],'complaints':[('Fan maintenance','Medium','Open')],'leave':[('Demo Student A','2026-12-01','Pending')],'notices':[('Welcome','Sample hostel notice board')]}
def connect():
 c=sqlite3.connect(os.getenv('HOSTEL_DB',str(Path(__file__).with_name('hostel.db')))); c.row_factory=sqlite3.Row; return c
def init():
 with connect() as c:
  for t,fields in SCHEMA.items():
   c.execute(f'CREATE TABLE IF NOT EXISTS {t}(id INTEGER PRIMARY KEY, '+','.join(f'{f} TEXT NOT NULL' for f in fields)+')')
  c.execute('CREATE TABLE IF NOT EXISTS metadata (seeded INTEGER)')
  if not c.execute('SELECT 1 FROM metadata').fetchone():
   for t,rows in SEED.items():
    c.executemany(f'INSERT INTO {t} ({",".join(SCHEMA[t])}) VALUES ({",".join("?" for _ in SCHEMA[t])})',rows)
   c.execute('INSERT INTO metadata VALUES (1)')
def data():
 with connect() as c: return {t:[dict(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY id')] for t in SCHEMA}
