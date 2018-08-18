from ezdb import EZDBClient


db = EZDBClient('clientdblist', 'http://127.0.0.1:5000', printouts = False, root_struct = list, max_retries = 3) 
db.clear()
db.append(1)
db.append(2)
db.append([db])
assert db == [1, 2, [[1, 2]]]
db = EZDBClient('clientdb', 'http://127.0.0.1:5000', printouts = False, root_struct = dict, max_retries = 3) 

db["asdf"]={}
db.clear()
db["asdf"]=1
db["asdf"]=db["asdf"]+1
db["none"]=None
db["arrfff"]={}
db["arrfff"]['i1']="success"
db['alist'] = []
db['alist'].append(2)
db['alist'].append(1)
db['alist'].append('three')
db['alist'].append([2,3,"3x"])

#print (json.dumps(intruder()))
#db["int"]=intruder()
#db['alist'].append(db['alist'])
k = db['alist']
db['alist'].extend(db['alist'])
assert [2,3,"3x"] in db['alist']
db['alist'].sort(reverse=True)
db['alist'] = sorted(db['alist'],reverse=True)
assert db == {'none': None, 'arrfff': {'i1': 'success'}, 'alist': ['three', 'three', [2, 3, '3x'], [2, 3, '3x'], 2, 2, 1, 1], 'asdf': 2}

