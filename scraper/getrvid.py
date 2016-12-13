import json
import wikipedia
import requests

f = open('result.json')
query ='Reverse Engineering'
headers=[{'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'},
{'user-agent':'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.8.1.8pre) Gecko/20070928 Firefox/2.0.0.7 Navigator/9.0RC1'},
{'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'}]
pageid = wikipedia.page(query).pageid
count =0
failure = []
while True:
  str_json = f.readline()
  if str_json == '':
    break;
  cur_json = json.loads(str_json)
  rvid = str(cur_json['rvid'][cur_json['rvid'].index('oldid=')+6:])
  # debug
  print str(count)+ ': '+ rvid+' '
  count+=1

  url = 'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&revids='+ rvid +'&rvprop=ids%7Ctimestamp%7Cuser%7Ccomment%7Ccontent&&format=json'
  try:
    r = requests.get(url,headers=headers[int(rvid)%3],timeout=10)
    js = r.json()
    # content = js['query']['pages'][str(pageid).decode('utf-8')]['revisions'][0]["*"]
    filename = 'store/'+str(js['query']['pages'][str(pageid)]['revisions'][0]['revid'])
    ff = open(filename,'w')
    ff.write(json.dumps(js))
    ff.close()
  except:
    print "error:",rvid
    print headers[int(rvid)%3]
    failure.append(rvid)

print 'failure:'
print failure
