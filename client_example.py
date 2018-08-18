from ezdb import EZDBClient

#Demonstrates opening a new database with the root structure as a list. 
db = EZDBClient('client_db_list', 'http://127.0.0.1:5000',
                root_struct=list, max_retries=3)
db.clear() #Clearing database, otherwise the
db.append(1)
db.append(2)
db.append([db])
db.extend(db)
#A test: compare the database state with expected results
assert db == [1, 2, [[1, 2]], 1, 2, [[1, 2]]]

#Now we interact with a new database, with a root type of dict
db = EZDBClient('client_db_dict', 'http://127.0.0.1:5000',
                root_struct=dict, max_retries=3)
db.clear()
db["an_int"] = 1
db["an_int"] = db["an_int"] + 1 # can reference existing keys for assignment
db["none"] = None #None type supported
db["subdict"] = {}
db["subdict"]['subsubdict'] = "success"
db['alist'] = []
db['alist'].append(2)
db['alist'].append(1)
db['alist'].append('three')
db['alist'].append([2, 3, "3x"])
db['alist'].append(db['alist']) # Getting more complicated

k = db['alist'] #Can save a reference
db['alist'].extend(k)
assert [2, 3, "3x"] in db['alist'] #'in' keyword supported

#Sort the data, either way, keywords supported
db['alist'].sort(reverse=False)
db['alist'] = sorted(db['alist'], reverse=True)
#Test the final result
assert db == {u'none': None, u'alist': [u'three', u'three', [2, 3, u'3x'], [2, 3, u'3x'], [2, 1, u'three', [2, 3, u'3x']], [2, 1, u'three', [2, 3, u'3x']], 2, 2, 1, 1], u'an_int': 2, u'subdict': {u'subsubdict': u'success'}}