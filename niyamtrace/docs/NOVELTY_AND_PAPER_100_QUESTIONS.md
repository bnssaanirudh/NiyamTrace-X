# 100 additional questions on novelty and the paper

Use these as possible answers, not claims that every feature is unprecedented. Questions 101–200 continue the earlier `FACULTY_100_QUESTIONS.md`. The defensible novelty claim is the paper's **specific integration and evaluation** of request-grounded constraints, policy, mediated execution and measured effects in its studied setting. The literature must be compared before claiming priority or uniqueness. Sources for study-specific numbers are `paper/current/main.tex`, its tables, and `apps/dashboard/static/paper-results.json`. Explain your actual contribution and permitted assistance truthfully.

## Research novelty and positioning

101. **What is the specific novelty claim?** The paper connects original request constraints to tool proposals and measured business effects, and evaluates the resulting safety–utility trade-off across distinct experimental settings.
102. **Is the underlying idea of authorization new?** No. Authorization, least privilege and policy enforcement are established ideas; the claim concerns their combination and evaluation for this request-to-effect problem.
103. **Is using an LLM for extraction novel by itself?** No. The contribution does not rest on the mere use of a language model to extract structured intent.
104. **What is the gap the paper addresses?** A role or tool permission may be valid while an individual proposed effect exceeds the user's actual request.
105. **Why describe novelty as an integration claim?** The individual building blocks have prior art; their particular composition and evidence must be assessed as a system contribution.
106. **Is this a new foundation-model architecture?** No. The work studies authorization and execution around model proposals, not a new transformer or pretrained model.
107. **What is new compared with simply asking an agent to be careful?** The proposed action is represented and checked at an explicit enforcement boundary, with outcomes and effects recorded.
108. **What is the paper's unit of protection?** An individual request and its permitted effects on business state in the studied workflows.
109. **Can a good engineering integration be a research contribution?** Yes, when it defines a precise problem and produces informative comparisons and failure analysis; significance depends on evidence and relevant prior work.
110. **How would you defend originality without overclaiming?** Explain the concrete mechanism, compare it to the cited closest systems, identify overlapping components, and state what the experiments add.

## Related work and alternatives

111. **How does this relate to role-based access control?** RBAC restricts capabilities by role; this work adds request-specific target and effect constraints.
112. **How does it relate to attribute-based access control?** Attributes can express identity and context conditions; request grounding additionally attempts to derive specific bounds from the user's instruction.
113. **How does it relate to capability systems?** Capabilities restrict authority through explicit grants; request-derived bounds could complement them, but equivalence or superiority is not established here.
114. **How does it relate to least privilege?** It applies a least-authority intuition to the scope of an individual proposed action and its effects.
115. **How does it relate to a policy engine?** A policy engine can enforce rules on structured inputs; this system also studies whether those inputs reflect the original request and the resulting write.
116. **Why not rely only on a system prompt?** A prompt is not itself a deterministic transaction boundary; the paper evaluates explicit mediation around proposed effects.
117. **Why not use only a tool allowlist?** An allowed tool can still be called with an unauthorized vendor, period, amount or target.
118. **Why not use human approval for every request?** It could reduce some risks but adds cost and delay; the paper motivates evaluating automated controls and selective escalation. A head-to-head study is needed for a quantified comparison.
119. **How is this different from prompt-injection benchmarks?** The paper focuses on mismatches between user request and effect; existing benchmarks often emphasize attacks from untrusted external content, though these concerns overlap.
120. **Does the paper claim official AgentDojo or other external benchmark scores?** No. The paper states exported external trajectories do not establish an official gate-in-path benchmark score.

## Formal ideas and boundary

121. **What is the intended safety invariant?** A committed effect should remain within the effect set authorized by the original request, identity and applicable policy.
122. **Can you express the invariant mathematically?** Ideally, committed delta Δ is a subset of the authorized effect set A(request, principal, policy); this ideal depends on how A is derived and checked.
123. **What is the main weakness of that expression?** The true meaning of a natural-language request is not automatically known; an incorrectly constructed A can permit an unwanted action.
124. **Why check both arguments and effects?** Correct-looking parameters do not alone establish that the underlying tool changes only the intended rows and fields.
125. **Is matching record counts sufficient?** No. Two different sets of rows can have the same count; identities, fields and values must be compared.
126. **What are selectors?** Conditions choosing affected records, such as vendor, month and year; a mismatched selector can broaden or redirect a write.
127. **What are negative constraints?** Instructions excluding actions, such as “do not archive”; losing negation can reverse the authorized effect.
128. **Does a typed schema enforce meaning?** It validates structure and types, but a schema-valid output can still misrepresent the user's intent.
129. **What is the difference between policy authorization and user intent?** Policy may permit a capability while the user's request provides a narrower authorization or an explicit prohibition.
130. **Where should enforcement occur?** Before the action commits, with the checked proposal bound to execution; post-execution detection can reveal a failure but cannot undo its original occurrence by itself.

## Evaluation structure

131. **Why are several experimental settings needed?** Reference verdicts, effect replay and native execution expose different failure modes and support different claims.
132. **What does a verdict-only experiment measure?** Whether decisions match a reference; it does not directly measure which database rows were changed.
133. **What does a native SQLite experiment add?** It observes committed business-state effects under the tested model, tool and execution setup.
134. **Why include a known-candidate control?** It helps isolate the executor and gate when supplied structured semantic inputs, separately from errors in model interpretation.
135. **Why is this not a full causal decomposition?** Different conditions and cohorts can vary in more than one way; a controlled matched experiment is required for stronger causal attribution.
136. **What is an ablation?** Removing or changing one component while keeping other relevant conditions fixed to estimate its contribution.
137. **Which ablations are especially relevant?** Compare model-only, role/scope, request grounding, interpretation intersection and certificate/broker controls on matched cases.
138. **Why test legitimate as well as prohibited requests?** To measure useful authorized completion alongside unauthorized effects; refusal alone can inflate apparent safety.
139. **Why retain failures in a paper?** They reveal failure modes and bound the strength of claims, and provide regression cases for future improvements.
140. **What should be frozen before a rerun?** Code and model versions, prompts, policies, dataset, seeds, environment and scoring rules; report deviations explicitly.

## Results and interpretation

141. **What is the frozen Qwen full-sequence result?** 1,997 correct verdicts out of 2,000 and zero observed unsafe final verdicts in that reference cohort.
142. **What is the frozen GPT-OSS full-sequence result?** 1,996/2,000 correct and zero observed unsafe final verdicts in that reference cohort.
143. **Are these numbers native write guarantees?** No. They are reference verdict results and cannot establish native database-write safety.
144. **What did the paired Granite anchor arm complete?** 152 of 162 authorized requests, with zero observed unsafe cases in that reference arm.
145. **What did full intersection change for Granite?** Authorized completion fell to 104/162, 48 fewer, without an additional observed reduction in unsafe cases in that comparison.
146. **Why can intersection hurt utility?** If it rejects a valid interpretation when alternatives disagree, legitimate tasks can be blocked; that is a proposed explanation, not proof for every individual failure.
147. **What did the native Qwen arm expose?** Three prohibited archive commits affecting five synthetic invoice rows, alongside 3/12 authorized completion in 48 attempts.
148. **Why is Granite's zero unsafe commits insufficient alone?** It also completed 0/12 authorized actions and produced many output errors, so non-execution contributed to the observation.
149. **What did the known-candidate native arm achieve?** It completed 12/12 authorized actions and observed no unsafe effects in 48 attempts, with structured candidates supplied rather than inferred.
150. **Why keep historical results after the guard was added?** The guard is a later implementation change; historical observations remain evidence until a controlled rerun measures the new version.

## NTX-24B and multilingual evidence

151. **What is NTX-24B?** A corrected-parser reference replay of saved NTX-24 generations, not an independent new generation run.
152. **What is its per-model cohort?** 120 saved generations: 104 non-ALLOW and 16 ALLOW cases.
153. **What are the model-only unsafe reference counts?** 61/104 for Qwen and 60/104 for Granite in the reported replay.
154. **What did text grounding observe?** Zero unsafe reference effects in 104 non-ALLOW cases per model and 13/16 authorized completion per model.
155. **What does 13/16 mean as a percentage?** 81.25% completion in that specific authorized subset; it is not a universal model accuracy.
156. **Did the certificate arm improve the observed count over text grounding?** The reported replay shows the same outcomes on those saved proposals; do not claim an incremental measured gain there.
157. **Which languages were stratified?** English, Hindi, Telugu and Romanized Telugu for each of the two models in the corrected replay.
158. **How many authorized examples per language?** Four per language per model, with 26 non-ALLOW examples; the same 120-case cohort is partitioned by language.
159. **What is the multilingual limitation?** Four authorized cases per language are too few for broad conclusions, and generated templates lack independent bilingual adjudication in this cohort.
160. **Why is a live Hindi or Telugu demo not validation?** A single exploratory observation cannot establish population performance or replace a controlled, independently reviewed evaluation.

## Statistical and methodological scrutiny

161. **Does zero observed unsafe cases establish zero probability?** No. Finite samples can miss rare failures; the estimate also depends on how representative and independent the cases are.
162. **Can you give a rough upper bound for zero events?** For n independent, representative Bernoulli trials, the one-sided 95% upper bound is 1−0.05^(1/n), approximately 3/n; correlated generated cases undermine that simple assumption.
163. **What would that bound be for 104 independent cases?** Approximately 2.84% exactly, or about 2.9% by the rule of three; do not treat it as a validated real-world risk bound for the correlated replay.
164. **Why avoid treating templates as independent observations?** Shared generators and families can make errors correlated, reducing the effective information in the sample.
165. **How should uncertainty be reported?** Give raw counts and denominators, appropriate intervals, dependence assumptions and, where feasible, cluster-aware or family-level analyses.
166. **What is data leakage here?** Overlap between tuning, prompt development and evaluation patterns could inflate results; investigate family, template and model-output reuse.
167. **What is the difference between a holdout and independence?** A held-out set is separated by a chosen procedure; it may still share generators, structures or linguistic patterns with development data.
168. **Why evaluate per language?** Aggregate numbers can hide failures in particular scripts or language varieties; small subgroup sizes still limit inference.
169. **What can multiple comparisons do?** Examining many methods and subgroups increases the chance of finding apparent differences by chance; predefine comparisons or adjust interpretation.
170. **How should model variability be evaluated?** Repeat with documented model versions, seeds where supported, multiple runs and confidence intervals; hosted APIs may not guarantee reproducibility.

## Threat model and limitations

171. **What is in the paper's threat model?** Mismatched selectors, missing authorization and forgotten prohibitions in the studied request-to-effect workflows.
172. **What is excluded?** The paper identifies privileged Python code execution, signing-key leakage, distributed concurrency and external enterprise connectors as outside its threat model.
173. **Does it solve all prompt injection?** No. Untrusted-content attacks interact with authorization, but the reported study does not establish comprehensive protection against them.
174. **Can a compromised signing key undermine the boundary?** Yes. Key compromise is outside the paper's stated scope and needs separate controls and testing.
175. **What if the model chooses the wrong target?** The system must compare against request-grounded constraints; if the constraint extraction itself is wrong, further independent grounding is needed.
176. **What if the policy source is stale?** The local implementation checks evidence eligibility and can block actions; inspect the recorded reason and source metadata.
177. **Is semantic equivalence always straightforward?** No. Ambiguity, implicit references, multilingual phrasing and conflicting instructions can require clarification or human review.
178. **Why is synthetic SQLite a limitation?** It offers controlled, inspectable effects, but cannot alone establish behavior in distributed enterprise systems.
179. **Does the current demonstration reproduce the paper automatically?** No. Current live interactions and historical research experiments have different setups, versions and purposes.
180. **What should the examiner infer from a failed live API call?** Provider availability is a practical limitation; it does not by itself establish the correctness or failure of a particular authorization rule.

## Reviewer challenges and future work

181. **What is the strongest criticism of the novelty?** Existing work already combines policies, capabilities and tool controls; the paper needs precise comparisons showing which connection and evaluation are distinctive.
182. **How would you answer “this is only a wrapper”?** Acknowledge the system is a mediation layer, then defend its explicit invariant, execution-bound effect checks and empirical analysis; a wrapper alone does not establish novelty.
183. **What result challenges your own proposal?** The native Qwen prohibited commits show that internally consistent proposals and certificates did not ensure correct semantic authorization.
184. **What is the most important trade-off?** Safety must be assessed with exact authorized completion; more conservative controls can prevent useful actions.
185. **What if all methods simply reject?** Report completion as well as unsafe effects. Zero unsafe commits with zero completion is not a successful useful agent.
186. **How would you test the later English prohibition guard?** Freeze the new version, replay the historical prohibition cases and matched allowed cases, measure commits and completion, and keep model-backed and guard-only results distinct.
187. **How would you test robustness to paraphrase?** Collect independently authored paraphrases and negations, include unseen families and languages, adjudicate meanings, then measure exact effects and completion.
188. **How would you test generalization to other tools?** Add distinct operations and state schemas with independently designed policies and tests; evaluate on tasks not used to develop the rules.
189. **How would you test concurrent execution?** Use controlled competing transactions, injected delays and independent writers; check isolation, stale predictions, exact deltas and rollback.
190. **How would you test policy changes?** Version and revoke evidence, test stale or unauthorized sources, and verify that policy updates affect only appropriate decisions.
191. **What independent baselines would strengthen the paper?** Compare well-specified role-only, policy-only, capability-based and human-review baselines on the same cases and state; avoid assuming which wins.
192. **What would strengthen ground truth?** Independent domain experts, bilingual adjudication, documented disagreement resolution and a held-out set of naturally authored requests.
193. **How would you investigate model errors?** Categorize schema errors, missing scope, polarity loss and wrong targets, and link each to final effects and task completion.
194. **How would you evaluate cost?** Measure model calls, latency, token usage, retrieval and broker overhead, and approval workload on a specified deployment and cohort.
195. **How would you monitor deployment?** Track provider availability, decision reasons, effect mismatches, latency, evidence freshness and drift, with privacy-aware trace handling.
196. **What is needed for stronger provenance?** Versioned datasets and prompts, source hashes, environment manifests, timestamped reports and a reproducible protocol that preserves failed runs.
197. **Can you claim the system is production-grade?** The evidence supports a local research prototype; production claims need additional security, reliability, integration and operational validation.
198. **What is the practical contribution despite failures?** The study makes request scope and actual effects inspectable and identifies concrete failure cases for improving the authorization path.
199. **What is the next research hypothesis?** For example, independent source-grounded polarity and target checks may reduce prohibited commits without excessive loss of authorized completion; test it rather than asserting it as fact.
200. **Give a 30-second novelty defense.** “Our work studies a boundary between what a user specifically requests and what an AI tool actually changes. We combine request-derived constraints, policy checks and mediated execution, and evaluate both unauthorized effects and useful completion. The native failures show why binding a proposal is not enough if the proposal misunderstood the request. The contribution is that specific system and evidence, with limits that require further validation.”
