# Recomputes v1.1 TEST partition hashes from public rule + label-free TV-001 view only.
# Never opens sealed/*, partitions/*, exclusions or label files.
import json,hashlib,sys
import polars as pl
from seqlogad.evaluation.split import _canonical_bytes,_iter_canonical_object_chunks,PROTOCOL_ID,PROTOCOL_VERSION,SPLIT_CONTRACT_ID,SPLIT_CONTRACT_VERSION
from seqlogad.ingestion.raw_metadata import build_hdfs_component_id
from seqlogad.evaluation.test_seal import sha256_canonical
def phash(man,recs):
    fixed={"dataset_fingerprint":man['fp'],"protocol":{"id":PROTOCOL_ID,"version":PROTOCOL_VERSION},"split_contract":{"id":SPLIT_CONTRACT_ID,"version":SPLIT_CONTRACT_VERSION},"split_payload_hash":man['sp'],"partition_name":"TEST"}
    mem=(_canonical_bytes({"structural_unit_id":a,"chronological_start":b,"chronological_end_exclusive":c}) for a,b,c in recs)
    d=hashlib.sha256()
    for ch in _iter_canonical_object_chunks(fixed,{"ordered_structural_membership":mem}): d.update(ch)
    return d.hexdigest()
def man(ds):
    m=json.load(open(f'data/processed/splits/{ds}/split-manifest.json'))
    s=json.load(open(f'data/processed/splits/{ds}/test-seal.json'))['binding']
    return {'fp':s['dataset_fingerprint'],'sp':s['split_payload_hash'],'test':s['test_partition_hash'],'src':m['dataset_semantics']['source_id']}
# HDFS
M=man('hdfs');cut=10058066
base='data/processed/target-views/TV-001/FOLD-TARGET-ARCH-HDFS/evaluation/'
e=pl.read_parquet(base+'events.parquet',columns=['rank','group']).filter(pl.col('rank')>=cut-5_000_000)
g=e.group_by('group').agg(pl.col('rank').min().alias('f'),pl.col('rank').max().alias('l'),pl.len().alias('n'))
a=g.filter(pl.col('f')>=cut)
print('hdfs after blocks',a.height,'lines',a['n'].sum())
from seqlogad.ingestion.raw_metadata import _hdfs_tokens
import itertools
rank2g=dict(zip(*e.filter(pl.col('rank')>=cut).select('rank','group').get_columns()))
keep=set(a['group'].to_list()); blocks={}
with open('data/raw/hdfs/HDFS_v1/HDFS.log','rb') as fh:
    for r,line in enumerate(itertools.islice(fh,cut,None),start=cut):
        g=rank2g.get(r)
        if g in keep:
            blocks.setdefault(g,set()).update(_hdfs_tokens(line.decode('utf-8','replace')).normalized)
print('multi-block groups',sum(len(v)>1 for v in blocks.values()))
fl={g:(f,l) for g,f,l in a.select('group','f','l').iter_rows()}
recs=sorted(((build_hdfs_component_id(tuple(blocks[g])),)+(fl[g][0],fl[g][1]+1) for g in keep),key=lambda r:(r[1],r[0]))
h=phash(M,recs);print('hdfs recomputed',h,'expected',M['test'],'MATCH' if h==M['test'] else 'NO MATCH')
h2=phash(M,recs[:-1]);print('neg control drop last',h2==M['test'])
# BGL
M=man('bgl');st,en=4273166,4747963
n=(en-st)//100
def bid(s,e): return "BGL-PARENT-"+sha256_canonical({"source_id":M['src'],"partition":"TEST","raw_rank_start_inclusive":s,"raw_rank_end_exclusive":e})
recs=[(bid(st+i*100,st+i*100+100),st+i*100,st+i*100+100) for i in range(n)]
h=phash(M,recs);print('bgl n',n,'recomputed',h,'expected',M['test'],'MATCH' if h==M['test'] else 'NO MATCH')
