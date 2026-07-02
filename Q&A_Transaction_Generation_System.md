

------ Question and Answers for TRANSACTION GENERATION SYSTEM ------
### Question 1 - When the contract does not say who orders title
What this is about. Every deal needs to know whether your side or the other side is responsible for ordering the title work. That single answer decides which task you get: an "Order Title" task (your office orders it) or a "Confirm Title Order" task (you follow up to make sure the other side ordered it).
How it works today. The system reads this straight from the contract whenever the contract states it. When the contract is silent and the question was not answered in the wizard, the system does not guess. It leaves it blank and shows a notice on the "Tasks & create" screen: "No title task was generated, confirm who orders title." That way a deal can never quietly launch with no title task.
What we suggest. Keep that honest notice as the safety net, and, if you like, let your brokerage set a default side for the silent case, since most offices have a usual arrangement.
Your call. When the contract does not say who orders title, would you like the system to assume a side by default (and which side: your side or the other side), or keep prompting you to choose each time?

#### Jake: 
```
If it’s not already noted in the contract, let’s ask the user who is inputting the transaction to manually input the answer to this question when they get to the verification screen..
 No need for a brokerage default (because it could end up being incorrect and the user could overlook it)
 ```


### Question 2 - Standard deadline windows when the contract does not list them
What this is about. A few deadlines are counted from a number of days the contract usually spells out: the inspection period, the inspection-response window, the HOA-document delivery window, and the insurance-commitment window.
How it works today. The system uses the number written in the contract. When that number is missing, it does not invent one. It leaves that single deadline undated with a short note, so you can fill it in.
What we suggest. Let your brokerage set standard fallback windows that pre-fill (visibly, so you can still change them) when the contract is silent. As a starting point, in calendar days: inspection 10, inspection response 5, HOA documents 10, insurance commitment 10.
Your call. What standard day counts should we use for your market? Please confirm or adjust the four suggested numbers above.

#### Jake:
```
There should be no standard deadline windows All purchase agreements are different and different things will matter to different agents and different brokerages. It doesn’t make sense to standardize anything because different markets determine different timelines. We need to train AI to recognize these fields better and make recommendations when it’s not 90% confident or above The recommendation would need to be approved by the agent and if it isn’t that confident it should just have a blank there for the agent to fill out during submission.
```

#### Jan:
```
Agreed, and this is already how the system works, so nothing to undo. It does not standardize these windows: it reads the number from the contract, and when the contract is silent it leaves that deadline blank with a note rather than inventing one. It already uses the 90% bar you describe: above it the value is accepted, below it it is surfaced for the agent to confirm, and a value it cannot find is left blank for the agent to fill in. So I will not add standard windows. The real work your answer points to is recognition: training the AI to find these fields more reliably, and showing a borderline read (say 70 to 89%) as a recommendation the agent approves rather than a silent fill. The system already tunes confidence field by field, so I will focus there, on better extraction of the inspection, inspection-response, HOA-document, and insurance windows. 
```


### Question 3 - Appraisal on cash deals
What this is about. Financed deals always include appraisal tasks (ordered, then completed) because the lender requires the appraisal. Cash deals usually have no lender and no appraisal.
How it works today. Cash deals get no appraisal tasks by default.
What we suggest. Keep cash deals appraisal-free by default. If some of your cash buyers do choose to appraise, we add a simple one-click "this cash deal has an appraisal" option on the deal, rather than always creating the tasks.
Your call. Do your cash deals usually involve an appraisal?

#### Jake:
```
AI should be Able to review the contract. Most cash deals or contracts should have something that signifies if the buyer would like an appraisal or not and if it does not have that it should have language in the contract that states whether the buyer would like an appraisal. I believe that AI should be trained to look for that on every cash deal regardless of state.
```

#### Jan: 
```
Agreed, and the right approach. Today the parser reads an appraisal deadline when the contract gives one, but it does not yet read an explicit "buyer elected or waived an appraisal" choice, and the current master list actually attaches a cash appraisal follow-up task to every cash deal by default (a small mismatch with how this guide describes it, worth knowing). I will add an explicit appraisal-election read to parsing on every cash deal and drive the appraisal task from it: elected means the tasks appear, waived means they do not, and silent-or-unsure means we ask the agent rather than guess, using the same confidence-and-confirm machinery as Question 2. One confirmation: when a cash contract is genuinely silent, default to no appraisal task and prompt the agent (my recommendation), or assume one? 
Let’s prompt the agent here. The better our inputs, the better our Agents can correctly work the file.
```


### Question 4 - Calendar days versus business days
What this is about. Some contract deadlines are written in calendar days (every day counts) and some in business days (weekends and holidays are skipped). The two can land on different dates, so it matters which way each deadline is counted.
How it works today. Every deadline is counted in calendar days, and if a deadline happens to land on a weekend or a recognized holiday, it is moved to the next business day.
What we suggest. Switch only the specific deadlines your contracts actually write in business days to count that way. The likely candidates are the inspection-response deadline and the financing or clear-to-close deadline, but we want your confirmation rather than guessing.
Your call. Which of your contract deadlines are written in business days rather than calendar days?

#### Jake:
```
For this question AI should read the contract and determine each deadline independently. Some deadlines should be calendar days and others business days and if no determination is stated definitively in the contract then calendar days will be the default for the timer of the task.
```

#### Jan: 
```
Agreed, and the default you want is already in place: deadlines are counted in calendar days, and one that lands on a weekend or federal holiday rolls forward to the next business day. The piece to add is reading each deadline's basis from the contract. The math for true business-day counting is already built; what the system does not yet do is decide, per deadline, which to use. So I will add a per-deadline read during parsing, calendar versus business, defaulting to calendar (rolled forward) when the contract is silent, exactly as you describe. One wording confirmation: for a calendar-day deadline that lands on a Saturday, I recommend still rolling it to the next business day (a deadline you cannot act on is not useful), reserving true business-day counting for deadlines the contract writes that way. 
```


#### Jake:
```
It must be calendar days. Unlike most typical business practices, real estate timelines can end on holidays and weekends, so we shouldn’t roll anything. The hot button is to default to calendar days always. If a timeline hits too early that is way better than hitting later and missing our deadline for any item for a client.

Most of the time, all timelines are based on calendar days unless specifically stated by the contract or written in by an agent.
```


### Question 5 - Which states to support next
What this is about. Closings work differently from state to state. In title-company states (such as Indiana, your primary market) the title company runs the closing. In attorney-closing states (for example New York, Georgia, or South Carolina) an attorney is involved and the task list is different.
How it works today. The system is set up for title-company states, with Indiana fully supported. The attorney-state tasks (attorney review period, attorney-ordered title, attorney closing) are not built yet.
What we suggest. Build the attorney-state workflow once you tell us which states your next brokerages are in, so we model the right one first instead of guessing.
Your call. Which states are your next brokerages in, and are there any attorney-closing states you would like supported first?

#### Jake:
```
We’re not building this to expand our brokerage into other states we are building this to sell to other brokerages to for Sale by owners to attorneys and attorney states So what we need to build is something that is usable for all 50 states. Let’s focus on the attorney closing states to build out those task lists using our existing lists and justice modifying them for attorneys versus title companies. If you have questions on any of the tasks and how they would relate to attorney states let us know and we will build those out for you.
```

#### Jan:
```
Understood. That reframes this from "which states do we expand into" to "make the product sell into all 50 states, attorney states included," and the build is set up for it. The product already knows which states are attorney versus title-company, already has the switch that selects an attorney workflow over a title-company one, and the parser already reads whether a deal closes through an attorney or a title company. What is missing is the attorney task content: today's master list is title-company and Indiana shaped, with no attorney tasks yet. So your instruction, adapt the existing lists for attorneys versus title companies, is the lowest-risk path: clone the title-company list, swap the steps a title company runs (ordering title, scheduling and running the closing, disbursing) for the attorney equivalents (attorney review and approval period, attorney orders the title commitment, attorney conducts closing and disbursement), tag them to the attorney workflow, and the existing switch selects them by state or by what the contract says. Closing practice nationwide is really these two patterns plus state-specific disclosure forms, so "all 50 states" is two base workflows plus per-state form differences, not fifty hand-built lists.
A few task questions so I can build the attorney list accurately (you offered):
- In attorney states, is the title commitment ordered by the attorney, or does an agent still order title and the attorney reviews it?
- Is there a formal attorney-review or approval period to model as its own deadline (for example the New York and New Jersey "attorney review," often around 3 business days), counted from contract acceptance?
- Who runs the closing and disburses funds: the attorney alone, or an attorney plus a title or settlement agent?
- Are there attorney-state steps with no title-company equivalent (for example an attorney opinion of title, or an attorney-prepared deed) that I should add rather than swap?
- For the for-sale-by-owner and attorney-direct customers you mentioned, does anything change versus a brokerage in who each task is assigned to?
```

#### Jake:
```
QUESTION #5 GUIDANCE

Hey Jan, I totally cheated and used AI, but honestly, if I hadn’t, you may not have received a response until 2027. 🙂

Also, I will email you an excel workbook you can utilize as a matrix similar to our original task workbook.

SUMMARY:
Here’s how it mapped:
Who orders title in attorney-controlled states?
 Answered under: “In attorney-controlled states, who orders title?”
 Conclusion: In NC, SC, GA, and DE, default ownership should sit with the attorney or attorney-controlled closing office, not the agent.
Is there a formal attorney-review deadline?
 Answered under: “Is there a formal attorney-review deadline?”
 Conclusion: NJ has a verified 3-business-day attorney-review model in certain licensee-prepared contracts. NY is contract-language-driven. NC, SC, GA, and DE should not get a default attorney-review deadline unless the contract creates one.
Who runs closing and disburses funds?
 Answered under: “Who runs closing and disburses funds?”
 Conclusion: In attorney-controlled states, closing control belongs to the attorney, though nonlawyers may perform some ministerial or settlement functions depending on the state.
Are there attorney-state steps with no title-company equivalent?
 Answered under: “Are there attorney-state steps with no title-company equivalent?”
 Conclusion: Yes. Add attorney-specific steps like title opinion, attorney title review, curative work, deed prep/review, recording authorization, and disbursement supervision.
Does FSBO or attorney-direct change task assignment versus brokerage?
 Answered under: “Does FSBO or attorney-direct change task assignment versus brokerage?”
 Conclusion: Yes. Brokerage/agent tasks get reassigned to the customer or attorney, but attorney-required legal/title/closing tasks stay intact.

DETAILED VERSION:
For North Carolina, South Carolina, Georgia, and Delaware, based on the sources verified.
In this cluster, do not assign title ordering or closing ownership to the real estate agent. Assign the legal-title and closing-control tasks to the attorney or attorney-controlled closing office.
North Carolina requires the legal closing work to be handled by a North Carolina attorney. The North Carolina State Bar lists residential closing functions including review of the purchase agreement, abstracting title, giving an opinion on title, applying for title insurance, preparing deeds/deeds of trust, resolving title issues, recording, disbursing when legally permitted, and giving a post-closing final title opinion. North Carolina law also says title insurance cannot be issued for North Carolina real estate until the title insurer has obtained the opinion of a licensed North Carolina attorney who conducted or supervised a reasonable title examination.
South Carolina should be modeled as attorney-supervised across five legal components: abstracting title, preparing documents, closing, recording, and disbursing. A South Carolina Bar ethics opinion says lawyer supervision must involve review of the work itself, not just taking a nonlawyer’s word for it, which is useful for your software logic because “checked box says attorney supervised” should not be enough.
Georgia should be modeled as attorney-controlled from beginning to end. The Georgia Supreme Court approved the rule that only a licensed Georgia attorney may close a real estate transaction or prepare/facilitate execution of a deed of conveyance, and the State Bar of Georgia’s 2025 formal advisory opinion says the lawyer must control the closing process from beginning to end.
Delaware should be modeled as attorney-conducted closing. Delaware’s Supreme Court approved guidance requiring a Delaware attorney to conduct closings for sales and refinances, participate directly or in a supervisory capacity in drafting or reviewing title-transfer documents, examine title, remove exceptions, supervise disbursement, and answer legal-effect questions.
Cluster 2: Attorney-review / mixed title-company workflow
Use this cluster for New Jersey and New York.
Do not treat New Jersey or New York as “attorney-only title company replacement” states. They are better modeled as attorney-review and attorney-representation states where title companies/title agents still commonly appear in the workflow.
New Jersey has the clearest formal attorney-review clock: if a real estate licensee prepares the contract, the contract must include an attorney-review clause giving buyer and seller three business days from delivery of the completely signed contracts to consult an attorney; the attorney may propose revisions or void the contract. New Jersey’s own consumer guide also says settlement statements are prepared by the title company, most closings involve lawyers, a title clerk, and lender representatives, funds may be disbursed by the attorney or closing agent, and deed/mortgage recording is usually done by the title agent or attorney.
New York does not support a universal statewide three-business-day attorney-review deadline from the sources I verified. NYSBA says if a broker prepares a contract, it is usually subject to attorney approval within a specified short time. The New York Court of Appeals treats attorney-approval contingencies according to the contract language, meaning your system should only create that deadline when the contract actually contains it. NYSBA also says a buyer’s attorney generally orders a title report from a title insurance company, while some upstate attorneys examine records or abstracts and give a title opinion or issue title insurance.
1. In attorney-controlled states, who orders title?
For North Carolina, South Carolina, Georgia, and Delaware, model the attorney as the workflow owner for title-related legal work. The agent should not be the default owner of “order title” in these workflows.
More precise version:
In North Carolina, use “Attorney orders/initiates title search and prepares title opinion/title insurance request.” Title insurance requires a North Carolina lawyer’s title opinion, and the State Bar treats title abstracting, title opinion, title insurance application, curative work, and final title opinion as legal closing functions.
In South Carolina, use “Attorney orders, reviews, or supervises title search/abstract and title commitment.” A title company may be involved mechanically, but South Carolina requires lawyer supervision of title abstracting and other closing components. So the task owner should be attorney, not agent.
In Georgia, use “Closing attorney/law firm handles title and closing coordination.” The sources I verified support attorney control of the closing process and attorney involvement in deed/conveyance execution. I would not assign title-ordering to the agent in Georgia.
In Delaware, use “Attorney examines title and clears exceptions.” The Delaware source specifically makes attorney participation necessary for examining title and removing title exceptions.
Product rule: the agent task should be “confirm closing attorney selected and send executed contract”, not “order title.”
2. Is there a formal attorney-review deadline?
For the attorney-controlled closing cluster, I would not create a default attorney-review deadline unless the contract itself creates one.
For North Carolina, South Carolina, Georgia, and Delaware, I verified attorney-controlled closing/title functions, but I did not verify a standardized statewide attorney-review period counted from contract acceptance. So do not create a generic “3-day attorney review” deadline for those states. Add a normal “attorney contract review” task, but not a hard statutory/form deadline unless the uploaded contract contains that clause.
For New Jersey, yes. Build a specific deadline when the contract is prepared by a real estate licensee: Attorney Review Deadline = 3 business days from delivery of fully signed contracts. Do not merely count from “acceptance,” because the New Jersey guide ties it to delivery of completely signed contracts.
For New York, build this as a contract-detected deadline, not a state-default deadline. If the contract says “subject to attorney approval within X days,” create that deadline. If the contract does not contain attorney approval language, do not invent it. NYSBA describes attorney approval as typical when a broker prepares the form, and the New York Court of Appeals enforces the attorney-approval contingency according to its own terms.
3. Who runs closing and disburses funds?
For your attorney-controlled cluster, assign closing control to the attorney.
In Delaware, assign both “conduct closing” and “supervise disbursement” to the Delaware attorney. That is directly supported.
In Georgia, assign “conduct/control closing” to the Georgia closing attorney. I would label funds movement as attorney-controlled disbursement workflow unless your state-specific legal review confirms a more precise statutory disbursement rule. The safe product workflow is not “title company runs closing.” It is “attorney controls the closing process from beginning to end.”
In North Carolina, assign legal closing work to the North Carolina attorney, but your system can allow ministerial signing/funds tasks to be performed by nonlawyers only where legally permitted. The State Bar says a nonlawyer may present documents, direct signatures, and receive/disburse funds as long as the nonlawyer does not perform legal closing services. Still, the legal owner remains the attorney.
In South Carolina, assign the five core components to attorney supervision, including disbursement. The South Carolina Bar notes that supervision over disbursement may involve outside nonlawyer activity, but the lawyer’s supervision obligation remains serious and cannot rest on blanket assurances.
New Jersey and New York should not use this same model. New Jersey expressly contemplates the attorney or closing agent disbursing funds and the title agent or attorney recording documents. New York commonly involves attorneys, title closers/title companies, lender counsel, and sometimes bank/title-company preparation of closing statements.
4. Are there attorney-state steps with no title-company equivalent?
Yes. Build these as additional attorney/legal workflow steps, not simple title-company replacements.
Add these attorney-specific tasks for the attorney-controlled cluster:
Attorney engagement confirmed.
Attorney representation/scope confirmed.
Attorney receives executed contract.
Attorney reviews contract for legal conditions and closing requirements.
Attorney orders or supervises title search/abstract.
Attorney reviews title results.
Attorney issues title opinion or title certificate where applicable.
Attorney resolves title defects, liens, exceptions, payoff issues, and curative items.
Attorney prepares or reviews deed and transfer documents.
Attorney prepares or reviews mortgage/deed of trust documents where applicable.
Attorney confirms legal authority to record.
Attorney supervises execution/signing.
Attorney authorizes or supervises recording.
Attorney authorizes or supervises disbursement.
Attorney completes post-closing title opinion/final title work where applicable.
North Carolina especially needs the extra “preliminary/final title opinion” logic because the State Bar and statute support that title-opinion structure. South Carolina needs “supervise five legal components.” Georgia needs “attorney controls closing and deed execution.” Delaware needs “attorney conducts closing, reviews transfer documents, examines title, clears exceptions, and supervises disbursement.”
5. Does FSBO or attorney-direct change task assignment versus brokerage?
Yes, but only at the brokerage layer. The attorney-controlled legal requirements do not disappear just because no agent is involved.
For FSBO in attorney-controlled states, assign brokerage-style tasks to the seller, buyer, or attorney. Do not assign them to an agent placeholder. The attorney still owns the legal title/closing steps.
For attorney-direct customers, push the workflow even more heavily toward attorney ownership. Contract preparation/review, title, deed, closing, recording, and disbursement supervision should sit with attorney roles. The customer’s tasks should be practical items: provide property details, upload contract/draft terms, provide payoff info, choose attorney, send ID, provide wiring instructions through secure process, complete disclosures, schedule inspections, and approve closing statement.
For New Jersey FSBO/attorney-direct, be careful. If a real estate licensee prepares the contract, the three-business-day attorney-review clause is required. If no licensee prepares it, do not automatically assume the same attorney-review deadline. That one distinction matters, because software loves making one wrong assumption at scale like a tiny compliance chainsaw.
For New York attorney-direct, the flow often starts earlier with attorneys before a binding contract is signed, especially downstate where NYSBA says the seller’s attorney usually prepares the contract. In that case, model “attorney drafts/reviews contract before execution” rather than “contract accepted, then attorney review starts.”
Recommended workflow logic
Use these rules:
For NC / SC / GA / DE:
 Default title/closing owner = Attorney.
 Default agent role = coordination only, if an agent exists.
 No default attorney-review deadline unless contract language creates one.
 Add attorney-specific legal tasks.
For NJ:
 Default contract review deadline = only when real estate licensee prepared contract.
 Deadline = 3 business days from delivery of completely signed contracts.
 Closing may involve attorney plus title/closing agent.
 Do not treat as attorney-only.
For NY:
 Attorney approval deadline = only if contract contains approval contingency.
 Title report often ordered by buyer’s attorney from title company.
 Closing may involve attorney plus title company/title closer/lender attorney.
 Do not treat as attorney-only.
For FSBO / attorney-direct:
 Remove broker/agent tasks or reassign them to customer/attorney.
 Keep attorney-required legal tasks intact.
 Add “confirm who represents whom” because the closing attorney may not represent every party, and people will absolutely assume the opposite unless the workflow prevents it.

 
#### Attorney Title workflow matrix:

##### Overview
 Coldwell Banker Stiles - Attorney / Title Workflow Workbook							
Developer-ready workflow summary for attorney-controlled, attorney-review, mixed title, FSBO, and attorney-direct real estate transaction logic. This is conservative by design and does not classify every state until verified.							
							
Primary product use case	Velvet Elves transaction workflow design						
Key warning	Do not use a single “attorney state” yes/no flag. Use state workflow flags and contract-detected deadlines.						
Included state clusters	NC, SC, GA, DE, NJ, NY, plus unverified/do-not-classify-yet bucket						
Not included	A complete 50-state verified matrix. This workbook only includes sourced clusters from the prior analysis.						
							
							
Cluster	Core Product Rule						
NC / SC / GA / DE	Attorney owns legal/title/closing workflow. Agent/customer coordinates only. No default attorney-review deadline unless contract creates one.						
NJ	Create 3-business-day attorney-review deadline only when licensee-prepared contract rule applies. Keep title company and closing-agent roles.						
NY	Create attorney-review deadline only from contract language. Support both attorney-title-opinion and title-company-title-insurance paths.						
FSBO	Remove brokerage tasks. Reassign coordination to customer. Keep attorney-required tasks intact.						
Attorney-direct	Attorney becomes primary workflow owner earlier. Customer handles intake, approvals, documents, funds, and scheduling tasks.						
Other states	Do not classify until verified. Use standard title/settlement workflow.						
							

##### Attorney / Title Workflow Matrix
Attorney / Title Workflow Matrix							
Main build matrix. Use this as the high-level state-cluster decision table before assigning tasks.							
							
State Cluster	States	Title Ordered By	Attorney Review Deadline	Closing Run By	Funds Disbursed By	Special Attorney Tasks to Add	FSBO / Attorney-Direct Difference
Attorney-controlled legal-title workflow	North Carolina	Default owner: North Carolina attorney. Agent task should be “Confirm closing attorney selected and send executed contract,” not “Order title.” NC treats title abstracting, title opinion, title insurance application, deed prep, curative work, recording, and final title opinion as attorney legal-closing functions.	No default statewide attorney-review clock verified. Create only if contract language creates one.	Attorney controls legal closing services. Nonlawyers may perform limited ministerial tasks only where allowed.	May be handled ministerially in limited situations, but legal determinations stay in attorney-controlled workflow.	Attorney title abstract; preliminary title opinion; title insurance application; deed/deed of trust prep or review; curative work; recording authorization; cancellation of prior deed of trust; final title opinion.	FSBO does not remove attorney workflow. Reassign agent coordination to customer. Add attorney representation/scope confirmation.
Attorney-supervised five-part closing workflow	South Carolina	Attorney owns or supervises title abstract/title review. Nonlawyer/title vendor may assist, but attorney supervision should be required.	No default statewide attorney-review clock verified. Create only if contract language creates one.	Attorney supervision applies to title abstracting, document preparation, closing, recording, and disbursement.	Lawyer-performed or lawyer-supervised. Disbursement is part of attorney-supervised closing workflow.	Attorney supervision checklist for title, documents, closing, recording, and disbursement. Capture “attorney reviewed work product,” not just a checkbox.	FSBO changes coordination owner only. Customer uploads contract/details; attorney handles supervised title/closing tasks.
Attorney-controlled closing and deed workflow	Georgia	Default owner: Georgia closing attorney/law firm. Do not assign “order title” to agent as primary task.	No default statewide attorney-review clock verified. Create only if contract language creates one.	Licensed Georgia attorney must close the real estate transaction.	Model as attorney-controlled closing disbursement. Have Georgia counsel validate exact escrow/disbursement mechanics before hardcoding.	Georgia attorney closing control; deed preparation/facilitation; title/legal instrument review; title opinion/validity workflow where applicable.	FSBO still needs attorney-controlled closing workflow. Customer replaces agent coordination tasks. Attorney remains closing owner.
Attorney-conducted closing workflow	Delaware	Default owner: Delaware attorney. Attorney examines title and handles title exceptions.	No default statewide attorney-review clock verified. Create only if contract language creates one.	Delaware attorney conducts closings for sales/refinances secured by Delaware real estate.	Delaware attorney supervises disbursement.	Attorney review/drafting of title-transfer and security documents; attorney title examination; removal of exceptions; attorney-supervised disbursement; legal-effect questions routed to attorney.	FSBO or attorney-direct does not remove attorney closing requirement. Customer handles intake/upload/approval tasks. Attorney owns title/document/closing/disbursement-supervision tasks.
Attorney-review plus title-company / closing-agent workflow	New Jersey	Do not model as attorney-only. Title companies/title clerks/title agents remain part of the workflow. Attorney reviews and negotiates legal terms; title company may prepare settlement statement and support title/closing functions.	Yes, in verified scenario: when a real estate licensee prepares the contract, attorney review is 3 business days from delivery of completely signed contracts.	Mixed workflow. Closings may involve lawyers, title clerk, lender representative, agents, buyer, and seller.	Funds may be disbursed by attorney or closing agent. Recording usually by title agent or attorney.	Attorney-review deadline; attorney notice/revision/void workflow; title company settlement statement task; closing-agent/title-agent recording task; attorney representation disclosure.	If FSBO and no real estate licensee prepared the contract, do not automatically create the 3-business-day deadline. Use contract detection.
Attorney-practice / contract-detected review workflow	New York	Do not model as attorney-only. NY varies by region. Support attorney abstract/title opinion or title company/title insurance path.	No universal default verified. Create only if contract contains attorney-approval language, using the contract’s stated time period.	Mixed attorney/title/lender workflow. Seller’s attorney or agent may prepare documents; buyer’s attorney reviews documents before closing.	Do not hardcode universal disbursement owner from this research. Use transaction-specific instructions and selected settlement/title/attorney roles.	Contract-detected attorney approval deadline; attorney contract review before execution where applicable; title pathway selection: attorney abstract/title opinion or title company/title insurance.	Attorney-direct may start earlier, especially where seller’s attorney prepares contract before execution. Do not model as accepted-contract-then-review unless contract says that.
Unverified / do-not-classify-yet states	All other states	Do not classify as attorney-only from this research. Use normal title/settlement workflow until validated.	No default deadline unless contract or state-specific rule is verified.	Use selected settlement provider, title company, escrow, or attorney based on validated local workflow.	Use selected settlement provider/title/escrow/attorney based on validated local workflow.	Add no attorney-only tasks unless verified.	FSBO removes brokerage tasks, but does not automatically make it attorney-controlled. Validate state before changing task ownership.




##### Recommended Workflow Flags
Recommended Workflow Flags							
Use flags instead of one “attorney state” toggle. One toggle is tidy, simple, and wrong. A rare trifecta.							
							
Workflow Flag	Type / Values	Default Logic	Notes				
requires_attorney_closing_control	true / false	true for NC, SC, GA, DE	Attorney must conduct, control, perform, or supervise core legal closing functions.				
requires_attorney_title_opinion_or_exam	true / false	true for NC and DE; validate by state for others	Used to add title opinion/exam tasks beyond standard title company workflow.				
requires_attorney_supervised_disbursement	true / false	true for SC and DE; conservative attorney-controlled for NC/GA	Use “attorney-supervised” where exact mechanics differ.				
has_default_attorney_review_period	true / false	true only for verified NJ scenario	Do not make NY or attorney-controlled states default review states.				
attorney_review_trigger	delivery of signed contract / contract clause / none	NJ: delivery of completely signed contracts when licensee-prepared; NY: contract clause	Avoid “from acceptance” unless source or contract says so.				
title_company_role_allowed	none / support role / settlement role / standard role	Support role in attorney-controlled states; mixed role in NJ/NY	Avoid falsely removing title companies from states that still use title/title insurance vendors.				
agent_orders_title_default	true / false	false for NC/SC/GA/DE	Agent should coordinate provider selection and document transfer, not own legal title work.				
fsbo_reassigns_agent_tasks_to_customer	true / false	true	FSBO changes coordination ownership, not legal requirements.				
							

##### State-Specific Logic Rules

State-Specific Logic Rules							
Detailed trigger/action logic for the verified clusters. These are better for developer implementation than narrative descriptions.							
							
State / Cluster	Trigger	System Action	Default Owner	Important Constraint			
NC	State = North Carolina	Set attorney-controlled legal/title/closing workflow	Attorney	Do not default agent to “order title.”			
NC	Contract uploaded	Create task: send executed contract to closing attorney	Agent or customer	FSBO/customer gets task if no agent exists.			
NC	Title work starts	Create title abstract/title opinion/title insurance application tasks	Attorney	Title insurance requires attorney title opinion per NC authority.			
SC	State = South Carolina	Enable five-part attorney supervision workflow	Attorney	Title, documents, closing, recording, and disbursement.			
SC	Nonlawyer/vendor assists	Create attorney review/supervision checkpoint	Attorney	Do not rely only on nonlawyer representation that work was done.			
GA	State = Georgia	Enable Georgia attorney closing-control workflow	Attorney	Licensed Georgia attorney must close transaction.			
GA	Deed/conveyance documents needed	Assign deed preparation/facilitation to attorney	Attorney	Do not assign deed execution facilitation to nonlawyer by default.			
DE	State = Delaware	Enable attorney-conducted closing workflow	Attorney	Attorney conducts closing and supervises disbursement.			
DE	Title exceptions found	Assign exception removal/review to attorney	Attorney	Legal-effect questions route to attorney.			
NJ	Contract prepared by real estate licensee	Create attorney-review deadline	Buyer/seller attorneys	3 business days from delivery of completely signed contracts.			
NJ	Closing setup	Keep title company/title clerk/title agent/closing agent roles available	Attorney + title/closing agent	Do not model NJ as attorney-only.			
NY	Contract contains attorney approval clause	Create attorney approval deadline from contract language	Attorney	No universal default clock.			
NY	Title pathway selected = attorney abstract/opinion	Assign title exam/opinion to attorney	Attorney	Path varies by region/transaction.			
NY	Title pathway selected = title company/title insurance	Assign title report/search to title company/title agent and review to attorney	Title company + attorney	Do not force one NY workflow.			
Other states	State not verified	Use standard title/settlement workflow	Selected provider	Do not classify as attorney-controlled until validated.			
							

##### Attorney-Specific Task Library
Attorney-Specific Task Library							
Use this tab to add tasks rather than blindly swapping a title company task for an attorney task.							
							
Task Category	Task Name	Default Owner	Applies To	Add / Swap / Conditional	Notes		
Engagement	Confirm attorney selected	Agent or customer	NC, SC, GA, DE, FSBO/attorney-direct	Add	Coordination task only.		
Engagement	Confirm attorney representation/scope	Attorney + customer	All attorney workflows; especially FSBO/attorney-direct	Add	Clarifies who the attorney represents.		
Contract	Send executed contract to attorney	Agent or customer	NC, SC, GA, DE	Add	Replaces “send to title” as the default coordination task in attorney-controlled states.		
Contract	Attorney contract review	Attorney	All attorney workflows where applicable	Conditional	Deadline only if state/contract creates one.		
Title	Order or supervise title search/abstract	Attorney	NC, SC, DE; GA validate local mechanics	Add	Attorney may use staff/vendor, but workflow owner remains attorney/supervising attorney.		
Title	Issue preliminary title opinion or title certificate	Attorney	NC; selected attorney-title-opinion pathways	Add	No direct title-company equivalent.		
Title	Review title results and exceptions	Attorney	NC, SC, DE, selected NY pathways	Add	Attorney legal review step.		
Title	Resolve title defects / curative work	Attorney	NC, SC, DE; as needed in all attorney workflows	Add	May involve liens, payoffs, corrections, exceptions.		
Insurance	Apply for or coordinate title insurance	Attorney or title/settlement role by state	NC, mixed states	Conditional	NC requires attorney opinion before title insurance issued.		
Documents	Prepare or review deed	Attorney	NC, SC, GA, DE; NY/NJ as applicable	Add	Especially important for GA and DE.		
Documents	Prepare or review deed of trust/mortgage/security documents	Attorney	NC, SC, DE; as applicable	Add	Do not assign legal drafting to agent.		
Closing	Conduct or control closing	Attorney	NC, SC, GA, DE	Add	May include supervised staff, but attorney is legal owner.		
Funds	Authorize or supervise disbursement	Attorney	SC, DE; conservative for NC/GA	Add	Use state-specific counsel before over-hardcoding mechanics.		
Recording	Authorize, perform, or supervise recording	Attorney	NC, SC, DE; mixed states as applicable	Add	NJ may also involve title agent.		
Post-closing	Final title opinion / final title work	Attorney	NC and selected attorney-title-opinion workflows	Add	No direct title-company-equivalent in the workflow.		
							

##### FSBO and Attorney-Direct Assignment Rules							
FSBO removes brokerage tasks. It does not erase attorney-required legal/title/closing tasks. Humanity tried, statutes objected.							
							
Brokerage Workflow Task	FSBO / Attorney-Direct Replacement	Owner in FSBO	Owner in Attorney-Direct	Notes			
Agent confirms attorney/title provider	Customer confirms attorney/title provider	Customer	Customer + attorney	System should prompt provider selection early.			
Agent sends contract	Customer uploads/sends contract	Customer	Customer	System should collect signed contract and route to attorney.			
Agent tracks title/closing milestones	System tracks attorney/customer milestones	System + customer	System + attorney	Customer sees status, attorney owns legal steps.			
Agent reminds parties of deadlines	System reminders to customer and attorney-facing users	System	System	Deadline logic must be state/contract-specific.			
Agent coordinates signatures	Attorney/customer coordinates signatures depending on state	Customer + attorney	Attorney	Do not let system assign legal execution control to customer where attorney required.			
Agent follows up on title issues	Attorney owns title/legal issues; customer receives status updates	Attorney	Attorney	Customer should not be tasked with legal curative work.			
Agent confirms closing package	Attorney/closing office confirms closing package	Attorney or closing office	Attorney	Use title/closing agent role only in mixed states.			
Agent explains process to client	System gives plain-English status explanation; attorney handles legal advice	System + attorney	System + attorney	Keep software educational, not legal advice.			
							


##### Attorney Review Deadline Logic
Attorney Review Deadline Logic							
Create attorney-review deadlines only where verified by state rule or contract language. Do not manufacture deadlines because the word “attorney” showed up.							
							
State / Cluster	Default Deadline?	Trigger	Start Date	Deadline Length	Implementation Note		
NC	No	Contract language only	Use contract-defined start if present	Use contract-defined period	No verified statewide post-acceptance attorney-review period from this research.		
SC	No	Contract language only	Use contract-defined start if present	Use contract-defined period	No verified statewide post-acceptance attorney-review period from this research.		
GA	No	Contract language only	Use contract-defined start if present	Use contract-defined period	No verified statewide post-acceptance attorney-review period from this research.		
DE	No	Contract language only	Use contract-defined start if present	Use contract-defined period	No verified statewide post-acceptance attorney-review period from this research.		
NJ	Yes, only when licensee-prepared contract rule applies	Real estate licensee prepared contract requiring attorney-review clause	Delivery of completely signed contracts	3 business days	Do not blindly use acceptance date. Use delivery of fully signed contracts.		
NY	No universal default	Attorney-approval clause detected in contract	Use contract-defined start	Use contract-defined period	Contract detection required.		
Other states	No	Verified state rule or contract language only	Use verified rule/contract	Use verified rule/contract	Do not create state default without validation.		
					

##### Sources and Verification Notes							
Plain-text URLs are included for source traceability inside the workbook.							
							
Jurisdiction / Topic	Source Name	URL	Supports	Verification Note			
North Carolina	North Carolina State Bar - Authorized Practice Advisory Opinion 2002-1	https://www.ncbar.gov/for-lawyers/ethics-and-governing-rules/ethics-opinions/opinions/authorized-practice-advisory-opinion-2002-1/	Attorney legal-closing functions; title opinion/title insurance relationship; allowed nonlawyer ministerial functions	Used for NC attorney-controlled legal/title workflow.			
South Carolina	South Carolina Bar Ethics Advisory Opinion 09-01	https://www.scbar.org/for-lawyers/quicklinks/legal-resources/ethics-advisory-opinions/ethics-advisory-opinion-09-01/	Attorney supervision over title abstracting, documents, closing, recording, disbursement	Used for SC five-part attorney supervision workflow.			
Georgia	Georgia Supreme Court / Justia case record	https://law.justia.com/cases/georgia/supreme-court/2003/s03u1451-1.html	Licensed Georgia attorney must close transaction; deed conveyance limitations	Used for GA attorney-controlled closing and deed workflow.			
Delaware	Delaware Supreme Court / ODC Digest download	https://courts.delaware.gov/ODC/Digest/Download.aspx?id=419	Attorney-conducted closing; title examination; document review; exception removal; disbursement supervision	Used for DE attorney-conducted workflow.			
New Jersey	New Jersey DOBI Consumer Guide: Buying a Home	https://www.nj.gov/dobi/division_consumers/pdf/buyingahome.pdf	3-business-day attorney review when licensee-prepared contract; mixed attorney/title/closing workflow	Used for NJ attorney-review plus title-company/closing-agent workflow.			
New York	New York State Bar Association - Legal Ease: Buying and Selling Real Estate	https://nysba.org/legalease-buying-and-selling-real-estate/	Attorney approval where contract provides; buyer attorney/title company title report path; regional variation	Used for NY contract-detected review and mixed title pathway.			
RESPA guardrail	Cornell Legal Information Institute - 12 U.S.C. § 2608	https://www.law.cornell.edu/uscode/text/12/2608	Seller cannot require buyer to buy title insurance from a particular title company in covered transactions	Used as provider-selection compliance guardrail.			
							
							

```
 ----------------- Question and Answers for TRANSACTION GENERATION SYSTEM ---------------------