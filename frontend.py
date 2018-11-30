#!/usr/bin/python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
import urllib
import os
import sys
import re
import html
import random

"""
I would've used flask, but it wasn't available on the linux lab computers, which I wanted my code to be runnable on
As a result, I'm doing really dumb HTML generation that's really hard to follow.
Basically, there's 5 pages, which I'm parsing GET params to determine:
home
crypto_library
library <-- non-crypto libraries
owner
topic
"""

crypto_libraries=[
  {"name":"openssl/openssl","indicators":["include openssl"],"infolink":"https://www.openssl.org/"},
  {"name":"jedisct1/libsodium","indicators":["include sodium"],"infolink":"https://github.com/jedisct1/libsodium/blob/master/README.markdown"},
  {"name":"wolfSSL/wolfssl","indicators":["include wolfssl"],"infolink":"https://www.wolfssl.com/"},
  {"name":"gnutls/gnutls","indicators":["include gnutls"],"infolink":"https://www.gnutls.org/"},
  {"name":"libtom/libtomcrypt","indicators":["include tomcrypt"],"infolink":"https://github.com/libtom/libtomcrypt/blob/develop/README.md"},
  {"name":"ARMmbed/mbedtls","indicators":["include mbedtls","include polarssl"],"infolink":"https://tls.mbed.org/"},
  {"name":"breadwallet/nettle","indicators":["include nettle"], "infolink":"https://www.lysator.liu.se/~nisse/nettle/"},
  {"name":"gpg/libgcrypt","indicators":["include gcrypt"], "infolink":"https://www.gnupg.org/software/libgcrypt/index.html"},
  {"name":"matrixssl/matrixssl","indicators":["include matrixssl"], "infolink":"https://github.com/matrixssl/matrixssl/blob/master/README.md"}
  #{"name":"nss-dev/nss","indicators":["include nss"], "infolink":"https://developer.mozilla.org/en-US/docs/Mozilla/Projects/NSS"},
  #{"name":"weidai11/cryptopp","indicators":["include cryptopp"],"infolink":"https://www.cryptopp.com/"},
  #{"name":"randombit/botan","indicators":["include botan"],"infolink":"https://botan.randombit.net/"},
  #{"name":"ryankurte/cryptlib","indicators":["include cryptlib"],"infolink":"https://www.cs.auckland.ac.nz/~pgut001/cryptlib/"},
]

if len(sys.argv)<4:
  print("Please call this program with 3 parameters:")
  print(""+sys.argv[0]+" <host> <dbname> <user>")
  sys.exit(1)
host=sys.argv[1]
dbname=sys.argv[2]
user=sys.argv[3]
try:
  pgpass = os.environ['PGPASSWORD']
except KeyError as e:
  print("Please define the pgpass as a bash environment variable, PGPASSWORD")
  print("For example:")
  print("export PGPASSWORD=my+pg+pass\n"+sys.argv[0]+" <host> <dbname> <user>")
  sys.exit(1)
  
conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+pgpass+" host="+host+"")
cur=conn.cursor()

def get_crypto_lib_display_name(full_name):
  return full_name[full_name.find('/')+1:]

class GitsecServer(BaseHTTPRequestHandler):
  def do_GET(self):
    qs=urllib.parse.parse_qs(self.path[self.path.find('?')+1:])
    for key,value in qs.items():
      print(html.escape("test'"))
      qs[key]=[html.escape(value[0])]
    print(qs)
    crypto_library=None
    if 'crypto_library' in qs:
      crypto_library=qs['crypto_library'][0]
    library=None
    if 'library' in qs:
      library=qs['library'][0]
    owner=None
    if 'owner' in qs:
      owner=qs['owner'][0]
    topic=None
    if 'topic' in qs:
      topic=qs['topic'][0]
    page='home'
    if library!=None:
      page='library'
    elif crypto_library!=None:
      page='crypto_library'
    elif owner!=None:
      page='owner'
    elif topic!=None:
      page='topic'
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(bytes("<style>body{ background-position: center; background-image:url('https://scottgriffy.com/databases.png');} table, th, td { border: 1px solid black; border-collapse: collapse; padding:1em; }</style>", encoding='utf-8'))
    self.wfile.write(bytes("<div style=\"border:2px solid #ccc;background-color:rgba(240,240,240,.7);filter: alpha(opacity=50);;position:absolute;left:50%;text-align:left;width:1100px;padding:20px;margin-left:-550px;\">",encoding='utf-8'))
    self.wfile.write(bytes("A survey of crypto library usage in Github Repositories. Created by Scott Griffy for Charles Winstead's CS586 Introduction to DBMS class at Portland State University, Fall 2018.<br/><br/>",encoding='utf-8'))
    cur.execute("select count(*) from \"gitsec.Repo\";")
    num_repos=0
    for row in cur:
      num_repos=row[0]
    self.wfile.write(bytes("This program searched over the top "+str(num_repos)+" Github repos with the most stars and searched their code to check which crypto library they use. It was limited to C code.<br/><br/>", encoding='utf-8'))
    if page=='home':
      datas=[]
      names=[]
      colors=[]
      for lib in crypto_libraries:
        cur.execute("select count(num_indicators) from \"gitsec.UsesCryptoLibrary\" U inner join \"gitsec.CryptoProvidingRepo\" P on crypto_library=repo_name where crypto_library='"+lib["name"]+"' and U.num_indicators>0 and (P.hide_from_ui <> '1' or P.hide_from_ui is null);")
        names.append(get_crypto_lib_display_name(lib["name"]))
        for row in cur:
          print(row[0])
          datas.append(row[0])
      names_list=str(names)
      datas_list=str(datas)
      colors=['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000'][:len(crypto_libraries)]
      colors_list=str(colors)
      print(colors_list)
      self.wfile.write(bytes("choose a crypto library:<br/>", encoding='utf-8'))
      for idx,lib in enumerate(crypto_libraries):
        self.wfile.write(bytes("<a href=\"/?crypto_library="+lib["name"]+"\">"+get_crypto_lib_display_name(lib["name"])+"</a>&nbsp;&nbsp;-&nbsp;&nbsp;",encoding='utf-8'))
        self.wfile.write(bytes("<a href=\""+lib["infolink"]+"\">info</a>&nbsp;&nbsp;-&nbsp;&nbsp;",encoding='utf-8'))
        self.wfile.write(bytes("used in "+str(datas[idx])+" repos",encoding='utf-8'))
        self.wfile.write(bytes("<br/>",encoding='utf-8'))
      self.wfile.write(bytes("<script src=\"https://scottgriffy.com/Chart.min.js\"></script>", encoding='utf-8'))
      self.wfile.write(bytes("""<div style=\"height:300px;width:300px\">
<canvas id=\"pie-chart\" ></canvas></div>""", encoding='utf-8'))
      self.wfile.write(bytes("""<script>
new Chart(document.getElementById("pie-chart"), {
type: 'pie',
data: {
  labels: """+names_list+""",
  datasets: [{
    label: "Usages",
    backgroundColor: """+colors_list+""",
    data: """+datas_list+"""
  }]
},
options: {
  title: {
    display: true,
    text: 'Usage of crypto libraries (by times included)'
  }
}
});</script>""", encoding='utf-8'))
    else: # we're not drawing the home page
      if page=='library':
        self.wfile.write(bytes("Confidence is based on the number of instances of 'include [crypto library]' found in the C code in the repo<br/><br/>", encoding='utf-8'))
      elif page=='crypto_library':
        libobj=None
        for lib in crypto_libraries:
          if lib["name"] == crypto_library:
            libobj=lib
            break
        indicator=libobj["indicators"][0]
        self.wfile.write(bytes("Confidence is based on the number of instances of '"+indicator+"' found in the C code in the repo<br/><br/>", encoding='utf-8'))
      if library!=None:
        self.wfile.write(bytes("You are viewing the crypto libraries used by "+library+"<br/>", encoding='utf-8'))
      elif page=='crypto_library':
        self.wfile.write(bytes("You are viewing the github repos that use "+get_crypto_lib_display_name(crypto_library)+"<br/>", encoding='utf-8'))
      elif page=='owner':
        self.wfile.write(bytes("You are viewing the repos owned by "+owner+"<br/>", encoding='utf-8'))
      elif page=='topic':
        self.wfile.write(bytes("You are viewing the repos related to the topic: "+topic+"<br/>", encoding='utf-8'))
      repo_name=library if library!=None else crypto_library
      # testing out users:
      # select R1.full_name,R2.full_name,R1.owner from "gitsec.Repo" R1 inner join "gitsec.Repo" R2 on R1.owner=R2.owner and R1.full_name!=R2.full_name;
      if page=='library' or page=='crypto_library':
        cur.execute("select bugs,stars,pulls,forks,owner from \"gitsec.Repo\" where full_name='"+repo_name+"';")
        for row in cur:
          self.wfile.write(bytes("This repo has "+str(0 if row[0]==None else row[0])+" open issues<br/>", encoding='utf-8'))
          self.wfile.write(bytes("This repo has "+str(0 if row[1]==None else row[1])+" stars<br/>", encoding='utf-8'))
          self.wfile.write(bytes("This repo has "+str(0 if row[2]==None else row[2])+" pulls<br/>", encoding='utf-8'))
          self.wfile.write(bytes("This repo has "+str(0 if row[3]==None else row[3])+" forks<br/>", encoding='utf-8'))
          self.wfile.write(bytes("This repo is owned by <a href=\"/?owner="+row[4]+"\">"+row[4]+"</a><br/>", encoding='utf-8'))
        cur.execute("select topic_name from \"gitsec.RelatedToTopic\" inner join \"gitsec.Repo\" on full_name=repo_name where full_name='"+repo_name+"';")
        topics=[]
        for row in cur:
          topics.append(str(row[0]))
        if len(topics)>0:
          self.wfile.write(bytes("This repo is related to the following topics: ", encoding='utf-8'))
          for topic in topics:
            self.wfile.write(bytes("<a href=\"/?topic="+topic+"\">"+topic+"</a>, ", encoding='utf-8'))
          self.wfile.write(bytes("<br/>", encoding='utf-8'))
          
      self.wfile.write(bytes("<a href=\"/\">back to home</a><br/><br/>", encoding='utf-8'))
      # first, we're going to query the table
      if page=='library':
        self.wfile.write(bytes("Here are the crypto libraries that this repo uses:", encoding='utf-8'))
      elif page=='crypto_library':
        self.wfile.write(bytes("Here are the repos that use this crypto library:", encoding='utf-8'))
      if page=='library':
        cur.execute("select U.library,P.repo_name,U.num_indicators,stars from \"gitsec.Repo\" R inner join \"gitsec.UsesCryptoLibrary\" U on R.full_name=U.library inner join \"gitsec.CryptoProvidingRepo\" P on crypto_library=repo_name where num_indicators>0 and U.library='"+library+"' and (P.hide_from_ui <> '1' or P.hide_from_ui is null) order by num_indicators desc;")
      elif page=='crypto_library':
        cur.execute("select U.library,P.repo_name,U.num_indicators,stars from \"gitsec.Repo\" R inner join \"gitsec.UsesCryptoLibrary\" U on R.full_name=U.library inner join \"gitsec.CryptoProvidingRepo\" P on crypto_library=repo_name where num_indicators>0 and U.crypto_library='"+crypto_library+"' and (P.hide_from_ui <> '1' or P.hide_from_ui is null) order by num_indicators desc;")
      elif page=='owner':
        # these two queries are especially bad.
        # basically, I wanted the top crypto_library and it's number of indicators, but could've figure out how to reuse a subquery
        # so, the subquery is pasted twice, selecting a different column
        # hopefully that info makes it easier to read
        cur.execute("""
select 
  R.full_name,
  (select crypto_library from \"gitsec.UsesCryptoLibrary\" U inner join \"gitsec.CryptoProvidingRepo\" P on U.crypto_library=P.repo_name where U.library=R.full_name and (P.hide_from_ui <> '1' or P.hide_from_ui is null) order by num_indicators desc limit 1),
  (select num_indicators from \"gitsec.UsesCryptoLibrary\" U inner join \"gitsec.CryptoProvidingRepo\" P on U.crypto_library=P.repo_name where U.library=R.full_name and (P.hide_from_ui <> '1' or P.hide_from_ui is null) order by num_indicators desc limit 1),
  R.stars
from \"gitsec.Repo\" R where owner='"""+owner+"""' order by num_indicators desc;
""")
      elif page=='topic':
        cur.execute("""
select
  R.full_name,
  (select crypto_library from \"gitsec.UsesCryptoLibrary\" U inner join \"gitsec.CryptoProvidingRepo\" P on U.crypto_library=P.repo_name where U.library=R.full_name and (P.hide_from_ui <> '1' or P.hide_from_ui is null) order by num_indicators desc limit 1),
  (select num_indicators from \"gitsec.UsesCryptoLibrary\" U inner join \"gitsec.CryptoProvidingRepo\" P on U.crypto_library=P.repo_name where U.library=R.full_name and (P.hide_from_ui <> '1' or P.hide_from_ui is null) order by num_indicators desc limit 1),
  R.stars
from \"gitsec.Repo\" R inner join \"gitsec.RelatedToTopic\" T on R.full_name=T.repo_name where topic_name='"""+topic+"""' order by num_indicators desc;""")
      # now, we draw the table
      if page=='library' or page=='crypto_library':
        self.wfile.write(bytes("<table>", encoding='utf-8'))
        self.wfile.write(bytes("""<tr>
<td>repo name</td>
<td>stars</td>
<td>uses crypto library</td>
<td>confidence</td>
<td>link</td></tr>
""", encoding='utf-8'))
        for row in cur:
          libobj=None
          for lib in crypto_libraries:
            if lib["name"] == str(row[1]):
              libobj=lib
              break
          indicator=libobj["indicators"][0]
          link="https://github.com/"+str(row[0])+"/search?q="+indicator+""
          self.wfile.write(bytes("""
<tr>
<td><a href=\"/?library="""+str(row[0])+"""\">"""+str(row[0])+"""</a></td>
<td>"""+str(row[3])+"""</td>
<td><a href=\"/?crypto_library="""+str(row[1])+"""\">"""+str(row[1])+"""</a></td>
<td>"""+str(row[2])+"""</td>
<td><a href=\""""+link+"""\">"""+link+"""</a></td>
</tr>
""", encoding='utf-8'))
        self.wfile.write(bytes("</table>", encoding='utf-8'))
      elif page=='owner' or page=='topic':
        self.wfile.write(bytes("<table>", encoding='utf-8'))
        self.wfile.write(bytes("<tr><td>repo name</td><td>stars</td><td>most used crypto library</td><td>confidence</td></tr>", encoding='utf-8'))
        for row in cur:
          if int(row[2]!=0):
            self.wfile.write(bytes("""
<tr>
<td><a href=\"/?library="""+str(row[0])+"""\">"""+str(row[0])+"""</a></td>
<td>"""+str(row[3])+"""</td>
<td><a href=\"/?crypto_library="""+str(row[1])+"""\">"""+str(row[1])+"""</a></td>
<td>"""+str(row[2])+"""</td>
</tr>
""", encoding='utf-8'))
        self.wfile.write(bytes("</table>", encoding='utf-8'))
    self.wfile.write(bytes("</div>",encoding='utf-8'))

def run(server_class=HTTPServer, handler_class=GitsecServer):
  server_address = ('', 8002)
  httpd = server_class(server_address, handler_class)
  httpd.serve_forever()

if __name__ == '__main__':
  run()
