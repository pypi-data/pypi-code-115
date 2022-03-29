# 2022.3.29 cp from dsk-to-essaydm python dsk-to-essaydm.py dsk-to-essaydm --debug true --eshost 172.18.0.1
import json, fire

def get_eid_ver(es, eid, index): # only final version data kept 
	try:
		res = es.get(index=index, id=eid) # doc_type=self.index_type,
		return int(res['hits']['hits']['_source'].get('ver',0))
	except Exception as ex:
		return 0

def index_dsk_actions(eid, rid, uid,final_score, snts, docs, dims, mkfs, index) : 
	''' NOT check eid duplicated '''
	actions=[]
	dims.update({'type':'doc', 'eid': eid, 'rid': rid , 'uid': uid, 'ver':ver, 'final_score':final_score}) #dims = dsk.get("doc", {})
	actions.append({'_op_type':'index', '_index':index, '_id': eid, '_source':dims})

	for idx, snt, doc in enumerate(zip(snts,docs)) : 
		sntlen = len(doc)
		if not sntlen : continue
		actions.append({'_op_type':'index', '_index':index,  '_id': f"{eid}-{idx}",  '_source': {'snt':doc.text, "eid":eid, 'rid': rid , 'uid': uid, 'tc':sntlen, 'awl': sum([ len(t.text) for t in doc])/sntlen ,  'type':'snt',	'postag':' '.join(['^'] + [f"{t.text}_{t.lemma_}_{t.tag_}_{t.pos_}" for t in doc] + ['$']) }})
		[actions.append({'_op_type':'index', '_index':index, '_id': f"{eid}-{idx}:trp-{t.i}",  '_source': {"eid":eid, 'rid': rid , 'uid': uid,'type':'trp', 'src': f"{eid}-{idx}", 'gov': t.head.lemma_, 'rel': f"{t.dep_}_{t.head.pos_}_{t.pos_}", 'dep': t.lemma_ }}) for t in doc if t.dep_ not in ('punct')]
		[actions.append({'_op_type':'index', '_index':index, '_id': f"{eid}-{idx}:tok-{t.i}",  '_source': {"eid":eid, 'rid': rid , 'uid': uid,'type':'tok', 'src': f"{eid}-{idx}", 'lex': t.text, 'low': t.text.lower(), 'lem': t.lemma_, 'pos': t.pos_, 'tag': t.tag_, 'i':t.i, 'head': t.head.i }}) for t in doc]
		[actions.append({'_op_type':'index', '_index':index, '_id': f"{eid}-{idx}:np-{np.start}",  '_source': {"eid":eid, 'rid': rid , 'uid': uid,'type':'np', 'src': f"{eid}-{idx}", 'lem': doc[np.end-1].lemma_, 'chunk': np.text, }}) for np in doc.noun_chunks]
	
		for mkf in mkfs: #dsk['snt']
			for kp, v in mkf['feedback'].items():
				actions.append({'_op_type':'index', '_index':index,  '_id': f"{eid}-{idx}:kp-{v['ibeg']}",  '_source': {"eid":eid, 'rid': rid , 'uid': uid, 'type':'feedback',
				'src': f"{eid}-{idx}",  'kp':v['kp'], 'cate': v['cate']} })
	return actions 

from collections import defaultdict 
def eids (topk=1000):
	''' '''
	eidver = defaultdict(int)
	for eidv in redis.dsk.zrevrange("eids",0, topk): #154762930-2
		arr = eidv.split("-")
		if len(arr) == 2 and eidver[arr[0]] < int(arr[1]) :  
			eidver[arr[0]] = int(arr[1]) 
	return eidver

def run(eshost, esport=9200, idxname='essaydm',rhost = '127.0.0.1', rport=3362, topk=1000, ): 
	''' import 3362 data to es:essaydm '''
	import redis 
	from elasticsearch import Elasticsearch,helpers
	fire.es		= Elasticsearch([ f"http://{eshost}:{esport}" ]) 
	fire.index  = idxname
	redis.dsk	= redis.Redis(host=rhost, port=rport, db=0, decode_responses=True)
	redis.mkf	= redis.Redis(host=rhost, port=rport, db=1, decode_responses=True)
	redis.bs	= redis.Redis(host=rhost, port=rport, db=2, decode_responses=False)
	print (eshost, fire.es, redis.dsk , flush=True)

	es_eids = set([ doc['_id'] for doc in helpers.scan(fire.es,query={"query": {"match": {"type":"doc"}}}, index=idxname)])
	print ("count of eids in ES", len(es_eids))

	actions = []
	for eid,ver in eids(topk): 
		if eid in es_eids: continue

		res = redis.dsk.hgetall( f"{eid}-{ver}") # dsk/pids/snts 
		dsk = json.loads(res['dsk'])
		dims = dsk['doc']
		snts = json.loads(res['snts'])
		docs = [spacy.redisdoc(snt, redis.bs) for snt in snts ]
		actions.extend(index_dsk_actions(eid, rid, uid,final_score, snts, docs, dims, mkfs, idxname))

if __name__ == '__main__': 
	fire.Fire(run) 