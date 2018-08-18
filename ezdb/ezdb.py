from __future__ import print_function
import urllib2
import sys
import os
from flask_restful import Resource
import pickle
import json
from time import sleep, strftime


class EZDBClient():
    def __init__(self, subkeys, url, printouts=False,
                 time_between_retry=.0005, max_retries=3, root_struct=dict):
        self.time_between_retry = time_between_retry
        self.max_retries = max_retries
        self.url = url
        self.printouts = printouts
        self.root_struct = root_struct
        if url[-1] != '/':  # Need end fwslash
            self.url = url+'/'

        # a root db client, not a subkeym requires initilaization
        if not isinstance(subkeys, list):
            self.subkeys = [str(subkeys)]
            root_copy = self.__get_root()
            # need to setup root node as root_struct if client db
            # does not exist
            if str(subkeys) not in root_copy or not isinstance(root_copy[self.subkeys[0]], root_struct):
                self.__keep_trying(
                    EZDBClient.__url_encode(self.__make_url_path() + ' = ' + str(root_struct())))
        else:
            self.subkeys = subkeys  # list case, i.e. a non-root node

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass

    def __keep_trying(self, urlCall):
        success = False
        num_retries = 0
        if self.printouts:
            print("sending " + urlCall)
        while not success and num_retries < self.max_retries:
            success, resp = EZDBClient.__parse_response(
                urllib2.urlopen(urlCall).read())
            num_retries += 1
            if not success and num_retries < self.max_retries:
                sleep(self.time_between_retry)
        assert success
        return resp

    def __getitem__(self,  key):
        urlcall = EZDBClient.__url_encode(self.__make_url_path(key))
        if self.printouts:
            print("get "+urlcall)
        ret_item = self.__keep_trying(urlcall)
        if ret_item is None or type(ret_item) in [int, float, str, bool]:
            return ret_item
        else:  # non primitives need to be a web reference, i.e. EZDBClient pointing to a deeper key
            child_subkeys = [x for x in self.subkeys]
            child_subkeys.append(key)
            return EZDBClient(child_subkeys, self.url, printouts=self.printouts)

    def __setitem__(self,  key, item):
        urlcall = EZDBClient.__url_encode(self.__make_url_path(
            key) + '=' + EZDBClient.__string_wrap(item))
        if self.printouts:
            print("set "+urlcall)
        self.__keep_trying(urlcall)

    def __get_self(self):
        urlcall = EZDBClient.__url_encode(self.__make_url_path())
        if self.printouts:
            print("__get_self "+urlcall)
        resp = self.__keep_trying(urlcall)
        return resp

    def __set_self_from_struct(self, item):
        urlcall = EZDBClient.__url_encode(
            self.__make_url_path()+'=' + EZDBClient.__string_wrap(item))
        if self.printouts:
            print("__set_self_from_struct "+urlcall)
        return urllib2.urlopen(urlcall).read()

    def __get_root(self):
        resp = self.__keep_trying(self.url+'root')
        return resp

    def __make_url_path(self, extraKey=None):
        tunneledURL = self.url + self.subkeys[0]
        for url in self.subkeys[1:]:
            tunneledURL += '[' + EZDBClient.__string_wrap(url) + ']'
        if extraKey:
            tunneledURL += '[' + EZDBClient.__string_wrap(extraKey) + ']'
        return str(tunneledURL)

    def __str__(self):
        return str(self.__get_self())

    def __as_local_copy(self, item):
        if not isinstance(item, EZDBClient):
            return item
        return eval(str(item))

    def __function_closure(self, func, mod, *args, **kwargs):
        cleanArgs = [self.__as_local_copy(item) for item in args]
        ret = func(mod, *cleanArgs, **kwargs)
        # apply any changes that happend to mod
        self.__set_self_from_struct(mod)
        return ret

    def clear(self):  # replaces the datatype's clear funciton, manually replacing self with a new instance of self type
        self_type = self.__get_self_type()
        self.__set_self_from_struct(self_type())

    def __get_self_type(self):
        return type(self.__as_local_copy(self))

    # this will be called when the client asks for a method belonging to the expected datatype. We look through that type for the desired method, if we arn't already providing one (e.g. we provide 'clear')
    def __getattr__(self, func_name, *args, **kwargs):
        func = None
        self_type = self.__get_self_type()
        for dtype in [self_type, EZDBClient]:
            if hasattr(dtype, func_name):
                func = getattr(dtype, func_name)

        mod = self.__get_self()

        return lambda *args, **kw: self.__function_closure(func, mod, *args, **kwargs)

    @staticmethod
    def __url_encode(line):
        return line.replace(' ', '%20')

    @staticmethod
    def __string_wrap(item):
        if type(item) in [str, unicode]:
            return '\'' + item + '\''
        else:
            return str(item)

    @staticmethod
    def __parse_response(line):
        data = json.loads(line)
        return (data['success'], data['data'])


class EZDBServer(Resource):
    theDB = {}

    def __init__(self, backup_filename='backup.save'):

        self.backup_filename = backup_filename
        if self.backup_filename and os.path.isfile(self.backup_filename):
            if not EZDBServer.theDB:  # keeping the static one Cached
                # if True:
                try:
                    self.__load_state()
                except Exception as e:
                    print(e, file=sys.stderr)
                    corrupt_backup_name = strftime(
                        "%Y%m%d-%H%M%S")+'_corrupt_'+self.backup_filename
                    print('start', corrupt_backup_name, file=sys.stderr)
                    os.rename(self.backup_filename, corrupt_backup_name)

    def __save_check(self, data):
        try:
            # test json serializable+deserializable
            json.loads(json.dumps(data))
            # test json pickleable and unpickleable
            pickle.loads(pickle.dumps(data))
            return True
        except:
            return False

    def __save_state(self, data):
        if self.__save_check(data):
            with open(self.backup_filename, 'w') as f:
                f.write(pickle.dumps(data))
        else:  # load up last working
            self.__load_state()

    def __load_state(self):
        with open(self.backup_filename, 'r') as f:
            lines = ''.join([x for x in f]).replace('\r\n', '\n')
            EZDBServer.theDB = pickle.loads(lines)
            # print("loaded db = " + str(EZDBServer.theDB), file=sys.stderr)

    @staticmethod
    def __prepare_lhs_eval_string(lhs_orig):
        lhs = lhs_orig.strip()
        lhs_covered = 'EZDBServer.theDB["'+lhs+'"]'.strip()
        ind = lhs.find('[')
        if ind > 0:
            lhs_covered = 'EZDBServer.theDB["'+lhs[:ind]+'"]'+lhs[ind:]
            lhs_covered = lhs_covered.replace('\\\'', '\'')
        return lhs_covered

    def get(self, get_msg_unicode):
        # print('>GetInDB>>' + str(EZDBServer.theDB), file=sys.stderr)
        get_msg = get_msg_unicode.encode("utf8", "ignore")
        # print('Got <',get_msg,'>', file=sys.stderr)
        if 'favicon.ico' in get_msg:
            return
        if get_msg == 'root':
            return {'success': True,
                    'data': EZDBServer.theDB}  # send the root
        split_msg = get_msg.split('=')
        # print('>lhfs>>' + str(split_msg[0]), file=sys.stderr)
        lhs = EZDBServer.__prepare_lhs_eval_string(split_msg[0])
        # print('>lhscovered>>' + str(lhs), file=sys.stderr)
        rhs = None
        if len(split_msg) > 1:
            rhs = split_msg[1]
        if rhs:
            act_string = lhs + '=' + rhs
            # print('!!!' + act_string, file=sys.stderr)
            exec(act_string)
        # print('<GetOutDB<<' + str(EZDBServer.theDB), file=sys.stderr)
        if self.backup_filename:
            self.__save_state(EZDBServer.theDB)
        try:
            return {'success': True,
                    'data': eval(lhs)}
        except Exception as e:
            print('\tError: ' + str(e), file=sys.stderr)
            return {'success': False,
                    'data': None}