"""Real API regressions for cross-owner reads, mutations and exported evidence."""
import uuid
import pytest
from httpx import ASGITransport,AsyncClient
from api.app.main import app
from api.app.database import Base,engine,async_session
from api.app.auth import create_token
from api.app.models import User,Source,Comparable,ExtractedField,ExtractionJob

@pytest.fixture
async def evidence():
 async with engine.begin() as c:await c.run_sync(Base.metadata.create_all)
 async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
  case=(await client.post('/api/v1/cases',json={'title':'Owner-only case'})).json()['id']
  source=(await client.post(f'/api/v1/cases/{case}/sources/url',json={'url':'https://example.com/private'})).json()['id']
  ids=[uuid.uuid4() for _ in range(5)];comp,field,job,other,viewer=ids
  async with async_session() as db:
   db.add_all([User(id=other,email='other@access.test',name='Other',role='analyst'),User(id=viewer,email='viewer@access.test',name='Viewer',role='viewer')]);await db.flush()
   db.add(Comparable(id=comp,case_id=uuid.UUID(case),source_id=uuid.UUID(source),property_title='Private evidence'));await db.flush()
   db.add(ExtractionJob(id=job,source_id=uuid.UUID(source),status='pending'));await db.flush()
   db.add(ExtractedField(id=field,extraction_job_id=job,comparable_id=comp,field_name='asking_price',raw_value='10',normalized_value='10',confidence=1));await db.commit()
  # A valid signed token whose role claim says admin must still use the DB role.
  headers=lambda id,email:{'Authorization':'Bearer '+create_token(str(id),email,'admin')}
  yield client,case,source,comp,field,job,headers(other,'other@access.test'),headers(viewer,'viewer@access.test')
 async with engine.begin() as c:await c.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_cross_owner_reads_and_exports_denied(evidence):
 c,case,source,comp,field,job,other,_=evidence
 assert (await c.get('/api/v1/cases',headers=other)).json()['total']==0
 for path in [f'/cases/{case}',f'/cases/{case}/sources',f'/sources/{source}/raw',f'/cases/{case}/comparables',f'/extraction-jobs/{job}',*[f'/cases/{case}/export/{fmt}' for fmt in ['csv','xlsx','pdf']]]:
  r=await c.get('/api/v1'+path,headers=other);assert r.status_code==404,(path,r.text)
 # Owner can still access records and exports.
 assert (await c.get(f'/api/v1/cases/{case}/comparables')).status_code==200
 for fmt in ['csv','xlsx','pdf']:
  assert (await c.get(f'/api/v1/cases/{case}/export/{fmt}')).status_code==200

@pytest.mark.asyncio
async def test_cross_owner_mutations_denied_before_side_effects(evidence):
 c,case,source,comp,field,job,other,_=evidence
 assert (await c.post(f'/api/v1/cases/{case}/sources/url',headers=other,json={'url':'https://example.com/new'})).status_code==404
 assert (await c.post(f'/api/v1/cases/{case}/sources/pdf',headers=other,files={'file':('test.pdf',b'%PDF-test','application/pdf')})).status_code==404
 assert (await c.post(f'/api/v1/sources/{source}/extract',headers=other)).status_code==404
 assert (await c.patch(f'/api/v1/comparables/{comp}/status',headers=other,json={'status':'invalid','reason':'test'})).status_code==404
 assert (await c.patch(f'/api/v1/comparables/{comp}/fields/{field}',headers=other,json={'new_value':'999','reason':'test'})).status_code==404
 assert len((await c.get(f'/api/v1/cases/{case}/sources')).json())==1
 assert (await c.get(f'/api/v1/extraction-jobs/{job}')).json()['status']=='pending'

@pytest.mark.asyncio
async def test_viewer_cannot_create_case(evidence):
 c,*_,viewer=evidence
 assert (await c.post('/api/v1/cases',headers=viewer,json={'title':'Forbidden'})).status_code==403

@pytest.mark.asyncio
async def test_upload_filename_cannot_escape_storage(evidence):
 c,case,*_=evidence
 for filename in ['../escape.pdf','..\\escape.pdf','/tmp/escape.pdf']:
  r=await c.post(f'/api/v1/cases/{case}/sources/pdf',files={'file':(filename,b'%PDF','application/pdf')})
  assert r.status_code==400,r.text
