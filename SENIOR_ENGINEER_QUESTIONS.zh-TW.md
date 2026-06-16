# Senior Engineer 可能會問的 15 個問題

這份文件針對 `Policy Ops Agent` 專案，整理 senior engineer 在 code review、design review 或 capstone presentation 中可能會追問的問題。每題都包含中文問題、English question、追問重點，以及中英文簡答版，方便直接準備 Q&A。

## 1. 為什麼 synthesizer 不使用真正的 LLM，而是 deterministic extractive synthesizer？

English question:

> Why does the project use a deterministic extractive synthesizer instead of a real LLM?

Senior engineer 可能想確認：

- 這是為了 demo/eval 可重現，還是因為缺少 LLM integration？
- 如果換成真正 LLM，要如何保留 citation grounding？
- 現在的 deterministic answer 是否過度依賴 exact sentence extraction？
- 這樣的設計是否能代表真實 agent behavior？

簡答 中文：

> 這是刻意的 capstone 設計取捨。專案重點是展示 agent workflow、RAG、tools、security、memory 和 evaluation，因此用 deterministic synthesizer 讓測試與評估完全可重現。Production 版本可以替換成 LLM，但需要加上 grounded prompting、citation verification 和 output validation。

Short answer English:

> This is an intentional capstone trade-off. The goal is to make the agent workflow, RAG, tools, security, memory, and evaluation reproducible. A production version could replace it with an LLM, but would need grounded prompting, citation verification, and output validation.

## 2. Retrieval 目前是 lexical scoring，為什麼不用 embeddings 或 vector database？

English question:

> Why does retrieval use lexical scoring instead of embeddings or a vector database?

Senior engineer 可能想確認：

- 現有政策 corpus 很小，所以 lexical retrieval 是否已足夠？
- 當政策文件增加到數百或數千份時，這個方法是否還可擴展？
- synonym、paraphrase、semantic matching 目前如何處理？
- baseline/optimized 的差異是否只是 hard-coded domain rules？

簡答 中文：

> 因為目前 corpus 很小，lexical retrieval 足以支援可重現的 baseline/optimized 實驗，也容易解釋錯誤原因。若政策文件變多或問題措辭更自由，下一步會改成 embeddings 或 hybrid retrieval，同時保留 lexical signals 和 citation traceability。

Short answer English:

> The current corpus is small, so lexical retrieval is enough for a reproducible and explainable baseline/optimized experiment. For a larger or more varied policy corpus, I would move to embeddings or hybrid retrieval while preserving lexical signals and citation traceability.

## 3. Optimized retrieval 的 boost rules 會不會太 domain-specific？

English question:

> Are the optimized retrieval boost rules too domain-specific?

Senior engineer 可能想確認：

- `_threshold_boost()` 是否只是為了修正 golden set 的特定案例？
- 新政策或新 threshold 加入後，誰負責維護 boost rules？
- 這些 boost 是否可能讓不相關 chunk 被錯誤排到前面？
- 有沒有 regression tests 覆蓋 boost 導致的副作用？

簡答 中文：

> 是，這是刻意揭露的 trade-off。optimized retrieval 用小型 domain-specific boost 修復 threshold 類 failure case，證明 eval 能抓出 retrieval 問題並衡量修正效果。但這不是長期最佳架構，政策規模變大後應改用 hybrid retrieval、reranking 或更系統化的 metadata/ontology。

Short answer English:

> Yes, that is an explicit trade-off. The optimized retriever uses small domain-specific boosts to fix a threshold-style failure and show that the eval can measure the improvement. It is not the long-term retrieval architecture; at larger scale I would use hybrid retrieval, reranking, or structured metadata.

## 4. Security guardrails 的 coverage 夠嗎？

English question:

> Are the security guardrails comprehensive enough?

Senior engineer 可能想確認：

- PII detection 目前只靠幾個 regex，是否會漏掉 email、phone number、address、API key？
- Prompt injection patterns 是否足以涵蓋 indirect injection 或 obfuscated input？
- Dangerous actions 是 substring matching，是否容易 false positive 或 false negative？
- blocked request 是否真的保證不會呼叫 tools？

簡答 中文：

> 對 capstone demo 夠用，但不夠 production。現在 guardrails 覆蓋常見 PII、prompt injection 和 dangerous action，並且在 tool routing 前執行，確保 blocked request 不會 call tools。Production 需要更完整的 PII/secrets detector、policy-based authorization、red-team tests 和 monitoring。

Short answer English:

> They are sufficient for the capstone demo, but not production-grade. The current checks cover common PII, prompt injection, and dangerous actions, and they run before tool routing so blocked requests do not call tools. Production would require stronger PII/secrets detection, policy-based authorization, red-team tests, and monitoring.

## 5. Tool authorization 為什麼只針對 escalation tool 做特殊檢查？

English question:

> Why does tool authorization only have special handling for the escalation tool?

Senior engineer 可能想確認：

- `retrieve_policy` 和 `remember_user_context` 是否也需要 permission model？
- Memory tool 是否可能記住敏感資訊？
- 未來如果加入外部 side-effect tools，例如 Jira、Slack、email，授權模型要如何擴充？
- tool permission 是否應該和 user role / policy scope 綁定？

簡答 中文：

> 因為目前 tools 都是本地且低風險，只有 escalation 代表可能被濫用成 bypass approval，所以先加特殊授權。Production 版本應該讓每個 tool 都有 permission policy，並根據 user role、資料分類、side effect 風險和 idempotency 做授權。

Short answer English:

> The current tools are local and low-risk, while escalation is the one that could be misused to bypass approvals. In production, every tool should have an explicit permission policy based on user role, data classification, side-effect risk, and idempotency.

## 6. Audit log 是否足以支援 governance requirements？

English question:

> Is the audit log sufficient for governance requirements?

Senior engineer 可能想確認：

- `data/audit.log` 是 local JSONL，是否能被使用者竄改？
- 是否需要不可變儲存、簽章、集中式 log collection？
- audit event 是否記錄足夠資訊，例如 retrieved citations、security tags、tool args？
- 是否會把敏感 user input 原文寫進 log，造成 data retention 風險？

簡答 中文：

> 目前 audit log 適合 demo 和本機 debugging，不是 production governance solution。它有記錄 answered/blocked、tool calls、metadata 和 timestamp。Production 需要集中式、不可竄改或可簽章的 audit storage，並對敏感輸入做 redaction 和 retention policy。

Short answer English:

> The current audit log is useful for demo and local debugging, but it is not a production governance solution. It records answered/blocked decisions, tool calls, metadata, and timestamps. Production would need centralized immutable or signed audit storage, plus redaction and retention policies for sensitive input.

## 7. Memory store 是否有資料治理問題？

English question:

> Does the memory store create data governance risks?

Senior engineer 可能想確認：

- `data/memory.json` 目前沒有 TTL、加密、刪除機制。
- 使用者如果要求記住 PII，目前是否會被 security layer 擋住？
- memory notes 是否需要分類，例如 preference、team context、sensitive data？
- 多使用者同時寫入 JSON file 時，是否會有 race condition？

簡答 中文：

> 有，這是 demo 版本最明顯的 production gap 之一。現在 memory 只用 JSON 保存最近 notes，適合展示 cross-session behavior。Production 需要 TTL、刪除權、加密、敏感資料分類、concurrency control，以及更嚴格的 memory write policy。

Short answer English:

> Yes, this is one of the clearest production gaps. The JSON memory store is only meant to demonstrate cross-session behavior. Production would need TTLs, deletion rights, encryption, sensitive-data classification, concurrency control, and stricter memory write policies.

## 8. `PolicyOpsAgent.ask()` 的 orchestration 是否會變得太肥？

English question:

> Is `PolicyOpsAgent.ask()` doing too much orchestration?

Senior engineer 可能想確認：

- validation、security、routing、tool execution、synthesis、audit 都在 `ask()` 裡，未來是否難維護？
- 是否需要把 workflow 拆成 pipeline steps 或 middleware？
- error handling 是否應該更細分，例如 retrieval failure 和 security block 不該都叫 blocked？
- metadata schema 是否需要穩定化？

簡答 中文：

> 目前大小仍可接受，因為專案刻意保持 code path 直觀，方便 presentation 和 tests。若功能增加，應該拆成 pipeline stages，例如 validation、policy decision、tool execution、synthesis、audit sink，並且讓 error taxonomy 和 response metadata 更穩定。

Short answer English:

> It is acceptable for the current project because the code path is intentionally explicit for presentation and testing. If the system grows, I would split it into pipeline stages such as validation, policy decision, tool execution, synthesis, and audit sink, with a clearer error taxonomy and stable metadata schema.

## 9. Evaluation 是否真的能衡量回答品質？

English question:

> Does the evaluation really measure answer quality?

Senior engineer 可能想確認：

- `fact_recall()` 用 substring matching，是否太脆弱？
- answer 語意正確但 wording 不同時會不會被判錯？
- answer 包含 expected fact 但上下文錯誤時會不會被判對？
- forbidden facts 是否足以防止 hallucination？

簡答 中文：

> 它衡量的是可重現的最低品質門檻，不是完整自然語言品質。expected facts、forbidden facts、citation 和 context recall 能抓出關鍵錯誤，尤其是 retrieval failure。更完整的版本會加入 semantic similarity、LLM judge、人類標註、多輪測試和 adversarial cases。

Short answer English:

> It measures a reproducible minimum quality bar, not full natural-language quality. Expected facts, forbidden facts, citations, and context recall catch important failures, especially retrieval failures. A stronger version would add semantic similarity, an LLM judge, human labels, multi-turn tests, and adversarial cases.

## 10. RAGAS-style context recall 的實作是否夠嚴謹？

English question:

> Is the RAGAS-style context recall implementation rigorous enough?

Senior engineer 可能想確認：

- 目前 context recall 只是 expected fact substring 是否出現在 retrieved context。
- 這和真正 RAGAS context recall 有哪些差距？
- blocked security cases 讓 context recall 下降到 0.92，是否應該從 aggregate 中分開統計？
- 是否需要 precision metric，避免 retrieval 回傳太多不相關 context？

簡答 中文：

> 這是 RAGAS-style 的簡化版，用來滿足 capstone 對 semantic/context metric 的要求並保持 deterministic。它能檢查 retrieved context 是否支援 expected facts，但缺少語意匹配和 context precision。更嚴謹版本會分開統計 blocked cases，並加入 context precision、faithfulness 和 semantic recall。

Short answer English:

> It is a simplified RAGAS-style metric designed to satisfy the capstone requirement while staying deterministic. It checks whether retrieved context supports expected facts, but lacks semantic matching and context precision. A stronger version would separate blocked cases and add context precision, faithfulness, and semantic recall.

## 11. Judge/kappa 的設計是否有說服力？

English question:

> Is the judge/kappa design convincing?

Senior engineer 可能想確認：

- `heuristic_llm_judge()` 是 deterministic heuristic，不是真正 LLM judge。
- human labels 全部是 1，kappa 1.0 是否有實質意義？
- 如果沒有 negative human labels，agreement metric 是否過於樂觀？
- 是否應該加入錯誤答案或人工標註的 mixed-quality cases？

簡答 中文：

> 目前 judge/kappa 展示的是 workflow，不是最強的統計證據。它能證明專案有 judge score 和 human label agreement pipeline，但 human labels 全為正例使 kappa 過於樂觀。更好的版本應加入 negative/mixed-quality labels、第二位 human judge 或真正 LLM judge。

Short answer English:

> The current judge/kappa demonstrates the workflow, not the strongest statistical evidence. It shows a judge-score versus human-label agreement pipeline, but all-positive human labels make the kappa optimistic. A better version would include negative or mixed-quality labels, a second human judge, or a real LLM judge.

## 12. Unit tests 是否覆蓋了重要 failure modes？

English question:

> Do the unit tests cover the important failure modes?

Senior engineer 可能想確認：

- 測試涵蓋 routing、security、memory、audit、retry、unknown tool。
- 是否有測試 retrieval ranking regression？
- 是否有測試 malformed policy files？
- 是否有測試 corrupted memory JSON？
- 是否有測試 concurrent writes 或 file permission errors？

簡答 中文：

> 現有 tests 覆蓋 capstone 要求的核心行為，包括 routing、安全封鎖、memory persistence、audit、retry 和 tool error。還可以補強 retrieval ranking regression、corrupted memory、malformed policy、file permission error 和 concurrency tests。

Short answer English:

> The current tests cover the core capstone behaviors: routing, security blocking, memory persistence, audit logging, retry, and tool errors. They should be expanded with retrieval ranking regression tests, corrupted memory tests, malformed policy tests, file permission errors, and concurrency tests.

## 13. Baseline vs optimized experiment 是否有足夠實驗嚴謹度？

English question:

> Is the baseline versus optimized experiment rigorous enough?

Senior engineer 可能想確認：

- improvement 從 0.96 到 1.00，只修復 1 個 case，是否足夠支持 optimization？
- golden set 是否被用來調參，導致 overfitting？
- 是否應該保留 holdout set？
- latency 差異很小，但在更大 corpus 下是否仍成立？

簡答 中文：

> 對 capstone 來說足夠，因為它有 baseline、optimized、metric delta 和 failure analysis。但它確實是小型實驗，只修復一個明確 retrieval failure。更嚴謹版本會加入 holdout set、更多 threshold cases、不同 policy domains 和 scaling latency tests。

Short answer English:

> It is sufficient for the capstone because it includes a baseline, optimized version, metric delta, and failure analysis. But it is a small experiment that fixes one clear retrieval failure. A more rigorous version would add a holdout set, more threshold cases, more policy domains, and scaling latency tests.

## 14. 如果要上 production，最先要改哪幾個地方？

English question:

> What would you change first before taking this to production?

Senior engineer 可能想確認：

- local JSON memory/audit 要換成可靠儲存。
- retrieval 要支援 policy versioning、access control、larger corpus。
- security 要使用更完整的 PII/secrets detection。
- synthesizer 如果換成 LLM，要加入 grounded prompting、citation verification、output validation。
- tools 若有 side effects，要加入 authorization、idempotency、rate limit、observability。

簡答 中文：

> 我會先改四件事：第一，把 memory/audit 換成可靠且有治理能力的儲存；第二，升級 retrieval 成 hybrid/vector 並加入 policy versioning；第三，強化 PII/secrets/security guardrails；第四，如果使用 LLM，加入 citation verification、output validation 和 observability。

Short answer English:

> I would change four things first: move memory and audit to governed reliable storage, upgrade retrieval to hybrid/vector search with policy versioning, strengthen PII/secrets/security guardrails, and if using an LLM, add citation verification, output validation, and observability.

## 15. 目前的 citation 是否真的能讓使用者驗證來源？

English question:

> Are the current citations enough for users to verify the source?

Senior engineer 可能想確認：

- citation 格式是 `source#doc_id`，但沒有行號或 section anchor。
- 使用者是否能快速找到原文？
- 如果 policy chunk 來自 Markdown section，是否應該顯示 section heading？
- answer 中每一句話是否能對應到具體 citation，還是 citation 只列在整體回答後？

簡答 中文：

> 目前 citation 足以指出來源文件和 chunk，但還不夠理想。更好的做法是 citation 包含 section heading、line number 或 stable anchor，並且讓 answer 的每個主要 claim 都能對應到具體 citation。

Short answer English:

> The current citations identify the source file and chunk, but they are not ideal. A stronger design would include section headings, line numbers or stable anchors, and map each major claim in the answer to a specific citation.

## 快速 Q&A 表

| # | English question | 中文簡答 | Short English answer |
| ---: | --- | --- | --- |
| 1 | Why use a deterministic synthesizer instead of an LLM? | 為了可重現測試與 eval；production 可換 LLM，但要加 citation verification。 | For reproducibility; production can use an LLM with citation verification. |
| 2 | Why lexical retrieval instead of embeddings? | corpus 小且需要可解釋 baseline；大規模時應改 hybrid/vector。 | Small corpus and explainable baseline; use hybrid/vector at scale. |
| 3 | Are boost rules too domain-specific? | 是明確 trade-off，用來修復可量測 failure；長期應用 reranking/metadata。 | Yes, it is a trade-off; long-term use reranking or metadata. |
| 4 | Are guardrails comprehensive enough? | demo 足夠，production 不足，需要更強 PII/secrets 和 red-team。 | Good for demo, not production; needs stronger detection and red-teaming. |
| 5 | Why limited tool authorization? | 現在 tools 低風險；production 每個 tool 都要 permission policy。 | Current tools are low-risk; production needs per-tool permissions. |
| 6 | Is audit log governance-ready? | 不是，只是本機 JSONL；production 要不可竄改與 redaction。 | No, it is local JSONL; production needs immutable logging and redaction. |
| 7 | Does memory create data risks? | 有，production 要 TTL、加密、刪除權、敏感資料分類。 | Yes; needs TTL, encryption, deletion, and classification. |
| 8 | Is `ask()` doing too much? | 目前可接受；功能增加後應拆 pipeline stages。 | Acceptable now; split into pipeline stages as it grows. |
| 9 | Does eval measure quality? | 衡量最低品質門檻，不是完整語意品質。 | It measures a minimum quality bar, not full semantic quality. |
| 10 | Is context recall rigorous? | 是簡化版，應補 precision、faithfulness、semantic recall。 | It is simplified; add precision, faithfulness, and semantic recall. |
| 11 | Is kappa convincing? | workflow 有，但全正例 labels 讓結果過樂觀。 | It shows the workflow, but all-positive labels are optimistic. |
| 12 | Are tests enough? | 覆蓋核心，但要補 retrieval regression 和 file/memory failure。 | Core coverage exists; add retrieval and file/memory failure tests. |
| 13 | Is the experiment rigorous? | capstone 足夠，但應加 holdout 和更多 cases。 | Enough for capstone; add holdout and more cases. |
| 14 | What changes for production? | 可靠儲存、hybrid retrieval、強 guardrails、LLM validation。 | Reliable storage, hybrid retrieval, stronger guardrails, LLM validation. |
| 15 | Are citations verifiable? | 可指出 file/chunk，但應加 section/line/claim mapping。 | Source file/chunk is enough for demo; add section/line/claim mapping. |

## 建議準備的回答方向

如果 presentation 時被問到這些問題，可以用以下方向回答：

- 這是 capstone demo，因此優先重視可重現、可測試與 evaluation clarity。
- 現有設計刻意保持 deterministic，避免外部 API 讓結果不穩定。
- Production 版本會優先升級 retrieval、security、memory/audit persistence 和 LLM grounding。
- Optimized retrieval 的 domain boosts 是一個小型實驗，不是宣稱最終 retrieval 架構。
- Evaluation 已能抓出一個真實 retrieval failure，但 judge/kappa 和 semantic metrics 還有明顯改進空間。

