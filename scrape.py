#!/usr/bin/python3
import traceback
import requests
import sys
import os
import psycopg2
import html
import datetime
import time

# Hi! I put in some comments to help you read this code, but it's still a mess.
# Also, this code will continue where it left off, so you can interrupt a scrape and it'll find where it stopped
# But, if you change anything between invocations, you'll have to add in some update statements (in place of the insert statements)
# I've got some select/udpate statements from when I had to re-run this to add in the rest of the columns (after Wednesday)

# here's the hard coded data that makes the crypto search possible
# here, we define what crypto libraries we're going to check each popular library against
# and the search term we're using to do so ('indicators')
# multiple indicators were supported to improve accuracy, but it ended up only being useful for one library, which had a previous name (mbedtls)
crypto_libraries=[
  {"name":"openssl/openssl","indicators":["include openssl"]},
  {"name":"breadwallet/nettle","indicators":["include nettle"]},
  {"name":"gpg/libgcrypt","indicators":["include gcrypt"]},
  {"name":"matrixssl/matrixssl","indicators":["include matrixssl"]},
  {"name":"jedisct1/libsodium","indicators":["include sodium"]},
  {"name":"wolfSSL/wolfssl","indicators":["include wolfssl"]},
  {"name":"gnutls/gnutls","indicators":["include gnutls"]},
  {"name":"libtom/libtomcrypt","indicators":["include tomcrypt"]},
  {"name":"ARMmbed/mbedtls","indicators":["include mbedtls","include polarssl"]}
  #{"name":"nss-dev/nss","indicators":["include nss"]},
  #{"name":"ryankurte/cryptlib","indicators":["include cryptlib"]},
  #{"name":"weidai11/cryptopp","indicators":["include cryptopp"]},
  #{"name":"randombit/botan","indicators":["include botan"]},
]

if len(sys.argv)<4:
  print("Please call this program with 3 parameters:")
  print(""+sys.argv[0]+" <host> <dbname> <user>")
  print("ex:")
  print(""+sys.argv[0]+" dbclass.cs.pdx.edu f18wdb15 f18wdb15")
  sys.exit(1)
host=sys.argv[1]
dbname=sys.argv[2]
user=sys.argv[3]
pgpass = None
try:
  pgpass = os.environ['PGPASSWORD']
except KeyError as e:
  print("Please define the pgpass as a bash environment variable, PGPASSWORD")
  print("For example:")
  print("export PGPASSWORD=my+pg+pass\n"+sys.argv[0]+" <host> <dbname> <user>")
  sys.exit(1)
client_user = None
try:
  client_user = os.environ['GITHUB_USER']
except:
  print("Please define your github username as a bash environment variable, GITHUB_USER")
  print("For example:")
  print("export GITHUB_USER=grifball\n"+sys.argv[0]+" <host> <dbname> <user>")
  sys.exit(1)
client_auth = None
try:
  client_auth = os.environ['GITHUB_AUTH']
except:
  print("Please define a personal access token as a bash environment variable, GITHUB_AUTH")
  print("For example:")
  print("export GITHUB_AUTH=myGHtoken385ab356dfe7bd78bed\n"+sys.argv[0]+" <host> <dbname> <user>")
  print("Github doesn't like anonymous users using their API for code searching")
  print("goto https://github.com/settings/tokens to get a token for this")
  sys.exit(1)

conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+pgpass+" host="+host+"")
cur=conn.cursor()
auth=(client_user, client_auth)
rj=requests.get("https://api.github.com/rate_limit", auth=auth).json()
print(rj["resources"]["search"])
print(rj["resources"]["search"]["remaining"])
def do_query(cur, query):
  # rolled the error handling into one function
  # we don't really care about transactions and whether they completed because we're the only one using the database
  # and our transactions are really just one insertion
  # don't use this for select queries, otherwise you won't get the results
  try:
    cur.execute(query)
  except Exception as e:
    print("failed on: "+query)
    cur.execute("ROLLBACK")
  else:
    cur.execute("COMMIT")
def spin_til_full_ready():
  # this function will sleep/check until our rate is acceptible
  # I was too lazy to see exactly what counted as a search or a 'core' query, so I just wait until ALL rates are above 0
  ready=0
  while ready==0:
    rj=requests.get("https://api.github.com/rate_limit", auth=auth).json()
    print(rj)
    ready=1
    try:
      if int(rj["resources"]["search"]["remaining"])==0:
        ready=0
      if int(rj["resources"]["core"]["remaining"])==0:
        ready=0
      if int(rj["rate"]["remaining"])==0:
        ready=0
    except Exception as e:
      # got a server error here once, hope it wasn't anything serious
      print("Wow! a server error? Let's give them some time to sort that out...")
      time.sleep(60)
      ready=0
    if ready==1:
      break
    time.sleep(1)
def load_til_200(url):
  res=None
  while res==None or res.status_code!=200:
    spin_til_full_ready()
    # have to have that accept header to get topics (I guess they're testing it)
    headers = {'Accept':'application/vnd.github.mercy-preview+json'}
    res=requests.get(url, headers=headers, auth=auth)
    if res.status_code==200:
      break
    else:
      # no idea why github is booting us out here...
      # I'm obeying their rate limits just like they tell me too
      # there's also no way to pay for better query rates
      # infuriating
      print(res.status_code)
      print(res.text)
      print("Uh oh, we're abusing their API! Better back off... sleeping for a minute")
    time.sleep(60)
  return res
def get_repo(name):
  # here's where the spaghetti code begins
  # first, check if we already got this repo
  cur.execute("select * from \"gitsec.Repo\" where full_name='"+name+"';")
  num_rows=0 # there is probably a better way to do this, I'm just checking if we got any rows
  for row in cur:
    num_rows+=1
  if num_rows==0:# or True: # used 'if True' here when I wanted to force updates
    # grabbing the repo
    res=load_til_200("https://api.github.com/repos/"+name)
    print(res)
    print(res.text)
    rj=res.json()
    full_name=str(rj['full_name'])
    forks=str(rj['forks'])
    owner=str(rj['owner']['login'])
    org_name="no_organization" # I added this in manually (in the schema generation, there's an insert command at the end), I know it really should be 'null' but I didn't wanna mess with the insert/update statement further
    if True: # just indenting this sub query
      # insert their organization into the db (if they have one)
      if "organization" in rj:
        org=rj["organization"]
        org_name=org["login"]
        #cur.execute("select * from \"gitsec.User\" where name='"+owner+"';")
        do_query(cur, "insert into \"gitsec.Organization\" (name) values ('"+org_name+"');")
    if True: # just indenting this sub query
      # insert the owner of this repo into the db
      res2=load_til_200("https://api.github.com/users/"+owner)
      rj2=res2.json()
      # don't mind this crazy date conversion, it was the best I could do with the default repos in the linux lab
      # this is copy and pasted into multiple places here
      created_at2=str(int(time.mktime(datetime.datetime.strptime(rj2['created_at'], "%Y-%m-%dT%H:%M:%SZ").date().timetuple())))
      num_repos=str(rj2['public_repos'])
      followers=str(rj2['followers'])
      following=str(rj2['following'])
      # check if this user already exists
      cur.execute("select count(*) from \"gitsec.User\" where name='"+owner+"';")
      exists=False
      for row in cur:
        exists=True if str(row[0])=="1" else False
      if exists:
        # update them if they do exist (this was added because I changed the columns between runs)
        do_query(cur, "update \"gitsec.User\" set name='"+owner+"', joined_at='"+created_at2+"', num_repos='"+num_repos+"', followers='"+followers+"', following='"+following+"' where name='"+owner+"';")
      else:
        do_query(cur, "insert into \"gitsec.User\" (name, joined_at, num_repos, followers, following) values ('"+owner+"','"+created_at2+"','"+num_repos+"','"+followers+"','"+following+"');")
    if True: # just indenting this sub query
      # get and insert the topics for this repo
      res2=load_til_200("https://api.github.com/repos/"+full_name+"/topics")
      rj2=res2.json()
      for name in rj2["names"]:
        do_query(cur, "insert into \"gitsec.Topic\" (topic_name) values ('"+name+"');")
        do_query(cur, "insert into \"gitsec.RelatedToTopic\" (topic_name, repo_name) values ('"+name+"','"+full_name+"');")
    if True: # just indenting this sub query
      # get the languages of this repo
      res2=load_til_200("https://api.github.com/repos/"+full_name+"/languages")
      rj2=res2.json()
      print(rj2.keys())
      for lang in rj2.keys():
        # link this repo to it's languages
        print(lang)
        do_query(cur, "insert into \"gitsec.Language\" (language_name) values ('"+lang+"');")
        do_query(cur, "insert into \"gitsec.UsesLanguage\" (language_name, repo_name, instances) values ('"+lang+"','"+full_name+"','"+str(rj2[lang])+"');")
    pulls=-1
    if True: # just indenting this sub query
      # this is a trick I found to get the number of pulls
      # the latest one is always first and it has a 'number' that's been counting from 0
      # so, the 'number' of the latest pull is also the number of pulls!
      res2=load_til_200("https://api.github.com/repos/"+full_name+"/pulls")
      rj2=res2.json()
      pulls=0
      if len(rj2)>0:
        pulls=rj2[0]["number"]
    stars=str(rj['stargazers_count'])
    num_issues=str(rj['open_issues'])
    subscribers=str(rj['subscribers_count'])
    created_dt=datetime.datetime.strptime(rj['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
    created_at=str(int(time.mktime(created_dt.timetuple())))
    # see if we already inserted this repo (checked again in case we're forcing updates)
    cur.execute("select count(*) from \"gitsec.Repo\" where full_name='"+full_name+"';")
    exists=False
    for row in cur:
      exists=True if str(row[0])=="1" else False
    if exists:
      # if we already inserted this repo, update it
      do_query(cur, "update \"gitsec.Repo\" set full_name='"+full_name+"', owner='"+owner+"', forks='"+forks+"', stars='"+stars+"', created_at='"+created_at+"', subscribers='"+subscribers+"', bugs='"+num_issues+"', pulls='"+str(pulls)+"', organization_name='"+org_name+"' where full_name='"+full_name+"';")
    else:
      do_query(cur, "insert into \"gitsec.Repo\" (full_name, owner, forks, stars, created_at, subscribers, bugs, pulls, organization_name) values ('"+full_name+"','"+owner+"','"+forks+"','"+stars+"','"+created_at+"','"+subscribers+"','"+num_issues+"','"+str(pulls)+"','"+org_name+"');")
    return res # return the result of the initial repo query if we want to do more Ops
  return None # if we already inserted this repo, and we're not forcing updates, return None (don't need to do operations)
def fill_db():
  # first, get info about all the crypto libraries
  for lib in crypto_libraries:
    res=get_repo(lib["name"])
    if res!=None:
      rj=res.json()
      full_name=str(rj['full_name'])
      # it's a crypto providing repo, so update that table as well
      do_query(cur, "insert into \"gitsec.CryptoProvidingRepo\" (repo_name) values ('"+full_name+"');")
      for keyword in lib["indicators"]:
        # add in all the indicators as well
        # these are used to search later, but they're also hard coded in the crypto_libraries dict
        do_query(cur, "insert into \"gitsec.UsageIndicator\" (repo_name,keyword) values ('"+full_name+"','"+keyword+"');")
        
  for page in range(1,30):
    # here's where we start grabbing popular C repos:
    pageq="https://api.github.com/search/repositories?q=language:c&sort=stars&order=desc&page="+str(page)
    print(pageq)
    res=load_til_200(pageq)
    rj1=res.json()
    for item in rj1['items']:
      res=get_repo(item["full_name"]) # add the repo
      # check if it was a crypto library:
      is_crypto_repo=False
      full_name=item["full_name"]
      for clib in crypto_libraries:
        if item["full_name"]==clib["name"]:
          is_crypto_repo=True
          break
      # if not, update 'CryptoUsingRepo'
      if not is_crypto_repo:
        do_query(cur, "insert into \"gitsec.CryptoUsingRepo\" (repo_name) values ('"+full_name+"');")
      worth_checking=0
      # here's the real expensive part, we're going to search this repo's code for each of out indicators and tally up the number of times it includes each crypto library
      # first, see if we have to do this at all
      for lib in crypto_libraries:
        cur.execute("select * from \"gitsec.UsesCryptoLibrary\" where library='"+item["full_name"]+"' and crypto_library='"+lib["name"]+"';")
        num_rows=0
        for row in cur:
          num_rows+=1
        if num_rows==0: # we haven't checked this combo of crypto lib and repo
          worth_checking=1
      if worth_checking==1:
        print(item["full_name"])
        # iterate through our crypto_libraries:
        for lib in crypto_libraries:
          cur.execute("select * from \"gitsec.UsesCryptoLibrary\" where library='"+item["full_name"]+"' and crypto_library='"+lib["name"]+"';")
          num_rows=0
          for row in cur:
            num_rows+=1
          # I'm checking thsi twice, this is an arifact of re-running the code
          # This whole process is so slow that checking each individual combination is important
          if num_rows==0: # we haven't checked this combo of crypto lib and repo
            indicators=0
            # go through this crypto library's indicators and tally up the number of results the search got
            for keyword in lib["indicators"]:
              res=load_til_200("https://api.github.com/search/code?q="+keyword+"+in:file+language:c+repo:"+item["full_name"])
              print(res)
              print(res.text)
              rj=res.json()
              instances=rj["total_count"]
              print("instances: "+str(instances)+" of "+lib["name"]+" in "+item["full_name"]+" using keyword: "+keyword)
              indicators+=instances
            do_query(cur, "insert into \"gitsec.UsesCryptoLibrary\" (library, crypto_library, num_indicators) values ('"+item["full_name"]+"','"+lib["name"]+"','"+str(indicators)+"');")

if __name__=='__main__':
  fill_db()
