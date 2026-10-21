"""Collect bounded native price paths for research; never execute trades."""
import argparse
import json
import subprocess
import time
from pathlib import Path
from dlmm_shadow import index_candidate, iter_rows, append
from dlmm_candidate_watch import WATCH_FILENAME
from dlmm_net_experiment import write


def collect(profile, state_dir):
    now = time.time()
    candidates = {}
    for file in (profile/'memories'/WATCH_FILENAME,
                 state_dir/'solana_candidate_watch.jsonl', state_dir/'solana_rejects.jsonl'):
        for row in iter_rows(file):
            index_candidate(candidates, row, now)
    state_file = state_dir/'price-path-last-attempt.json'
    previous = json.loads(state_file.read_text()) if state_file.exists() else {}
    selected = sorted(candidates.values(), key=lambda c:(previous.get(c['pool'],0),-c['source_ts'],c['pool']))[:30]
    if not selected:
        summary = dict(status='no_recent_candidates', candidates=0, checked_at=now)
        write(state_dir/'price-path-summary.json',summary)
        return summary
    executor = profile/'skills/solana-dlmm/scripts/dlmm_executor.js'
    try:
        output = subprocess.check_output(['node',str(executor),'candidate-price-path',
            json.dumps([dict(pool=c['pool'],base_mint=c['base_mint']) for c in selected])],
            stderr=subprocess.DEVNULL, timeout=25)
        result = json.loads(output)
    except (subprocess.SubprocessError, ValueError):
        result = dict(status='unmeasured',reason='native_batch_unavailable',observations=[])
    if result.get('status') != 'deferred':
        for c in selected:
            previous[c['pool']] = now
        write(state_file,{p:t for p,t in previous.items() if p in candidates})
    identities = {c['pool']:c for c in selected}
    for row in result.get('observations',[]):
        c = identities.get(row.get('pool'))
        if not c or row.get('base_mint') != c['base_mint']:
            raise ValueError('Unexpected batch identity')
        append(profile/'memories/dlmm_candidate_price_paths.jsonl',
               dict(row,source_ts=c['source_ts'],mode=c['mode'],collected_at=time.time()))
    summary = dict(status=result['status'],reason=result.get('reason'),candidates=len(candidates),
                   requested=len(selected),observed=sum(r.get('status')=='observed' for r in result.get('observations',[])),
                   checked_at=time.time(),basis='research_price_path_not_net_profit')
    write(state_dir/'price-path-summary.json',summary)
    return summary


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--state-dir',type=Path,default=Path.home()/'.local/state/azimuth')
    a=p.parse_args()
    print(json.dumps(collect(a.profile,a.state_dir)))
