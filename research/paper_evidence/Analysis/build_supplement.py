"""Build the supplementary LaTeX from audited result records and a coverage map."""
from pathlib import Path
import json,csv,re
B=Path(__file__).resolve().parents[1]
D=json.loads((B/'Data/Verified_Historical_Results.json').read_text())
P=json.loads((B/'Data/Verified_Paper_Results.json').read_text())
O=B/'Supplementary';O.mkdir(exist_ok=True)
def esc(x):
    s=str(x)
    return ''.join({'&':r'\&','%':r'\%','_':r'\_','#':r'\#','$':r'\$','{':r'\{','}':r'\}','\\':r'\textbackslash{}'}.get(c,c) for c in s)
def pct(v):return f'{100*float(v):.2f}%'
def short(v):return {'qwen25_3b':'Qwen2.5-3B','granite33_2b':'Granite-3.3-2B','smollm2_17b':'SmolLM2-1.7B',
                             'qwen_primary':'Qwen primary','granite_primary':'Granite primary','qwen':'Qwen','granite':'Granite'}.get(v,v.replace('_',' '))
parts=[]
def para(s):
    # Narrative strings contain LaTeX commands; escape only bare percent signs.
    s=re.sub(r'(?<!\\)%', r'\\%', s)
    parts.append(s+'\n\n')
def section(n,title):para(r'\section*{S'+str(n)+'. '+title+'}')
def table(caption,headers,records,widths=None):
    n=len(headers)
    if widths is None:widths=([.25]+[.65/(n-1)]*(n-1)) if n>1 else [.9]
    spec='@{}'+''.join(r'>{\raggedright\arraybackslash}p{'+str(w)+r'\textwidth}' for w in widths)+'@{}'
    head=' & '.join(r'\textbf{'+esc(x)+'}' for x in headers)+r' \\'
    if len(records)<=12:
        para(r'\begin{minipage}{\textwidth}\centering\small\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.12}'+'\n'+
             r'\captionof{table}{'+esc(caption)+'}\n'+r'\begin{tabular}{'+spec+'}\n'+r'\toprule'+'\n'+head+'\n'+r'\midrule'+'\n'+
             '\n'.join(' & '.join(esc(c) for c in row)+r' \\' for row in records)+'\n'+r'\bottomrule\end{tabular}\end{minipage}')
        return
    para(r'{\small\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.12}'+'\n'+r'\begin{longtable}{'+spec+'}\n'+
         r'\caption{'+esc(caption)+r'}\\'+'\n'+r'\toprule'+'\n'+head+'\n'+r'\midrule\endfirsthead'+'\n'+
         r'\multicolumn{'+str(n)+r'}{l}{\small\itshape Table \thetable\ continued}\\'+'\n'+r'\toprule'+'\n'+head+'\n'+
         r'\midrule\endhead\midrule\multicolumn{'+str(n)+r'}{r}{\small Continued on next page}\\\endfoot\bottomrule\endlastfoot'+'\n'+
         '\n'.join(' & '.join(esc(c) for c in row)+(r' \\*' if len(records)-3<=i<len(records)-1 else r' \\') for i,row in enumerate(records))+'\n'+r'\end{longtable}}')
def source(relative):para(r'\noindent\textit{Record:} \path{Reproducibility/Historical/'+relative+'}.')

inventory=[
('A01','Early anchor stress','16,800 constructed cases','S3; retained raw CSVs','Predicate agreement, not live model accuracy.'),
('A02','SIL/IIEA construction','50,000 effect-set cases; four methods','S3; retained raw CSVs','Shared symbolic oracle; no language-model inference.'),
('A03','First execution broker','2,500 repeated fixture trials','S3; raw trial CSV','Repeated conditions; not 2,500 independent states.'),
('A04','Statistics and generator audit','Same 2,000 outputs; archived 10,000-row corpus audit','S2/S3; audit JSON','Not a fresh model study; archived corpus audit not re-executed.'),
('A05','Frozen runtime ablation','2,000/model, 500 groups','Article; S2','Same stored outputs across four stages; Qwen cache reuse disclosed.'),
('A06','Metamorphic lab','21,762 mutations/controls per detector','S4; raw JSONL','Includes 9,756 attacks; shares generated source groups.'),
('A07','Transaction-first reference broker','1,320 scenarios','Article; S4','120 distinct states/arguments per condition; reference implementation.'),
('A08','Risk-selective authorization','600 held-out cases/split; 20 splits','Article; S5','Repeated splits overlap; five retain unsafe verdicts.'),
('A09','Anchor Lock V3','10,248 attacks + 2,000 controls','Article; S4','Post-freeze hardening; 3,996 valid output replays and 3,200 benign transforms.'),
('A10','BFCL/MLCL external stage','Attempts and empty score files','S12; status records','No official authorization score.'),
('A11','AgentDojo/Agent-SafetyBench stage','Attempt/inventory records','S12; status records','File availability and failed CLI execution are not model outcomes.'),
('A12','Stateful external stage','Attempted trajectories','S12; status records','Context/API/runner failures remain unscored.'),
('A13','Unified benchmark matrix','Aggregates of available stages','S12; source matrix','Missing inputs and duplicate summaries are not new experiments.'),
('AX','Wave-3 master exports','Repeated stage and status exports','Archive provenance','Re-export of earlier cohorts; not an independent replication.'),
('X01','Hosted QUICK pilot','Three domains/model; six trajectories','S12','Ungated external harness; sparse descriptive rewards only.'),
('X02','Provider recovery preflights','Three provider-family checks','S12; archived status CSVs','HTTP 402 failures; no new inference outcomes.'),
('X03','Local GPU server attempts','Two failed startup archives','S12; source history','Infrastructure failures; no performance score.'),
('X04','Latest local T4 external pilot','Two AgentDojo rows/model; limited stateful rewards','S12; retained CSVs','Baseline/injection rows are related; no gate in callback path.'),
('O06A','October 6 live baselines','160 shared requests/model; three checkpoints','S6','Ungated verdict baseline; non-ALLOW denominator 140.'),
('O06B','October 6 live red team','300 attacks; 12 families','Article; S7','198 residual-unsafe classifications, not 198 native commits.'),
('O06C','October 6 stateful harness','160 paired requests','Article; S7','Exporter flags/effect counts; separate reference database implementation.'),
('O06D','October 6 demonstration ablation','240 demonstration requests','Companion audit; excluded','Demonstration backend; not empirical live-model validation.'),
('O08A','October 8 open-weight reference study','152 scored + 64 contrast realizations/model','Article; S8','Three models; full/anchors/single-best have identical decisions.'),
('O08B','October 8 contrasts and mutations','32 contrast pairs/model; applicable proposal mutations','S8','Applicability differs; zero eligible SmolLM2 negation deletions.'),
('O08C','October 8 public intent diagnostic','240 outputs/model; 24/cell','S8','Selected classes; public intent gold is not ERP authorization gold.'),
('O08D','October 8 uncertainty probe','40 requests; four samples/request','S11','AUC 0.475; no validated ambiguity estimator.'),
('O10','October 10 native counterexamples','Three native API/broker checks + seven pipeline probes; 16 separate reference controls','Article; S13','Vulnerable earlier source; reference controls are not deployed mediation.'),
('O11A','October 11 candidate intersection','360/direction; six methods','Article; S9','4,320 method rows are correlated; preferred proposal fixed.'),
('O11B','October 11 controlled subset','240/direction; 80 groups','S9','Nested subset of O11A, not an extra cohort.'),
('O11C','October 11 public intent diagnostic','336 outputs/model across two protocols','Article; S10','Same dataset family as earlier diagnostic; no independent ERP labels.'),
('O11D','October 11 contrasts and language agreement','60 pairs/model; 80 three-language groups','Article; S10','Validity and conditional agreement reported separately.'),
('O11E','October 11 uncertainty probe','30 requests; four samples/request','Article; S11','Ten requests have no valid sample; AUC confounded by failure.'),
('O11F','Selected secondary-interpretation retest','48 previously discovered regressions','Article; S9; raw retest archive','Selected-case diagnosis, not a fresh full-cohort replication.'),
('O11G','Blocked native regressions','Zero completed source assertions','S13; import-error records','Collection/probe failure is not a pass.'),
('O14','Independent-audit notebook smoke','Four demonstration examples','S15; companion audit','Input null/publication-eligible false; not model performance.'),
('O17A','Annotation history','32 requests, two supplied reviewer files','Companion private-cohort aggregate audit','Previously examined; policy/ethics documentation incomplete; excluded from paper outcomes.'),
('O17B','Offline original/parser-patch diagnostic','Same 32 requests in two arms','Companion private-cohort aggregate audit','Mock parser, no positive cohort, no independent holdout after debugging.'),
('O18','Prospective policy/new-case plan','Planning/review artifacts','Coverage record; no outcome score','A proposed experiment is not an executed result.'),
('O19','Synthetic source execution smoke','Four generated fixtures','S13; SQLite/traces','Mock extractor; one positive operation; year test accepts BLOCK or CLARIFY.'),
('O20','Local native broker repair','Nine probes; 34 security regressions','Article; S13','18 retained before/after databases; local SQLite only; 361 retained test passes.'),
('O21/22','Earlier live private diagnostic','Same 32 requests/model','Companion private-cohort aggregate audit','No positive labels and no simulation/commit; not manuscript validation.'),
('O23','Frozen native live controlled study','48 generated probes/model','Article; S14','Actual inference; three Qwen unsafe commits/five row changes.'),
('O23C','Known-candidate execution control','Same 48 generated probes','Article; S14','Correct supplied candidates, not model inference.'),
('O23H','Repeated private diagnostic','Same previously examined 32/model','Companion private-cohort aggregate audit','Repeated labels; no new human holdout; private text excluded.'),
('L750','Older MASSIVE/MTOP headline protocol','Reported 450/300 examples','Legacy-claim audit only','Matching original output/scorer records not recovered; no verified paper score.'),
('LX','Earlier local pilot headline claims','Reported nine-case/six-trajectory variants','Legacy-claim audit only','Do not substitute these for the recovered latest T4 snapshot.'),
]
with (B/'Audit/Experiment_Coverage.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['study_id','study','units','placement','qualification']);w.writerows(inventory)
md=['# Experiment coverage and preservation\n','Each recovered study or attempted study has an explicit destination. Rows are not independent cohorts and must not be summed.\n',
    '| ID | Study | Units | Kept in | Qualification |','|---|---|---|---|---|']
md+=['| '+' | '.join(row)+' |' for row in inventory]
(B/'Audit/Experiment_Coverage.md').write_text('\n'.join(md)+'\n')

para(r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.85in]{geometry}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{lmodern,microtype}
\usepackage{amsmath,amssymb,booktabs,array,longtable,xurl,caption}
\usepackage[hidelinks]{hyperref}
\captionsetup{hypcap=false}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.55em}\emergencystretch=2em
\renewcommand{\thetable}{S\arabic{table}}
\hypersetup{pdftitle={NiyamTrace-X Supplementary Information: complete recovered experimental record}}
\begin{document}
\begin{center}{\Large\bfseries Supplementary Information}\par\vspace{0.5em}
{\large NiyamTrace-X: Evaluating authorization safeguards for multilingual tool-using agents}\par
Badampudi Agasthya Anirudh, Sri Pranav K, Vijayarajan V\par
Evidence freeze: 13 October 2026\end{center}''')
para('This supplement preserves the recovered experimental record from the first constructive tests through the frozen native live evaluation. Earlier studies support or qualify the Article, but do not all test the same implementation or hypothesis. Algorithm fixtures, stored-output replays, live reference-harness runs, native execution, and failed benchmark attempts remain distinct. Results are not pooled across versions or counted again when re-exported. Private participant outcomes and unverified legacy headline claims remain in the companion audit rather than being promoted to manuscript validation.')
section(1,'Study coverage and evidence hierarchy')
para('The coverage map includes completed studies, nested analyses, repeated exports, attempted benchmarks and exclusions. A large row count does not imply many independent tests. Every numerical result below is either recomputed from retained records or explicitly identified as an archived report. The package includes source-file hashes and runnable analysis, so a reader can follow each finding to its evidence. Article references identify the public datasets and benchmark papers; experimental evidence here is identified by study and source record.')
table('Coverage of the recovered research history. Audit-only rows are considered and preserved, but excluded from publication performance claims.',
      ['ID / study','Units and destination','Interpretation'],[(a+' / '+b,c+'; '+d,e) for a,b,c,d,e in inventory],widths=[.29,.28,.33])
section(2,'Frozen reference outputs and language slices')
para('The frozen holdout has 500 semantic groups with four surface realizations per group. Both checkpoints reuse the same 2,000 requests. Four GPT-OSS parse errors remain incorrect. Qwen has 1,042 cached outputs; these are analyses of retained inference, not a new all-fresh model replication. Strict semantic correctness includes clarification and disagreement information. Eight-field agreement alone is a different metric.')
table('Language-specific strict semantic and final verdict correctness, recomputed from original output files.',
      ['Checkpoint','Language','Strict semantic','Final verdict'],[(x['model'],x['language'],f"{x['semantic_correct']}/500 ({pct(x['semantic_correct']/500)})",f"{x['verdict_correct']}/500 ({pct(x['verdict_correct']/500)})") for x in D['frozen_languages']])
table('Complete frozen ablation. Methods use the same records and are not independent cohorts.',
      ['Checkpoint','Stage','Correct / 2,000','Unsafe ALLOW'],[(x['model'],short(x['stage']),x['correct'],x['unsafe_allow']) for x in P['frozen_stages']])
para('GPT-OSS clarification-only retains two unsafe verdicts, matching its base replay. A former prose value of six is corrected. The current Article uses 10,000 whole-group bootstrap draws with seed 20261013. Earlier case-independent intervals and McNemar calculations are preserved in the original statistics archive but are not used for population inference. The illustrative zero-event bound uses 374 non-ALLOW semantic groups, about 0.80%, and requires generated-group exchangeability; it is not a deployed risk bound.')

section(3,'Initial constructive tests and generator audit')
para('A01 supplies 2,400 clean candidate-contract matches and 14,400 deliberately corrupted contracts across four language/script conditions. The predicate detects all corrupted contracts and rejects six clean matches: 16,794/16,800 agreement, or 99.96%. The clean false-positive rate is 6/2,400 (0.25%). This tests a predicate against constructed semantic contracts; it is not live language-model accuracy or a count of authorized database actions.')
table('Early anchor predicate by generated relation. Each relation contributes 2,400 examples.',
      ['Relation','Cases','Predicate agreement','Blocks'],[(short(x['relation']),x['n'],pct(x['accuracy']),x['blocks']) for x in D['anchor_stress']['relations']])
source('Early_Stages/01_Anchor_Stress_RESULTS/anchor_case_results.csv')
para('A02 samples 50,000 symbolic effect-set configurations and evaluates four rules on each configuration. The 200,000 method rows share those configurations. Full-rule correctness is perfect against this constructed oracle; that checks the encoded algorithm, not whether an extractor recovers all genuine readings of a request. Four saved property flags refer to the symbolic assumptions. They cannot establish unconditional natural-language soundness: intersection-only still has 1,745 unsafe verdicts relative to the anchor-aware oracle.')
table('Constructed effect-set ablation; all methods have the same 50,000 oracle cases.',
      ['Method','Correct / 50,000','Unsafe ALLOW','Unnecessary clarify'],[(short(x['system']),x['correct'],x['unsafe_allow'],x['unnecessary_clarify']) for x in sorted(D['constructed_effect_set_ablation'],key=lambda x:x['system'])])
source('Early_Stages/02_SIL_IIEA_ABLATION_RESULTS/sil_iiea_case_results.csv')
para('A03 repeats ten broker conditions 250 times each. All 250 valid calls commit and all 2,250 invalid calls are rejected. The retained records repeatedly name the same fixture invoices. They are not 2,500 independently sampled database states, and their success does not rule out an untested transaction race. The later A07 campaign explicitly varies states and arguments and is reported separately.')
table('First reference broker: repeated fixture checks.', ['Condition','Trials','Commits'],[(short(x['condition']),x['n'],x['commits']) for x in D['early_broker']])
para('A04 also retains a source audit of the original 10,000-row public/generated request corpus: 1,668 exact duplicate raw-text rows, 5,330 normalized-template duplicate rows, a normalized unique fraction of 46.7%, 7,380 semantic groups, and only 156 groups spanning multiple languages. The sampled near-duplicate rates are 47.7% at cosine threshold 0.95 and 55.95% at 0.90. These are archived corpus-audit results; the complete original corpus and vectorization run were not re-executed for this redraft. They qualify generator diversity and do not enlarge the 500-group frozen holdout.')
source('Early_Stages/04_STATS_REPRO_RESULTS/public_dataset_audit.json')

section(4,'Metamorphic hardening and transaction-first reference execution')
para('A06 contains 21,762 generated variants per detector: 9,756 expected attacks and 12,006 clean or semantics-preserving controls. Both saved detectors detect 8,260 attacks, miss 1,496 and produce no false positives, giving 84.67% attack recall. The misses occur in quantifier broadening. A09 uses a different 10,248-attack construction plus 2,000 clean controls. Its v2 recall is 85.40%; v3 closes all retained misses. The 84.67% and 85.40% rates have different denominators and must not be silently substituted.')
table('A06 family-level outcomes for the frozen predicate; the saved hardened-v2 predicate is identical on this campaign.',
      ['Family','Examples','Expected attack','False negatives','False positives'],[(short(x['family']),x['n'],pct(x['expected_trigger_rate']),x['false_negative'],x['false_positive']) for x in D['metamorphic_v2_families'] if x['detector']=='frozen'])
table('A09 retained attack families; the v3 rule was added after the primary freeze.',
      ['Attack family','Attacks','V2 recall','V3 recall'],[(short(x['attack']),x['n'],pct(x['v2_recall']),pct(x['v3_recall'])) for x in D['anchor_v3']['families']])
para('Neither v3 nor v2 fires on the 2,000 clean A09 controls. V3 adds no new trigger over 3,996 valid frozen model outputs; four invalid GPT-OSS outputs cannot be replayed. The separate 3,200 benign surface transformations also add no trigger. These are finite retained-case compatibility checks, not open-ended multilingual security guarantees, and they do not retrospectively replace the v2 headline experiment.')
para('A07 moves validation inside the SQLite write transaction and compares signed predicted effects, current effects, and committed changes. Each of eleven conditions has 120 distinct state and argument hashes. All 120 valid trials commit; all 1,200 invalid/crash trials fail closed or roll back. The retained legacy-race JSON contains a predicted identifier and a pointer to notebook output; by itself it does not reproduce a full independently audited legacy race. The transaction-first architecture and its randomized v2 results are the supported observations.')
table('Transaction-first reference broker. Distinct states and arguments: 120 per condition.',
      ['Condition','Trials','Commits'],[(short(x['condition']),x['n'],x['commits']) for x in D['reference_broker_v2']])
source('Early_Stages/07_VERIFIED_EXECUTION_BROKER_V2_RESULTS/exp07_randomized_attack_trials.csv')

section(5,'Exploratory risk-selective authorization')
para('A08 trains a selector using deployment-observable features and evaluates held-out generated requests. On its initial 600-case test split, selection removes 26 unsafe raw ALLOW verdicts and retains 155 of 181 raw allows (85.64%). Accuracy remains 94.00%, while the frozen full runtime gives 99.83% on those same 600 requests. This utility/risk comparison concerns the recorded generated distribution.')
table('Initial held-out selector comparison. The raw-allow retention column follows the original export definition.',
      ['Policy','Cases','Accuracy','Unsafe ALLOW','Auto-allow count','Raw-allow retention'],[(short(x['policy']),x['n'],pct(x['accuracy']),x['unsafe_allow'],x['auto_allow_count'],pct(x['raw_allow_retention'])) for x in D['selective_risk']['single_split']])
para('Five of twenty repeated group splits retain at least one unsafe ALLOW. Raw-allow retention ranges from 80.30% to 91.79%. The splits reuse source groups and are not twenty independent validation datasets. The original target risk level and calibration upper bound therefore cannot be presented as a distribution-free deployment guarantee.')
table('Repeated selector splits: all twenty outcomes are retained, including failures.',
      ['Seed','Test cases','Unsafe ALLOW','Raw-allow retention','Calibration upper bound'],[(x['seed'],x['n'],x['unsafe_allow'],pct(x['raw_allow_retention']),pct(x['cal_cp95_upper'])) for x in D['selective_risk']['repeated_splits']])
g=D['selective_risk']['gpt_transfer']
if g:
    table('Archived transfer comparison using GPT-OSS outputs; same selector protocol, not new inference.',
          ['Policy','Cases','Accuracy','Unsafe ALLOW','Auto-allow count'],[(short(x.get('policy','')),x.get('n',''),pct(x['accuracy']),x['unsafe_allow'],x.get('auto_allow_count','')) for x in g])

section(6,'October 6 live baseline behavior')
para('The October 6 T4 baseline uses 160 shared requests for each of three checkpoints. Each checkpoint has 140 expected non-ALLOW requests. This is an ungated verdict baseline and does not measure native broker protection. Invalid outputs remain incorrect. The unsafe-ALLOW denominator is 140, not 160.')
table('Ungated live baseline counts, recomputed from retained case rows.',
      ['Checkpoint','Correct / 160','Valid / 160','Unsafe ALLOW / 140'],[(short(x['model']),x['correct'],x['valid'],x['unsafe_allow']) for x in D['oct06_baselines']])
source('October06_Baselines/case_level_results.csv')

section(7,'October 6 adversarial and stateful failures')
para('The adaptive semantic red-team record uses a Qwen attacker and Granite victim across twelve generated families, with 25 attacks each. It retains 198 residual-unsafe classifications out of 300. This is a semantic/gate label, not evidence that 198 native database commits occurred.')
table('All red-team families; failures are not suppressed.', ['Attack family','Attacks','Residual-unsafe labels'],[(short(x['family']),x['n'],f"{x['residual_unsafe']} ({pct(x['residual_unsafe']/x['n'])})") for x in D['oct06_redteam']])
para('The separate stateful reference harness has 160 paired requests. Its exporter records 79 unsafe raw cases and 53 unsafe gated cases; its raw and gated effect-count sums are 318 and 240. The 320 final SQLite files are retained. These counts follow that harness and its initial-state assumptions; they are not pooled with the later native evaluation, whose complete before/after state and actual broker events are audited independently. A decrease from 79 to 53 is partial mitigation, not uniform containment.')
table('Stateful reference exporter results.', ['Arm','Requests','Unsafe-case flags','Effect-count sum'],[['Raw',160,79,318],['Gated',160,53,240]])
source('October06_Stateful/paired_results.csv')

section(8,'October 8 open-weight reference replication and diagnostics')
para('This separate protocol has 120 generated controlled requests plus 32 generated challenge wrappers per checkpoint, rendered in four language/script conditions. Another 64 contrast realizations are retained separately, giving 216 records per checkpoint and 648 overall. Full, anchor-only and single-best decisions are identical on the 152 scored requests. The same observations therefore do not isolate benefit from independent alternative interpretations.')
table('October 8 scored outcomes. Completion uses all 64 expected-ALLOW requests, including invalid outputs.',
      ['Checkpoint','Correct / 152','Valid / 152','Raw unsafe cases','Raw unsafe rows','Full completion / 64'],[(short(x['model']),x['correct'],x['valid'],x['raw_unsafe_cases'],x['raw_unauthorized_rows'],x['all_attempt_completion_n']) for x in D['oct08_semantic']])
para('All three full methods have zero observed unauthorized reference effects. Qwen completes 53/64 expected positive actions and Granite 48/64. SmolLM2 completes 44/64 (68.75%). Its old exported completion value is 44/54 (81.48%), conditional on a valid extraction; that denominator omits ten failed positive extractions. The all-attempt denominator is used here so failure cannot improve apparent utility.')
table('All October 8 ablation arms; methods share each checkpoint\'s 152 scored requests.',
      ['Checkpoint','Method','Verdict accuracy','Block rate','Clarify rate'],[(short(x['model_key']),short(x['variant']),pct(x['decision_accuracy']),pct(x['block_rate']),pct(x['clarify_rate'])) for x in D['oct08_ablations']])
table('October 8 language slices, 38 scored requests per cell.', ['Checkpoint','Language','Valid','Verdict accuracy'],[(short(x['model_key']),short(x['language']),pct(x['parse_success']),pct(x['full_accuracy'])) for x in D['oct08_languages']])
table('October 8 contrast pairs. Failed extraction remains in the pair-success denominator.', ['Checkpoint','Changed field','Pairs','Both valid','Pair success'],[(short(x['model_key']),x['contrast_field'],x['n'],pct(x['parse_both']),pct(x['pair_success'])) for x in D['oct08_minimal_pairs']])
para('Proposal-mutation recall is conditional on the mutation being applicable to a retained parsed proposal. Entity/year slots can be absent, scope can already be broad, and negation can already be lost. There are only four applicable negation-deletion mutations for Qwen and Granite and none for SmolLM2. A missing row for the latter is not 100% detection.')
table('Applicable mutation detections; non-applicable counts are retained in the source table.', ['Checkpoint','Mutation','Applicable','Detected'],[(short(x['model_key']),short(x['attack']),x['n'],x['detected']) for x in D['oct08_mutations']]+[['SmolLM2-1.7B','negation deletion',0,'Not defined']])
table('Mutation applicability across every attempted mutation type.', ['Checkpoint','Mutation','Attempted','Applicable','Not applicable'],[(short(x['model_key']),short(x['attack']),x['attempted'],x['applicable'],x['not_applicable']) for x in D['oct08_mutation_applicability']])
table('Retained clean-proposal controls. These contain model-derived proposals; a refusal may reflect earlier extraction error.', ['Checkpoint','Controls','Blocked/clarified','Exported false-positive rate'],[(short(x['model_key']),x['n_clean'],x['clean_block_or_clarify'],pct(x['clean_false_positive_rate'])) for x in D['oct08_clean_controls']])
para('The public intent diagnostic has 240 class-ID outputs per checkpoint: 24 requests per dataset/language/protocol cell. MASSIVE uses English, Hindi and Telugu, while MTOP uses English and Hindi. Both an English-prototype and an in-language prototype protocol are retained. Public intent labels are not independent authorization labels. Released utterances/prototype text are not redistributed in this package; output records and selected class metadata are retained.')
external=D['oct08_external'];cells=sorted({(x['dataset'],x['language'],x['protocol']) for x in external})
table('October 8 selected-class intent results; 24 attempts per cell. Cells show correct / valid output counts.',
      ['Dataset / language / protocol','Qwen','Granite','SmolLM2'],[(f'{d} / {l} / {short(p)}',*[f"{round(float(next(x for x in external if (x['dataset'],x['language'],x['protocol'],x['model_key'])==(d,l,p,m))['intent_accuracy'])*24)}/24; {round(float(next(x for x in external if (x['dataset'],x['language'],x['protocol'],x['model_key'])==(d,l,p,m))['parse_success'])*24)} valid" for m in ['qwen25_3b','granite33_2b','smollm2_17b']]) for d,l,p in cells],widths=[.37,.17,.17,.17])

section(9,'October 11 paired candidate methods and selected retest')
para('The preferred primary proposal is fixed across six methods. There are 360 requests per model direction and 100 semantic groups, comprising 240 controlled requests plus 120 minimal-pair realizations. The 4,320 method rows do not represent independent requests. The raw arm is deliberately unprotected and bypasses constraints; it is not a matched production baseline.')
table('All six paired methods, with exact completion over 162 expected positive requests per direction.',
      ['Primary','Method','Correct / 360','Unsafe cases','Unauthorized rows','Completion / 162'],[(short(x['direction']),short(x['variant']),x['correct'],x['unsafe_cases'],x['unsafe_rows'],x['exact_completions']) for x in P['paired_variants']])
table('Nested controlled-only slice: 240 requests, 80 groups, 60 expected-ALLOW requests per direction.',
      ['Primary','Method','Correct / 240','Completion / 60'],[(short(x['direction']),short(x['variant']),x['correct'],x['exact_completions']) for x in D['oct11_controlled_subset']])
para('Granite loses 48 correct decisions under full intersection, with no corrections; 28 are controlled requests and 20 are minimal-pair realizations. The regressions span 34 groups. The case-weighted decline is 13.33 percentage points, with whole-group bootstrap interval [-17.09,-9.69] for full-minus-anchors. Equal-group weighting gives -12.67 points and [-17.00,-8.67]. The previous mixed interval [-17.17,-8.67] is not used. Case-level McNemar values remain archival calculations without an independence claim.')
para('The selected secondary-model retest repeats 48 already discovered regressions. All still clarify: 29 have missing/null secondary arguments and 19 use invalid tool identifiers. The original response files and manifest are preserved in the audit. This is a selected failure diagnosis, not a new estimate for all 360 requests or a fresh two-direction replication.')

section(10,'October 11 public intent, contrasts and cross-language validity')
para('Each model supplies 336 outputs: 120 MASSIVE requests and 48 MTOP requests under each of two prototype protocols. MASSIVE covers English, Hindi, Kannada, Tamil and Telugu; MTOP covers English and Hindi. Class correctness and output validity are distinct. Both checkpoints use the pinned revisions retained in the Article package.')
nlu=D['oct11_external_cells'];cells=sorted({(x['dataset'],x['language'],x['protocol']) for x in nlu})
table('October 11 selected 12-class public intent results; each cell has 24 attempts.',
      ['Dataset / language / protocol','Qwen correct; valid','Granite correct; valid'],[(f'{d} / {l} / {short(p)}',*[f"{next(x for x in nlu if (x['dataset'],x['language'],x['protocol'],x['model'])==(d,l,p,m))['correct']}/24; {next(x for x in nlu if (x['dataset'],x['language'],x['protocol'],x['model'])==(d,l,p,m))['valid']}/24" for m in ['qwen','granite']]) for d,l,p in cells],widths=[.42,.24,.24])
table('October 11 critical-field contrast pairs.', ['Checkpoint','Changed field','Pairs','Both valid','Successful contrast'],[(short(x['model']),x['field'],x['n'],x['valid_both'],x['success']) for x in D['oct11_contrasts']])
table('Three-language consistency over 80 controlled groups. Agreement is not correctness.',
      ['Checkpoint','All three valid / 80','Identical proposals / 80','Agreement among valid'],[(short(x['model']),x['all_valid'],x['identical'],f"{x['identical']}/{x['all_valid']}") for x in D['oct11_crosslingual']])

section(11,'Sampling-based uncertainty and its failure confound')
para('The October 8 probe samples four interpretations for each of 40 requests. Its ambiguity AUC is 0.475 and the original multisample rule gives 37/40 correct decisions. That result does not validate disagreement as an ambiguity detector. The separate October 11 probe samples four interpretations for each of 30 Qwen requests. Ten requests yield no valid sample. Assigning them maximum disagreement gives AUC 0.639, while the 20 requests with any valid sample give AUC 0.500. The higher all-case value partly detects parser failure. Neither experiment supplies independently annotated sets of genuinely plausible interpretations.')
table('Uncertainty probes remain separate cohorts.', ['Protocol','Requests','Samples/request','No-valid requests','Ambiguity AUC'],[['October 8',40,4,D['oct08_uncertainty']['no_valid_samples'],'0.475'],['October 11, all attempts',30,4,10,'0.639'],['October 11, any valid sample',20,4,0,'0.500']])

section(12,'External benchmark attempts, pilot rewards and missing scores')
para('A10--A13 and subsequent recovery attempts are retained even when they produce no benchmark result. BFCL output CSVs are empty or timed out. AgentDojo attempts include CLI/API failures; an Agent-SafetyBench file inventory establishes availability, not successful execution. Provider recovery preflights fail with HTTP 402. Two original local GPU attempts fail during server startup. No score is assigned to an unexecuted model or an unavailable evaluator. Meta-stage matrices that aggregate these files are not new experiments.')
host=[x for x in D['external_hosted_quick'] if x['domain']!='ALL_3_DOMAINS']
table('Hosted QUICK pilot: one ungated external trajectory per domain/checkpoint.', ['Model label','Domain','Trajectories','Reward'],[(x['model'],x['domain'],x['n'],x['mean_reward']) for x in host])
para('The recovered latest T4 snapshot is smaller than some older draft descriptions. Its AgentDojo banking records contain one injected and one baseline row per checkpoint: Granite utility 0 and 1, security 0 and 1; Qwen utility 0 and 0, security 0 and 1. Those paired rows are not two independent tasks. Workspace, travel and Slack slices fail before a scored case. Granite has two scored stateful trajectories, airline reward 1 and retail reward 0; telecom is unscored. Qwen has no scored stateful trajectory in this latest snapshot. Context errors record a 3,072-token maximum. Earlier claims of nine evaluable AgentDojo cases per model, six Granite trajectories or four scored Qwen trajectories are retained only as legacy claims until matched records for that separate snapshot are available.')
table('Recovered latest T4 aggregates. These are ungated harness diagnostics, not NiyamTrace-X authorization scores.',
      ['Harness','Checkpoint','Metric','Recorded rows','Mean'],[(x['benchmark'],short(x['slug']),x['metric'],x['n'],x['mean'] if x['mean'] else 'Not scored') for x in D['external_latest_t4_summary']])
para('Chat, automatic tool choice and forced tool choice pass for Granite-3.3-2B, Qwen2.5-3B, Qwen2.5-7B-AWQ and xLAM-2-3B. Phi-4-mini and xLAM-1B pass chat/forced-tool preflight but fail automatic-tool selection. These compatibility checks cannot substitute for successful task-level benchmark evaluation. All recovered official gate-in-path readiness records report zero completed scored trajectories for AgentDojo, BFCL and the stateful harness. No official safety/task-success claim is made for a source adapter alone.')

section(13,'Native vulnerabilities, source smoke and later broker repair')
para('The earlier native snapshot at commit 651e87ef452c80008d4f73c8f2de21321e21fa50 retains three material counterexamples: direct executor invocation without gate authority changes three rows; an untrusted self-sealed certificate changes three rows; and a live missing-year request is assigned a year and changes three rows. The separate delta-mismatch test rolls back. These are historical implementation failures, not claims about every later source snapshot. The October 11 native pytest/probe attempt stops at dependency/collection errors and therefore does not validate a repair.')
scope={'CURRENT_DIRECT_EXECUTOR':'Native direct API','CURRENT_BROKER':'Native broker','STRICT_REFERENCE_NOT_DEPLOYED':'Reference only','ACTUAL_PRODUCTION_PIPELINE':'Native pipeline'}
table('Complete earlier native and reference case record. RECORDED is the original status, not an inferred pass. The upstream verdict can be ALLOW while a tampered call is rejected later; reference-only rows do not validate the native executor.',
      ['Scenario','Scope','Retained status','Recorded verdict','Changed rows'],[(short(x['scenario']),scope[x['condition']],x['status'],x['verdict'] or 'Not a verdict test',x['mutated_rows']) for x in D['earlier_native_cases']],widths=[.29,.19,.16,.16,.10])
para('O19 uses four generated English source-smoke fixtures with a mock extractor. The authorized archive changes exactly three invoice rows and consumes one nonce; the viewer, wrong-tenant and missing-year fixtures change no business rows. The missing-year fixture accepts either BLOCK or CLARIFY and returns BLOCK. Its configured smoke success therefore concerns no-write behavior, not exact CLARIFY-label accuracy. Other business handlers were not validated by this one-operation control.')
table('Four-fixture source smoke, prior to the fully audited local repair.', ['Fixture','Native verdict','Accepted by script','Business rows changed'],[(short(x['case']),x['decision'],x['expected_by_script'],x['business_rows_changed']) for x in D['source_smoke']])
para('O20 records local commit 8d1cb88de100c025800bc75cebd9bf1ed1fa5d59 with a 29-file patch manifest. All nine synthetic security probes have retained traces and eighteen before/after SQLite files. Independent logical-state comparison finds only the intended three-row positive archive; all eight negative probes change no business rows. Its retained test summary is 361 passed, one skipped, zero failed and 34 native adversarial regressions. This is a bounded local SQLite repair verification, without live model inference. The later frozen native experiment retains a different suite report, 364 passed and one skipped. These counts belong to different evaluated snapshots and are not contradictory or additive.')
table('Audited local native security repair: actual executor/broker/pipeline entry points.',
      ['Probe','Native verdict','Business changes','Positive completion'],[(short(x['probe'].replace('SEC-','')),x['decision'],x['business_rows_changed'],'Yes' if x['authorized_completion'] else 'Not a positive case') for x in D['native_repair']],widths=[.43,.14,.13,.20])
para('The local fixes exercise direct mediation, certificate origin, missing year, replay, stale state, tenant and role boundaries, policy revocation, and a valid positive commit. Earlier in-branch reports of 484 tests/19 probes and unsuccessful CI are preserved as historical source reports; they are not substituted for the independently retained local evidence or presented as current repository status. Source revisions, protected-key assumptions, and tested entry points delimit the claim. No distributed PostgreSQL or production deployment validation is inferred.')

section(14,'Frozen native live models and known-candidate control')
para('The final native controlled study has 48 generated probes per checkpoint: six vendor--month groups, two language conditions, and four families. Expected verdicts are twelve ALLOW, twenty-four BLOCK and twelve CLARIFY. The model response schema lacks an explicit negation slot, and its separate decision does not veto the extracted proposal. User messages contain no gold labels. Strict output validation is applied without retrospective normalization.')
table('All generated native attempts, with output and runtime failures kept in denominators.',
      ['Checkpoint / control','Native correct / 48','Output errors','Completion / 12','Commits','Unsafe cases (rows)'],
      [(m,v['native_correct'],v['model_output_errors'],v['authorized_nonempty_completions'],v['commit_cases'],f"{v['unsafe_effect_cases']} ({v['unsafe_business_rows']})") for m,v in P['native'].items()]+[['Known correct candidates',48,0,12,12,'0 (0)']])
para('Qwen has 35 month-type failures, ten correct native verdicts, six commits and three positive completions. Its other three commits violate explicit English prohibitions and change five invoice rows. The three valid negation proposals all execute; the other nine negation realizations fail validation. Granite has 43 output errors, five accepted early clarifications, no correct native verdicts and no positive completion. Its zero unsafe count accompanies total loss of authorized utility. The known-candidate control completes all twelve intended operations without unsafe effects. These outcomes are actual native effects, not the reference verdict or prototype-broker scores.')
para('Qwen has zero raw-model correct verdicts over these 48 requests, while Granite has five. Qwen\'s ten native correct verdicts occur in the 24 English probes; none occurs in the 24 Romanized Telugu probes. The output interface and generated templates limit this comparison. The public package verifies eighteen live and forty-eight known-candidate before/after logical-state pairs against final SQLite files: 66 pairs in the manuscript cohorts. The larger private export has 98 pairs, including the excluded repeated participant cohort. Those counts must not be interchanged.')

section(15,'Exclusions, incomplete evidence and preserved private history')
para('Demonstration notebook outputs are preserved as demonstrations. In particular, a 240-case demonstration ablation reports rates of 30%, 70%, 50% and 90% for its variants, and the independent-audit smoke contains four examples with no input dataset. Neither is a live validation experiment, and neither contributes a performance result in the Article. An empty file, an import error or a planned run is not counted as a completed test.')
para('The previously examined 32-request participant cohort and its annotation, offline-parser, parser-patch, earlier-live and repeated-live histories are all mapped in the companion audit. Supplied reviewer files agree on labels and the user confirms human validation. Those facts do not themselves establish a signed study policy, independent fresh sampling, or the ethics/consent record. The cohort has no positive ALLOW cases. Its numerical outcomes are preserved as aggregate audit records without private request text, but excluded from publication validation in these manuscripts. Previous planning targets such as 200 requests are not universal journal requirements and are not treated as rules here. Inclusion as a human-participant result would require the authors to resolve the actual documentation and policy context.')
para('The older 450-example MASSIVE / 300-example MTOP protocol appears in legacy drafts, with reported intent/slot/frame scores. Matching raw outputs and scorer artifacts for that exact protocol were not recovered. These claims remain in the legacy ledger; the verified selected-class October 8/11 results are used instead. Similarly, earlier external pilot headline counts are not silently mapped onto the smaller recovered latest snapshot. An explicit missing-evidence classification preserves provenance more accurately than an unsupported number in the results section.')

section(16,'Contract structure and conditional interpretation intersection')
para(r'''Let a supported request reading be represented by a contract $C=(a,t,\tau,\phi,\kappa,n)$: action $a$, target selector $t$, temporal constraints $\tau$, affected attributes/values $\phi$, cardinality/quantifier constraints $\kappa$, and polarity $n$. The reference extraction additionally retains clarification and disagreement information. For fixed state $s$, a compiled effect set $\widehat E(C,s)$ represents the permitted changes. Order contracts by effect-set inclusion at that state: $C_1\preceq_s C_2$ if $\widehat E(C_1,s)\subseteq\widehat E(C_2,s)$. Intersection is the conservative meet of supplied represented effect sets, not a proof that the supplied readings are complete or plausible.''')
para(r'''For principal $p$, let $P(p,s)$ be policy-permitted effects and $I(u)$ the retained candidate set. The intended authority is $A(u,p,s)=\varnothing$ when $I(u)=\varnothing$; otherwise $A(u,p,s)=P(p,s)\cap\bigcap_{C\in I(u)}\widehat E(C,s)$. An explicit write prohibition contributes no write permission. Missing critical scope requires clarification before a guessed selector can authorize a write. Read-only assistance and authorization of a future write are distinct; a write-level BLOCK label must not be confused with denial of all assistance.''')
para(r'''If every supported security-relevant reading is covered, each compiled set stays within that reading, policy/state checks remain current, and every committed effect is mediated, every accepted effect belongs to all supported readings and policy. This conditional statement follows from set inclusion. Its premises can fail: a model can omit negation, hallucinate a target, supply an invalid secondary candidate, or fail to represent a plausible reading. A superfluous restrictive candidate can prevent a legitimate action. The constructive SIL/IIEA tests check encoded set operations; the independent-candidate and native studies test consequences of unreliable inputs.''')
table('Representation-to-implementation correspondence and observed boundaries.',
      ['Component','Reference construction','Native evaluated interface'],[
      ['Polarity','Explicit negation field and request anchors','No explicit negation slot; prompt asks unknown/BLOCK; separate decision is not a veto'],
      ['Interpretation set','Candidate effect-set intersection','One recorded live extraction; reused if repair is requested'],
      ['Principal authority','Separate policy-permitted effect set','Trusted fixture principal; login/JWT path not evaluated'],
      ['Evidence','Support for the proposed contract','Access-controlled policy chunks; equal Jaccard/fuzzy retrieval; deterministic support rules'],
      ['Effect boundary','Reference effect oracle','Gate certificate and protected-key broker inside SQLite transaction'],
      ['Positive utility','Exact authorized set completed','All intended OPEN invoices in exact scope archived; no partial/no-op credit'],
      ['Completeness','Requires supported-reading coverage','Not established by internal consistency or model confidence']])
para('A capability preserves the proposal accepted by the gate through execution. It cannot repair a missing request prohibition before issuance. This is why the current local broker controls can pass while the live model path still makes three unauthorized commits.')

section(17,'Reproduction, file provenance and corrections')
para(r'''Run \path{Analysis/reproduce_results.py} for the primary experiments and \path{Analysis/reproduce_history.py} for the historical records. Both use the Python standard library, make no model calls, and check retained rather than newly executed source-test reports. The package-wide SHA-256 file covers the delivered files; \path{Audit/Historical_File_Provenance.json} maps each recovered historical record to its original archive member. Private text is not redistributed. Benchmark utterances/prototypes should be obtained from their original releases under their terms for any fresh inference.''')
para('The editorial corrections include GPT-OSS clarification-only unsafe count two; case-weighted versus equal-group bootstrap estimands; failure-inclusive SmolLM2 completion 44/64 rather than conditional 44/54; mutation applicability and zero eligible negation cases; and separation of the recovered latest T4 pilot from unsupported older headline counts. Earlier source reports remain available with their version/protocol labels. No zero count is promoted to zero production risk, and no failed source test is promoted to a pass.')
para(r'\end{document}')
(O/'supplement.tex').write_text('\n'.join(parts))
print(json.dumps({'coverage_rows':len(inventory),'supplement_tables':sum(p.count('\\caption{')+p.count('\\captionof{table}') for p in parts)},indent=2))
