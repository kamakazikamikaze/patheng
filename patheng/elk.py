from __future__ import print_function
from pyelasticsearch import ElasticSearch
import json
import os
import pickle
import requests
import time
from .utils import checkmakedir
import uuid


def make_index(url, indexname, mapping, debug=False):
    '''
    Check for and, if necessary, create an ElasticSearch index

    Keyword arguments:
    url -- Base URL of the ElasticSearch node/cluster
    indexname -- Name of the target ElasticSearch index
    mapping -- Index mapping structure
    '''
    check_exists = requests.get(url + indexname)
    #check_exists = request_session.get(url + indexname)
    if check_exists.status_code == 404:  # if the index doesn't exist MAKE IT...and set up the mapping as well!
        if debug:
            print("another day, another index.")
        r = requests.put(url + indexname, data=json.dumps(mapping))
        if debug:
            print("index creation:", r.json()['acknowledged'])
        del r


def checkservers(config, debug=False):
    '''
    Check if destination ElasticSearch clusters are online and prepare indices for data
    Allows for an optional error index

    Keyword arguments:
    config -- a dictionary of configuration arguments passed in at runtime
        Required key-value pairs:
        'send to' -- a dictionary of all target ES clusters
            key: cluster metadata name
            value: dictionary of arguments
                Required key-value pairs:
                'data index' -- ElasticSearch index the target data will be sent to
                '#' -- (string representation of an integer) member nodes of the cluster; at least 1 ('1') is required; 'address:port'
                'log errors to index': integer or boolean representing if any errors while reaching hosts should be sent to an error index
                Optional key-value pairs:
                '#' -- (string representation of an integer) additional member nodes to attempt sending data to, incremental
                'error index' -- if logging errors, this is the ElasticSearch index to file the data under
    '''
    sendto = []  # If we're sending to a primary and a mirror, just use a loop in the query function to iterate through each one
    offline = []
    timestamp = time.strftime("%Y.%m.%d")
    for name, cluster in config['nodes'].iteritems():
        try:  # Check which primary node to send to
            cluster['data index'] = cluster['data index'].split(
                str(time.strftime("%Y")))[0] + str(timestamp)
            if cluster['log errors to index']:
                cluster['error index'] = cluster['error index'].split(
                    str(time.strftime("%Y")))[0] + str(timestamp)
            cluster['name'] = name
            # Timestamp of when data was attempted to be sent to this cluster.
            # Used for (off)loading pickle dumps
            cluster['name_ts'] = name.split(str(time.strftime("%Y")))[
                0] + '_' + str(timestamp)
            cluster['alive'] = False
            i = 1  # i is to be cast as a string but incremented as an integer since we're using a Dict/JSON
            while not cluster['alive']:
                if not 'http://' in cluster[str(i)].encode():
                    if debug:
                        print('Cluster', name, 'was missing \'http://\'')
                    cluster[str(i)] = 'http://' + cluster[str(i)]
                if not cluster[str(i)][-1] == '/':
                    if debug:
                        print('Cluster', name, 'was missing \'/\'')
                    cluster[str(i)] += '/'
                try:
                    if requests.get(cluster[str(i)]).status_code == 200:
                        cluster['url'] = cluster[str(i)]
                        make_index(cluster['url'], cluster['data index'])
                        if cluster['log errors to index']:
                            make_index(cluster['url'], cluster['error index'])
                        cluster['alive'] = True
                        sendto.append(cluster)
                        if debug:
                            print(
                                '\nCluster', name, 'will send to', cluster[
                                    str(i)] + cluster['data index'])
                            if cluster['log errors to index']:
                                print(
                                    'Errors will be sent to', cluster[
                                        str(i)] + cluster['error index'])
                    else:
                        if debug:
                            if i == 1:
                                print('\n')
                            print('Cluster', name, 'master', i,
                                  'cannot be reached. Trying next...')
                        i += 1
                except:
                    if debug:
                        print('Cluster', name, 'master', i,
                              'cannot be reached. Trying next...')
                    i += 1

        except Exception as e:  # No nodes are reachable. We should query devices anyways, but how do we want to handle them in the next run?
            offline.append(cluster)
            if type(e).__name__ == "KeyError":
                if debug:
                    print(
                        '\nCluster',
                        name,
                        'has zero master nodes to send to! Skipping for now.')
            else:
                print(e)

    return sendto, offline


def bulkpush(sendto, offline, queue, errorqueue, debug=False):
    '''
    Send data in a bulk document to target ElasticSearch clusters
    If a cluster is unreachable, data will be offloaded to a temporary directory until it is back online

    Keyword arguments:
    sendto -- list of online clusters to send data to
    offline -- list of offline clusters to withhold data for
    queue -- multiprocessing queue of documents ready to be sent
    errorqueue -- multiprocessing queue of documents ready to be sent
    '''
    docs = []
    errordocs = []
    while not queue.empty():
        docs.append(queue.get())
    while not errorqueue.empty():
        errordocs.append(errorqueue.get())
    for cluster in sendto:
        # if debug:
        #	pprint(cluster)
        es = ElasticSearch(cluster['url'])
        if docs:
            r = es.bulk(
                (es.index_op(doc) for doc in docs),
                index=cluster['data index'],
                doc_type=cluster['data index type'])
        if errordocs:
            r = es.bulk(
                (es.index_op(doc) for doc in errordocs),
                index=cluster['error index'],
                doc_type=cluster['error index type'])
        if debug:  # TODO: add try except statment with imformative errors
            if r[
                    'errors'] == False:  # TODO: dump data to be sent next time the script is run
                print('\n\t', 'Bulk package was received by', cluster['name'])
            else:
                print(
                    '\n\t',
                    'Bulk package was not accepted by',
                    cluster['name'])
    if offline:
        _localoffload(
            offline=offline,
            docs=docs,
            errordocs=errordocs,
            debug=debug)


def _localoffload(offline, docs, errordocs=None, debug=False):
    """
    Setup the offloading of data into pickles.
    Prepares data to be pickled and generates a message on how to correctly modify target data, should a misconfiguration have occurred.

    Keyword arguments:
    offline -- dictionary of offline ES clusters
    docs -- ES documents to be sent to 'data index' for each cluster
    errordocs -- ES documents to be sent to 'error index'
    """
    basedir = './cfg/tmp/'
    checkmakedir(basedir)
    datadir = basedir + 'data/'
    checkmakedir(datadir)
    pickle = []
    err_pickle = []
    if docs:
        docid = str(uuid())
        _dumplist(docs, datadir + docid)
        pickle.append(docid)
    if errordocs:
        errid = str(uuid())
        _dumplist(errordocs, datadir + errid)
        err_pickle.append(errid)
    for cluster in offline:
        # makes a json for each
        clusterfile = basedir + cluster.pop('name_ts', 0) + '.json'
        cluster['pickle'] = pickle
        cluster['err_pickle'] = err_pickle
        if os.path.exists(clusterfile):
            f = open(clusterfile, mode='r+')
            old = json.load(f)
            cluster['pickle'] += old['pickle']
            cluster['err_pickle'] = old['err_pickle']
            f.seek(0)
        else:
            f = open(clusterfile, mode='w')
        cluster['instructions'] = "keep the name the same but change any of the incorrect information about the cluster if need. Ignore the pickle fields as they point to the data that will be sent. Do NOT touch pickle nor err_picke fields"
        cluster['path_to_data'] = datadir
        json.dump(cluster, f, indent=4, sort_keys=True)
        f.close()


def _dumplist(docs, file):
    """
    Pickle-dump documents in a list format to disk
    """
    try:
        if isinstance(docs, list) and docs:
            with open(file, 'w') as f:
                pickle.dump(docs, f)
    except Exception as e:
        print(e)
        pass


def loadlocal(debug=False):
    """
    Check for data offloaded to disk and retry sending if cluster(s) are now online
    """
    # TODO: have each cluster checked on a unqiue cluster basis instead of on a per json basis.
    # TODO: give user control of where data and tmp folder is stored
    basedir = './cfg/tmp/'
    datadir = basedir + 'data/'
    checkmakedir(basedir)
    checkmakedir(datadir)
    sendto = []
    dumpconfigs = [
        basedir +
        file for file in os.listdir(basedir) if file.endswith('.json')]
    if dumpconfigs:
        for configfile in dumpconfigs:
            try:
                cluster = {}
                with open(configfile, 'r') as f:
                    cluster = json.load(f)
                name = cluster['name']
                cluster['alive'] = False
                i = 1  # i is to be cast as a string but incremented as an integer since we're using a Dict/JSON
                while not cluster['alive']:
                    if not 'http://' in cluster[str(i)].encode():
                        if debug:
                            print('Cluster', name, 'was missing \'http://\'')
                        cluster[str(i)] = 'http://' + cluster[str(i)]
                    if not cluster[str(i)][-1] == '/':
                        if debug:
                            print('Cluster', name, 'was missing \'/\'')
                        cluster[str(i)] += '/'
                    try:
                        if requests.get(cluster[str(i)]).status_code == 200:
                            cluster['url'] = cluster[str(i)]
                            cluster['data index'] = make_index(
                                cluster['url'], cluster['data index'])
                            if cluster['log errors to index']:
                                make_index(
                                    cluster['url'], cluster['error index'])
                            cluster['alive'] = True
                            cluster['dumpconfigs'] = configfile
                            sendto.append(cluster)

                            if debug:
                                print(
                                    '\nDumped cluster', name, 'will send to', cluster[
                                        str(i)] + cluster['data index'])
                                if cluster['log errors to index']:
                                    print(
                                        'Errors will be sent to', cluster[
                                            str(i)] + cluster['error index'])
                        else:
                            if debug:
                                print('\nDumped cluster', name, 'master',
                                      i, 'cannot be reached. Trying next...')
                            i += 1
                    except Exception as e:
                        if debug:
                            print(e)
                            print('Dumped  cluster', name, 'master', i,
                                  'cannot be reached. Trying next...')
                        i += 1
            except Exception as e:
                if debug:
                    print(e)
                    print(
                        'Dumped cluster',
                        name,
                        'has zero master nodes to send to! Skipping for now.')
        for cluster in sendto:
            try:
                es = ElasticSearch(cluster['url'])
                for pickleid in cluster['pickle']:
                    with open(datadir + pickleid, 'rb') as f:
                        docpile = pickle.load(f)
                    r = es.bulk(
                        (es.index_op(doc) for doc in docpile),
                        index=cluster['data index'],
                        doc_type=cluster['data index type'])
                for errpickleid in cluster['err_pickle']:
                    with open(datadir + errpickleid, 'rb') as f:
                        errdocpile = pickle.load(f)
                    r = es.bulk(
                        (es.index_op(doc) for doc in errdocpile),
                        index=cluster['error index'],
                        doc_type=cluster['error index type'])
                    if debug:
                        if r['errors']:
                            print(r['errors'])
                            raise Exception
                os.remove(cluster['dumpconfigs'])
            except Exception as e:
                print(e)
                print("thought the cluster was up but it really isn't")
        _cleanupdump(debug)


def _cleanupdump(debug=False):
    """
    Clean up remaining files from pickle directory that no longer serve a purpose
    """
    basedir = './cfg/tmp/'
    datadir = basedir + 'data/'
    leftoverdumpconfigs = [
        basedir +
        file for file in os.listdir(basedir) if file.endswith('.json')]
    allpickleddocs = os.listdir(datadir)
    pickledocsneeded = []
    for configfile in leftoverdumpconfigs:
        try:
            with open(configfile, 'r') as f:
                cluster = json.load(f)
            pickledocsneeded += cluster['pickle']
            pickledocsneeded += cluster['err_pickle']
        except:
            pass
    pickledocstodel = list(set(allpickleddocs) - set(pickledocsneeded))
    for pickledoc in pickledocstodel:
        os.remove(datadir + pickledoc)
