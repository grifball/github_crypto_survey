#psql -h dbclass.cs.pdx.edu f18wdb15 f18wdb15
import requests
import sys
import os
import psycopg2
import html
import datetime
import time

pgpass = os.environ['PGPASSWORD']
print(pgpass)
conn = psycopg2.connect("dbname=f18wdb15 user=f18wdb15 password="+pgpass+" host=dbclass.cs.pdx.edu")
cur=conn.cursor()
cur.execute('SELECT version()')
db_version = cur.fetchone()
print(db_version)
try:
  cur.execute("drop schema githubsec CASCADE;")
except psycopg2.Error as e:
  print("drop failed: "+e.pgerror)
  cur.execute("ROLLBACK")
cur.execute("create schema githubsec;")
cur.execute("COMMIT")
cur.execute("""
CREATE TABLE githubsec.Repo (
full_name varchar(200),
owner varchar(200),
forks INT,
fork_from varchar(200),
bugs INT,
stars INT,
created_at INT,
subscribers INT,
pulls INT,
organization_name varchar(200)
);
""")
cur.execute("COMMIT")

# goto https://github.com/settings/tokens to get a token for this (GITHUB_AUTH)
client_auth = os.environ['GITHUB_AUTH']
client_user = os.environ['GITHUB_USER']
auth=(client_user, client_auth)
rj=requests.get("https://api.github.com/rate_limit", auth=auth).json()
print(rj["resources"]["search"])
print("https://api.github.com/search/repositories?q=crypto+language:c&sort=stars&order=desc")
res=requests.get("https://api.github.com/search/repositories?q=crypto+language:c&sort=stars&order=desc", auth=auth)
print(res.status_code)
rj=res.json()
crypto_libraries=["openssl/openssl","jedisct1/libsodium","weidai11/cryptopp"]
for item in rj['items']:
  full_name=item['full_name']
  qstr="https://api.github.com/repos/"+item["full_name"]
  print(qstr)
  if full_name in crypto_libraries:
    res=requests.get(qstr, auth=auth)
    rj=res.json()
    full_name=str(rj['full_name'])
    forks=str(rj['forks'])
    owner=str(rj['owner']['login'])
    #organization=str(rj['organization']['login'])
    stars=str(rj['stargazers_count'])
    subscribers=str(rj['subscribers_count'])
    #created_dt=dateutil.parser.parse(rj['created_at'])
    created_dt=datetime.datetime.strptime(rj['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
    created_at=str(int(time.mktime(created_dt.timetuple())))
    cur.execute("insert into githubsec.Repo (full_name, owner, forks, stars, created_at, subscribers) values ('"+full_name+"','"+owner+"','"+forks+"','"+stars+"','"+created_at+"','"+subscribers+"');")
    #res=requests.get("https://api.github.com/search/repositories?q=crypto+language:c&sort=stars&order=desc", auth=auth)
cur.execute("COMMIT")
sys.exit(0)
print("https://api.github.com/search/repositories?language:c&sort=stars&order=desc")
res=requests.get("https://api.github.com/search/repositories?q=language:c&sort=stars&order=desc", auth=auth)
rj=res.json()
for item in rj['items']:
  print(item["full_name"])
  print("https://api.github.com/search/code?q=openssl+in:file+language:c+repo:"+item["full_name"])
  print("https://api.github.com/search/code?q=libsodium+in:file+language:c+repo:"+item["full_name"])
  res=requests.get("https://api.github.com/search/code?q=libsodium+in:file+language:c+repo:"+item["full_name"], auth=auth)
  rj=res.json()
  for item2 in rj['items']:
    print(item["full_name"])
    print(item2["html_url"])
"""
print("https://api.github.com/search/repositories?q=crypto+language:c%2b%2b&sort=stars&order=desc")
res=requests.get("https://api.github.com/search/repositories?q=crypto+language:c%2b%2b&sort=stars&order=desc")
rj=res.json()
for item in rj['items']:
  print(item["full_name"])
res=requests.get("https://api.github.com/search/repositories?q=security+language:c&sort=stars&order=desc")
rj=res.json()
for item in rj['items']:
  print(item["full_name"])
  print("https://api.github.com/search/code?q=openssl+in:file+language:c+repo:"+item["full_name"])
print("https://api.github.com/search/repositories?q=crypto+language:c%2b%2b&sort=stars&order=desc")
res=requests.get("https://api.github.com/search/repositories?q=security+language:c%2b%2b&sort=stars&order=desc")
rj=res.json()
for item in rj['items']:
  print(item["full_name"])
"""
#sys.exit(0)
