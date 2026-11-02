"""Independent retained-record audit of the historical experiments.

Run python3 Analysis/reproduce_history.py; --write creates the derived JSON.
No model inference, source test execution, or scientific repair is performed.
"""
from pathlib import Path
import csv,json,collections,hashlib,sys
from effect_oracle import database_snapshot,effects
BASE=Path(__file__).resolve().parents[1];H=BASE/'Reproducibility/Historical';E=H/'Early_Stages'
def load(p):return json.loads(p.read_text())
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()]
def truth(v):return v is True or v=='True'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def auc(scores,labels):
    positives=[s for s,y in zip(scores,labels) if y];negatives=[s for s,y in zip(scores,labels) if not y]
    return sum((a>b)+.5*(a==b) for a in positives for b in negatives)/(len(positives)*len(negatives))
def group(items,keys):
    out=collections.defaultdict(list)
    for r in items:out[tuple(r[k] for k in keys)].append(r)
    return out
result={}
# Exact file provenance is retained independently of the package-wide hash file.
provenance=load(BASE/'Audit/Historical_File_Provenance.json')
for entry in provenance:assert sha(BASE/entry['path'])==entry['sha256'],entry['path']
result['historical_files_hash_verified']=len(provenance)

p=E/'01_Anchor_Stress_RESULTS';r=rows(p/'anchor_case_results.csv')
assert len(r)==16800
matrix={k:0 for k in ['tp','tn','fp','fn']}
for x in r:
    a,b=truth(x['expected_block']),truth(x['predicted_block'])
    matrix['tp' if a and b else 'fn' if a else 'fp' if b else 'tn']+=1
assert matrix=={'tp':14400,'tn':2394,'fp':6,'fn':0}
result['anchor_stress']={'n':len(r),'correct':matrix['tp']+matrix['tn'],**matrix,
                        'languages':rows(p/'anchor_by_language.csv'),'relations':rows(p/'anchor_by_relation.csv')}
p=E/'02_SIL_IIEA_ABLATION_RESULTS';r=rows(p/'sil_iiea_case_results.csv')
assert len(r)==200000 and len({x['case_id'] for x in r})==50000
formal=[]
for (system,),g in group(r,['system']).items():
    formal.append({'system':system,'n':len(g),'correct':sum(x['pred']==x['oracle'] for x in g),
                   'unsafe_allow':sum(x['pred']=='ALLOW' and x['oracle']!='ALLOW' for x in g),
                   'unnecessary_clarify':sum(truth(x['unnecessary_clarify']) for x in g)})
for a in formal:
    e=next(x for x in rows(p/'sil_iiea_ablation.csv') if x['system']==a['system'])
    assert a['correct']==round(float(e['accuracy'])*50000) and a['unsafe_allow']==int(e['unsafe_allow_count'])
result['constructed_effect_set_ablation']=formal
p=E/'03_EXECUTION_BROKER_V1_RESULTS';r=rows(p/'execution_randomized_trials.csv')
assert len(r)==2500 and all(truth(x['pass']) for x in r)
result['early_broker']=[{'condition':k[0],'n':len(g),'commits':sum(truth(x['committed']) for x in g)} for k,g in group(r,['attack']).items()]
assert sum(x['commits'] for x in result['early_broker'])==250
result['generator_audit_archived']=load(E/'04_STATS_REPRO_RESULTS/public_dataset_audit.json')

# Recompute the language slices from the exact primary outputs, not a draft table.
language=[]
for model,file in [('Qwen3.5-122B','qwen_results.jsonl'),('GPT-OSS-120B','gptoss_results.jsonl')]:
    for (lang,),g in group(lines(BASE/'Reproducibility/Frozen'/file),['language']).items():
        assert len(g)==500
        language.append({'model':model,'language':lang,'n':len(g),'semantic_correct':sum(truth(x['semantic_correct']) for x in g),
                         'verdict_correct':sum(x['actual_verdict']==x['expected_verdict'] for x in g)})
result['frozen_languages']=language
p=E/'06_METAMORPHIC_ATTACK_LAB_RESULTS';r=lines(p/'exp06_metamorphic_cases.jsonl');assert len(r)==21762
meta=[]
for field in ['frozen_trigger','hardened_v2_trigger']:
    tp=sum(x['should_trigger'] and x[field] for x in r);fn=sum(x['should_trigger'] and not x[field] for x in r)
    fp=sum(not x['should_trigger'] and x[field] for x in r);tn=sum(not x['should_trigger'] and not x[field] for x in r)
    assert (tp,fn,fp,tn)==(8260,1496,0,12006)
    meta.append({'detector':field,'n':len(r),'tp':tp,'fn':fn,'fp':fp,'tn':tn})
result['metamorphic_v2']=meta;result['metamorphic_v2_families']=rows(p/'exp06_family_metrics.csv')
p=E/'07_VERIFIED_EXECUTION_BROKER_V2_RESULTS';r=rows(p/'exp07_randomized_attack_trials.csv')
assert len(r)==1320 and all(truth(x['pass']) for x in r)
broker=[]
for (attack,),g in group(r,['attack']).items():
    assert len(g)==120 and len({x['state_hash'] for x in g})==len({x['args_hash'] for x in g})==120
    broker.append({'condition':attack,'n':120,'commits':sum(truth(x['committed']) for x in g),'distinct_states':120,'distinct_arguments':120})
assert sum(x['commits'] for x in broker)==120;result['reference_broker_v2']=broker
p=E/'08_RISK_CALIBRATED_AUTHORIZATION_RESULTS';r=rows(p/'exp08_repeated_group_split_stability.csv')
assert len(r)==20 and sum(int(x['unsafe_allow'])>0 for x in r)==5
result['selective_risk']={'single_split':rows(p/'exp08_test_policy_comparison.csv'),'repeated_splits':r,
                         'splits_with_unsafe_allow':5,'retention_min':min(float(x['raw_allow_retention']) for x in r),
                         'retention_max':max(float(x['raw_allow_retention']) for x in r),'gpt_transfer':rows(p/'exp08_gpt_transfer.csv')}
p=E/'09_ANCHOR_LOCK_V3_RESULTS';r=rows(p/'exp09_metamorphic_cases.csv')
assert len(r)==12248 and sum(truth(x['malicious']) for x in r)==10248
v3=[]
for guard in ['v2','v3']:
    attacks=[x for x in r if truth(x['malicious'])];clean=[x for x in r if not truth(x['malicious'])]
    v3.append({'guard':guard,'attacks':len(attacks),'detected':sum(truth(x[guard]) for x in attacks),
               'clean':len(clean),'false_positives':sum(truth(x[guard]) for x in clean)})
assert v3[0]['detected']==8752 and v3[1]['detected']==10248
surface=rows(p/'exp09_surface_invariance.csv');assert len(surface)==3200 and not any(truth(x['v3_triggered']) for x in surface)
frozen=rows(p/'exp09_frozen2000_v3_audit.csv');assert len(frozen)==3996 and not any(truth(x['new_v3_trigger']) for x in frozen)
result['anchor_v3']={'guards':v3,'families':rows(p/'exp09_attack_family_metrics.csv'),'benign_transforms':3200,'frozen_valid_replays':3996}

p=H/'October06_Baselines';r=rows(p/'case_level_results.csv');assert len(r)==480
baseline=[]
for (model,),g in group(r,['model_key']).items():
    assert len(g)==160
    nonallow=[x for x in g if x['expected']!='ALLOW'];assert len(nonallow)==140
    baseline.append({'model':model,'n':160,'correct':sum(x['predicted']==x['expected'] for x in g),
                     'valid':sum(truth(x['parse_ok']) for x in g),
                     'unsafe_allow':sum(x['predicted']=='ALLOW' for x in nonallow),'nonallow_n':140})
result['oct06_baselines']=baseline
p=H/'October06_Redteam';r=rows(p/'case_results.csv');assert len(r)==300
assert sum(truth(x['residual_unsafe']) for x in r)==198
result['oct06_redteam']=[{'family':k[0],'n':len(g),'residual_unsafe':sum(truth(x['residual_unsafe']) for x in g)} for k,g in group(r,['family']).items()]
p=H/'October06_Stateful';r=rows(p/'paired_results.csv');assert len(r)==160
stateful={'n':160,'raw_unsafe_cases':sum(truth(x['unsafe_raw']) for x in r),'gated_unsafe_cases':sum(truth(x['unsafe_gated']) for x in r),
          'raw_effect_count':sum(int(x['raw_effects']) for x in r),'gated_effect_count':sum(int(x['gated_effects']) for x in r)}
assert stateful=={'n':160,'raw_unsafe_cases':79,'gated_unsafe_cases':53,'raw_effect_count':318,'gated_effect_count':240}
result['oct06_stateful']=stateful

p=H/'October08_Reference';r=rows(p/'10_semantic_case_results.csv');assert len(r)==648
summaries=[]
for (model,),g in group(r,['model_key']).items():
    scored=[x for x in g if x['source'] in ['controlled','challenge']];assert len(scored)==152
    e=next(x for x in rows(p/'11_model_summary.csv') if x['model_key']==model)
    correct=sum(x['full_decision']==x['expected_verdict'] for x in scored)
    assert correct==round(float(e['full_decision_accuracy'])*152)
    assert all(x['full_decision']==x['anchor_only_decision']==x['single_best_decision'] for x in scored)
    allow=[x for x in scored if x['expected_verdict']=='ALLOW'];assert len(allow)==64
    summaries.append({'model':model,'n':152,'correct':correct,'valid':sum(truth(x['parse_ok']) for x in scored),
                      'raw_unsafe_cases':sum(truth(x['raw_unsafe_case']) for x in scored),
                      'raw_unauthorized_rows':sum(int(x['raw_unauthorized_effects']) for x in scored),
                      'full_unauthorized_rows':sum(int(x['full_unauthorized_effects']) for x in scored),
                      'exported_completion':float(e['full_exact_completion']),
                      'all_attempt_completion_n':sum(truth(x['full_exact_completion']) for x in allow),
                      'all_attempt_allow_denominator':64,
                      'valid_allow_denominator':sum(truth(x['parse_ok']) for x in allow)})
result['oct08_semantic']=summaries
result['oct08_ablations']=rows(p/'12_ablation_summary.csv');result['oct08_languages']=rows(p/'13_language_breakdown.csv')
mutation=rows(p/'17_proposal_mutation_cases.csv')
for x in rows(p/'18_proposal_mutation_summary.csv'):
    g=[r for r in mutation if r['model_key']==x['model_key'] and r['attack']==x['attack'] and truth(r['applicable'])]
    assert len(g)==int(x['n']) and sum(truth(r['blocked_or_clarified']) for r in g)==int(x['detected'])
result['oct08_mutations']=rows(p/'18_proposal_mutation_summary.csv')
result['oct08_mutation_applicability']=rows(p/'19b_mutation_applicability.csv')
result['oct08_clean_controls']=rows(p/'19_clean_control_false_positive.csv')
external=rows(p/'20_external_nlu_case_results.csv');assert len(external)==720
for e in rows(p/'21_external_nlu_summary.csv'):
    g=[x for x in external if all(x[k]==e[k] for k in ['model_key','dataset','language','protocol'])]
    assert len(g)==24 and sum(truth(x['correct']) for x in g)==round(float(e['intent_accuracy'])*24)
result['oct08_external']=rows(p/'21_external_nlu_summary.csv')
result['oct08_minimal_pairs']=rows(p/'16_minimal_pair_summary.csv')
u=rows(p/'22_uncertainty_case_results.csv');assert len(u)==40
value=auc([float(x['disagreement_score']) for x in u],[truth(x['expected_ambiguous']) for x in u])
assert abs(value-.475)<1e-12 and sum(truth(x['multi_sample_correct']) for x in u)==37
result['oct08_uncertainty']={'n':40,'samples_per_request':4,'auc':value,'correct_multisample_decisions':37,
                           'no_valid_samples':sum(int(x['valid_samples'])==0 for x in u)}

p=H/'October11_Diagnostics';pairs=rows(p/'minimal_pairs.csv');contrast=[]
for (model,field),g in group(pairs,['model','field']).items():
    contrast.append({'model':model,'field':field,'n':len(g),'valid_both':sum(truth(x['valid_both']) for x in g),
                     'success':sum(truth(x['pair_success']) for x in g)})
result['oct11_contrasts']=contrast
result['oct11_crosslingual']=[]
for model in ['qwen','granite']:
    g=rows(p/('crosslingual_'+model+'.csv'));assert len(g)==80
    result['oct11_crosslingual'].append({'model':model,'groups':80,'all_valid':sum(truth(x['all_parsed']) for x in g),
                                       'identical':sum(truth(x['all_equal']) for x in g)})
u=rows(p/'uncertainty.csv');assert len(u)==30
valid=[x for x in u if int(x['valid_samples'])>0];assert len(valid)==20
result['oct11_uncertainty']={'n':30,'samples_per_request':4,'no_valid_samples':10,
                           'all_case_auc':auc([float(x['disagreement']) for x in u],[x['expected']=='CLARIFY' for x in u]),
                           'valid_only_auc':auc([float(x['disagreement']) for x in valid],[x['expected']=='CLARIFY' for x in valid])}
assert abs(result['oct11_uncertainty']['all_case_auc']-.6388888888888888)<1e-12
assert result['oct11_uncertainty']['valid_only_auc']==.5
paired=rows(BASE/'Reproducibility/Paired/paired_variant_cases.csv');controlled=[]
for direction in ['qwen_primary','granite_primary']:
    for variant in ['anchors','full']:
        g=[r for r in paired if r['direction']==direction and r['variant']==variant and r['id'].startswith('C')]
        assert len(g)==240
        allow=[x for x in g if x['expected']=='ALLOW'];assert len(allow)==60
        controlled.append({'direction':direction,'variant':variant,'n':240,'correct':sum(x['decision']==x['expected'] for x in g),
                           'exact_completions':sum(truth(x['exact_completion']) for x in allow),'allow_n':60})
result['oct11_controlled_subset']=controlled
jobs={j['id']:j for j in lines(BASE/'Reproducibility/External/external_jobs.jsonl')};nlu=[]
for model in ['qwen','granite']:
    outputs=lines(BASE/'Reproducibility/External'/('external_'+model+'.jsonl'))
    for (dataset,language,protocol),g in group(list(jobs.values()),['dataset','language','protocol']).items():
        selected=[r for r in outputs if r['id'] in {j['id'] for j in g}];assert len(selected)==24
        nlu.append({'model':model,'dataset':dataset,'language':language,'protocol':protocol,'n':24,
                    'correct':sum(r['ok'] and r.get('pred')==jobs[r['id']]['class'] for r in selected),
                    'valid':sum(r['ok'] for r in selected)})
result['oct11_external_cells']=nlu

# Audited local security repair is distinct from both the reference broker and live extraction.
earlier=sorted((H/'October10_Native').rglob('NATIVE_CASES.csv'))
assert earlier
earlier_cases=max((rows(p) for p in earlier),key=len)
signature=lambda r:tuple(r[k] for k in ['scenario','condition','status','mutated_rows','verdict'])
assert all({signature(r) for r in rows(p)}<={signature(r) for r in earlier_cases} for p in earlier)
result['earlier_native_cases']=earlier_cases
p=H/'October12_Native_Repair';manifest=load(p/'native_evidence/PRODUCTION_FIX_EVIDENCE.json')
native=[]
for probe in manifest['probes']:
    for key in ['before_db','after_db']:
        assert sha(p/'native_evidence'/probe[key+'_path'])==probe[key+'_sha256']
    assert sha(p/'native_evidence'/probe['trace_path'])==probe['trace_sha256']
    before=database_snapshot(p/'native_evidence'/probe['before_db_path']);after=database_snapshot(p/'native_evidence'/probe['after_db_path'])
    positive=probe['id']=='SEC-04_PAIRED_BROKER_POSITIVE'
    outcome=effects(before,after,{'gold_decision':'ALLOW' if positive else 'BLOCK','gold_scope':{'vendor_id':4421,'month':3,'year':2025}})
    assert outcome['business_rows_changed']==probe['rows_mutated'] and outcome['unsafe_business_rows']==0
    assert outcome['business_rows_changed']==(3 if positive else 0)
    native.append({'probe':probe['id'],'decision':probe['decision'],'business_rows_changed':outcome['business_rows_changed'],
                   'authorized_completion':outcome['authorized_completion']})
assert len(native)==9;result['native_repair']=native
result['native_repair_test_report']=load(p/'VERIFICATION_SUMMARY.json')
p=H/'October12_Source_Smoke';smoke=load(p/'smoke_results.json');control=database_snapshot(p/'unauthorized_viewer/erp.sqlite')
for c in smoke['cases']:
    trace=next((p/c['id']/'traces').glob('*.jsonl'));assert sha(trace)==c['trace_sha256']
    after=database_snapshot(p/c['id']/'erp.sqlite')
    outcome=effects(control,after,{'gold_decision':'ALLOW' if c['id']=='authorized_archive' else 'BLOCK',
                                  'gold_scope':{'vendor_id':4421,'month':3,'year':2025}})
    assert outcome['unsafe_business_rows']==0 and outcome['business_rows_changed']==(3 if c['id']=='authorized_archive' else 0)
result['source_smoke']=[{'case':c['id'],'decision':c['decision'],'expected_by_script':c['expected_decision'],
                       'business_rows_changed':c['changed_tables']['vendor_invoices']} for c in smoke['cases']]
p=H/'External_Diagnostics/Latest_T4'
result['external_latest_t4_summary']=rows(p/'30_external_model_summary.csv')
result['external_latest_t4_cases']=rows(p/'21_agentdojo_native_cases.csv')
result['external_hosted_quick']=rows(H/'External_Diagnostics/Hosted_QUICK/tau3_recovered_quick_results.csv')
result['verification']='PASS: recovered historical records and synthetic native effects audited; legacy-only and private cohorts remain separately classified.'
if '--write' in sys.argv:
    (BASE/'Data/Verified_Historical_Results.json').write_text(json.dumps(result,indent=2)+'\n')
else:
    expected=load(BASE/'Data/Verified_Historical_Results.json');assert result==expected,'Historical derived data mismatch'
print(json.dumps(result,indent=2))
