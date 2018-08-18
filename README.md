# ezdb
(Python 2) Access a remote database like you would a native structure

This library provides two components:
- EZDBServer Class:
  A Flask webserver which provides endpoints for reading and writing to a database. The database can store any data which is compliant with the JSON format. The database is automatically backed up and will attempt to rollback from faulty states
- EZDBClient Class: 
  This client interfaceses with the database as if you were simply using a python built-in dictionary or list. All calls made will automatically get/set changes to the database when appropriate. All dictionary and list methods are supported (inherited). Note, only JSON-compatible structures are supported  

# Example Server:
```python
from flask import Flask
from flask_restful import Api
from ezdb import EZDBServer

app = Flask(__name__)
api = Api(app)
api.add_resource(EZDBServer, '/<string:get_msg_unicode>')
if __name__ == '__main__':
    app.run(debug=True)
```

# Example Client:
```python
from ezdb import EZDBClient

#Demonstrates opening a new database with the root structure as a list. If no such DB exists, one will be made
db = EZDBClient('client_db_list', 'http://127.0.0.1:5000',
                root_struct=list, max_retries=3)
db.clear() #Clearing database, otherwise the state will be as you left it
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
assert db == {u'none': None, u'alist': [u'three', u'three', [2, 3, u'3x'], [2, 3, u'3x'], [2, 1, u'three', [2, 3, u'3x']], [2, 1, u'three', [2, 3, u'3x']], 2, 2, 1, 1], u'an_int': 2, u'subdict': {u'subsubdict': u'success'}}```
```

# Features:
- By its design, any number of clients can access the same data, using it for storge or client-to-client communcation. The design is inherently threadsafe, though the database may change between client requests
- You can configure how many attempts will be made for a given query. If the query still fails, an assert will be failed
  
# Limitations:
- You cannot assign to your EZDBClient object directly, due to limitations of the language. For example the following would overwrite the client with a simple dictionary:
```python
  db = EZDBClient('client_db_list', 'http://127.0.0.1:5000')
  db = {} #This would be overwriting the magical db structure with simple dict!
```

- As mentioned before, only JSON-like structures can be managed (think int, bool, float, list, dict). You may consider manual serialization of your classes to JSON before storage

- The library runs evaluates strings as code and as such poses a security threat. Consider configuring flasks security features to only allow trusted users

