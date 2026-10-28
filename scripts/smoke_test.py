"""Real HTTP CRUD check; creates and cleans its own synthetic fixture."""
import argparse
import csv
import io
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rules import today_jakarta
parser=argparse.ArgumentParser()
parser.add_argument('--base-url',default='http://127.0.0.1:8000')
parser.add_argument('--json')
args=parser.parse_args()
base=args.base_url.rstrip('/')
client=build_opener(HTTPCookieProcessor(CookieJar()))
results=[]
tool_id=loan_id=None
token=''
code='UJI-'+uuid.uuid4().hex[:10].upper()


def fetch(path,data=None):
    request=Request(base+path,data=urlencode(data).encode() if data is not None else None)
    try:
        with client.open(request,timeout=15) as response:
            return response.status,response.read().decode('utf-8-sig'),response.geturl()
    except HTTPError as error:
        return error.code,error.read().decode('utf-8-sig'),error.geturl()


def post(path,data=None):
    return fetch(path,{'csrf_token':token,**(data or {})})


def check(name,condition):
    results.append({'case':name,'passed':bool(condition)})
    print(('PASS' if condition else 'FAIL')+' · '+name)
    if not condition:
        raise AssertionError(name)


try:
    status,body,_=fetch('/health')
    check('HTTP health and real database',status==200 and json.loads(body)['status']=='ok')
    _,body,_=fetch('/alat/baru')
    token=re.search(r'name="csrf_token" value="([^"]+)"',body)[1]
    fixture=dict(code=code,name='Alat DEMO HTTP',category='Pengujian',location='Rak Uji',condition='Baik',notes='Fixture otomatis')
    status,body,_=post('/alat/baru',fixture)
    check('Create equipment over HTTP',status==200 and code in body)
    _,body,_=fetch('/alat?'+urlencode({'q':code}))
    tool_id=int(re.search(r'/alat/(\d+)/ubah',body)[1])
    fixture['name']='Alat DEMO Diperbarui'
    status,body,_=post(f'/alat/{tool_id}/ubah',fixture)
    check('Update and read equipment',status==200 and fixture['name'] in body)
    status,_,_=post('/alat/baru',fixture)
    check('Duplicate code rejected',status==400)
    today=today_jakarta()
    loan=dict(equipment_id=tool_id,borrower='Peminjam DEMO HTTP',nim='DEMO-HTTP',
              purpose='Pengujian aplikasi nyata',borrowed_on=today.isoformat(),
              due_on=(today+timedelta(days=3)).isoformat(),checkout_notes='Kelengkapan diperiksa')
    status,body,url=post('/peminjaman/baru',loan)
    loan_id=int(re.search(r'/peminjaman/(\d+)/bukti',url)[1])
    check('Create loan and print receipt',status==200 and 'Bukti peminjaman alat' in body)
    status,_,_=post('/peminjaman/baru',loan)
    check('Second active loan rejected',status==400)
    loan['purpose']='Pengujian CRUD diperbarui'
    status,body,_=post(f'/peminjaman/{loan_id}/ubah',loan)
    check('Update loan persisted',status==200 and loan['purpose'] in body)
    status,body,_=post(f'/alat/{tool_id}/hapus')
    check('Foreign key preserves equipment history',status==200 and 'memiliki riwayat' in body)
    status,body,_=post(f'/peminjaman/{loan_id}/kembalikan',{'return_condition':'Baik','return_notes':'Lengkap'})
    check('Return loan updates receipt',status==200 and 'Dikembalikan' in body and 'Lengkap' in body)
    status,body,_=fetch('/peminjaman/export.csv?'+urlencode({'q':code}))
    rows=list(csv.DictReader(io.StringIO(body)))
    check('Filtered CSV has real persisted transaction',status==200 and len(rows)==1 and rows[0]['status']=='Dikembalikan')
    status,_,_=fetch('/alat/baru',fixture)
    check('Missing CSRF token rejected',status==400)
    status,body,_=post(f'/peminjaman/{loan_id}/hapus')
    check('Delete loan over HTTP',status==200)
    loan_id=None
    status,body,_=post(f'/alat/{tool_id}/hapus')
    _,filtered,_=fetch('/alat?'+urlencode({'q':code}))
    check('Delete equipment and verify absence',status==200 and 'Tidak ada alat' in filtered)
    tool_id=None
except Exception as error:
    print(f'ERROR: {type(error).__name__}: {error}')
    if not results or results[-1]['passed']:
        results.append({'case':'Unexpected error','passed':False,'error':str(error)})
finally:
    if loan_id is not None:
        post(f'/peminjaman/{loan_id}/hapus')
    if tool_id is not None:
        post(f'/alat/{tool_id}/hapus')
    report=dict(tested_at=datetime.now(timezone.utc).isoformat(),scope='Real HTTP application check',
                base_url=base,tests=len(results),passed=sum(r['passed'] for r in results),cases=results,
                successful=bool(results) and all(r['passed'] for r in results))
    if args.json:
        destination=Path(args.json)
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"HTTP checks: {report['passed']}/{report['tests']}")
sys.exit(0 if report['successful'] else 1)
