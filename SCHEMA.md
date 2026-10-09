# Zotero Library Classification Schema

- **Version:** v1.7 (2026-10-09)
- **Source of truth:** [`ontology.yaml`](ontology.yaml) defines the tag vocabulary, tag hierarchy (parent → child), collection scopes and boundaries, and domain defaults. This document explains the principles and rules behind it.
- **Checker:** `tools/check_schema.py` (read-only, see §6).

The collection tree and vocabulary below are those of the original library (biomedical AI). The principles and rules apply to any field; the onboarding agent tailors `ontology.yaml` to a new library (see README).

### Changelog
- **v1.7:** Added `00_MyPublications` as a "view" collection (`views` in `ontology.yaml`): the user's own papers also sit here besides their one home collection. The checker ignores it when counting homes (E1/E2).
- **v1.6:** Dropped tag numbers (`m:1104 GAN` → `m:GAN`). Groups became parent tags that are applied to papers: a paper with a child tag must also carry its parent tag (H1, e.g. `m:GAN` + `m:generative`). Group Saved Searches now match the parent tag exactly (`tag is m:generative`) and are named after it. Renamed the `d:` group `clinical` to `clinical-data` (it clashed with the `d:clinical` tag). The single-group axes `type:` and `a:` have no parent tag. Checker: E4 is now "child tag without its parent tag"; new E8 flags leftover numbered tags.
- **v1.5:** Added the `lab:` axis (closed vocabulary of 6 labs named by PI surname, tagged when the PI is an author).
- **v1.4:** Added the `model:` axis (open vocabulary), the `00_Inbox` staging collection and its triage procedure, and TL;DR notes.
- **v1.3:** Added 7 user-specified exception tags: `t:fairness`, `t:anomaly-detection`, `m:data-augmentation`, `m:noisy-imbalanced-labels` (new group m:20 data-centric), `t:GRN`, `d:cytology`, `t:registration`.
- **v1.2:** Widened collection 40. Added the placement rule for interpretability studies and widened x9_General to cover experimental techniques and resources. Restricted `t:classification`.
- **v1.1:** Introduced tag numbering and the ontology (axis → group → tag). Expanded the vocabulary and relaxed per-axis tag limits. Added domain-default omission (T5) and boundary rules.
- **v1:** Initial agreement.

## 0. Core principles

1. **Collections use exactly one axis:** `domain → problem` (what problem the paper tries to solve).
2. **Method, data/modality, task, paper type and disease/biology area are tags,** never collections.
3. **Each paper has exactly one home collection:** a single leaf of the domain tree. `00_Inbox` is the only exception (§3). `00_MyPublications` is an extra view, not a home (§3).
4. **No duplicate items.** To show a paper in several places, add the same item to more collections (macOS: drag adds, Cmd+drag moves).
5. **Tags form a two-level hierarchy (parent → child).** A paper with a child tag always carries its parent tag too, so a group is browsed by clicking its parent tag or through the Saved Search of the same name. Cross-axis views are Saved Searches.
6. Deciding question: *"What problem does this paper's main contribution solve?"* → home collection. Everything else is a tag.

> Example: a paper that combines ST and H&E with prototype MIL to predict survival
> → home `13_HistologyToMolecular` / tags `m:set-aggregation` `m:prototype` `m:MIL` `d:spatial-omics` `d:ST` `t:clinical-prediction` `t:survival`
> (`d:H&E` is the pathology domain default, so it is omitted.)

---

## 1. Collection tree

Scopes, exclusions and boundary rules live in the `collections` section of `ontology.yaml`.

```
00_Inbox                     Staging area for new papers (§3)
00_MyPublications            View of the user's own papers; they also have a home below (§3)
10_Pathology/
  11_FoundationModels · 12_SlideRepresentation · 13_HistologyToMolecular
  14_LanguageReportsAgents · 15_Robustness · 16_CellLevel
  17_ImagingInfra · 18_DataBenchmarks · 19_General
20_SingleCell_Spatial/
  21_FoundationModels · 22_Integration_BatchEffect · 23_Cytometry_Clinical
  24_Perturbation_VirtualCell · 29_General
30_Molecules_Drugs/
  31_Design_Optimization · 32_Interaction_Binding · 33_Property_Representation · 39_General
40_Clinical_Population       (leaf)
50_BioSequenceFMs            (leaf)
90_Methods/
  91_Architectures_SSL_Generative · 92_Multimodal_VLM · 93_LLMs · 99_General
```

### Key boundary rules (full list in `ontology.yaml`)
- **11 vs 12:** An encoder pretrained for general use without task labels → 11. A model trained or tuned for specific labels → 12.
- **11 vs 13:** Molecular data used only as a pretraining signal to build a general encoder → 11. Output is a molecular prediction → 13.
- **13 vs 14:** 14 only when the output is text or the model is conversational / VQA / agentic. Survival prediction that fuses reports stays in 13 with `d:text`.
- **x9_General vs topic collections:** Reviews and perspectives go in the topic collection with a `type:` tag. x9 holds only papers covering the whole domain.
- **18 vs topic collections:** A benchmark for a specific problem goes in that problem's collection with `type:benchmark`. 18 holds only general-purpose resources not tied to one problem.
- **Domain vs 90_Methods:** An LLM or agent working on one domain's data → that domain. Cross-domain or general-purpose → 93.
- **Interpretability studies:** Place them with the model being interpreted and add `t:interpretability` (pathology FM interpretation → 11, MIL explanation → 12).
- **Experimental techniques, databases, QC tools:** The domain's x9_General, with `type:non-ML` or `type:tool`.
- **Domains without a home yet** (here: non-pathology medical imaging): place by method in 9x and track with a `d:` tag (`d:medical-image`) until C4 is met.

---

## 2. Tag system

### Format: `<axis>:<name>`
- Examples: `m:GAN`, `t:expr-prediction`, `type:review`. No numbers.
- **Parent and child tags.** Each group in `ontology.yaml` is a **parent tag** named after the group (`m:generative`); the tags listed under it are its **child tags** (`m:GAN`, `m:diffusion`). Tags under `ungrouped` have no parent.
- **H1. A paper with a child tag must also carry its parent tag.** `m:GAN` → also `m:generative`. Several children of one parent share a single parent tag. A parent tag alone is allowed when no child fits.
- Parent tags do not count toward the per-axis limits below, except a parent used without any of its children.
- Group and tag names are unique within an axis.
- When a tag moves to another group, swap the parent tag on its papers.
- The tag selector sorts by name. `/unread` and `/star` start with `/` and appear at the top.

### Axes

| Axis | Meaning | Per paper |
|---|---|---|
| `m:` | Method | 0–3 |
| `d:` | Data / modality (central as input or prediction target) | 0–3 |
| `t:` | Task | 0–2 |
| `type:` | Paper type (omitted for ordinary method papers) | 0–2 |
| `a:` | Disease / biology area (optional). No oncology tag: it would apply to almost everything | 0–2 |
| `model:` | Name of the proposed model (open vocabulary, see below) | 0–2 |
| `lab:` | Lab whose PI is an author (closed vocabulary, see below) | 0–3 |

- Every paper needs **at least 1** `m:`/`d:`/`t:`/`type:`/`a:` tag. An omitted domain default counts as one.
- `t:classification` is used only when no more specific `t:` tag applies.
- Leave an axis empty when nothing fits. Do not invent meaningless tags. For example, a paper that merely uses a transformer gets no `m:` tag.

### Parent tags (summary; full definitions in `ontology.yaml`)
- **m:** representation-learning · generative · adaptation-setting · set-aggregation · graph · architecture · language-models · multimodal · decision-causal · interpretability-methods · data-centric (ungrouped: ensemble)
- **d:** tissue-imaging · spatial-omics · single-cell · bulk-molecular · molecules-proteins · clinical-data · general-imaging · structured-language
- **t:** molecular-prediction · batch-effect · clinical-prediction · synthesis-reconstruction · cell-tissue-analysis · omics-analysis · molecular-design · language-tasks · trustworthiness (ungrouped: representation, anomaly-detection)
- **type:**, **a:** no parent tags (all tags ungrouped)

### `model:` axis (open vocabulary)
- Format: `model:<official name>`, e.g. `model:TITAN`, `model:CONCH`, `model:CHIEF`. Replace spaces with hyphens (`model:EXAONE-Path-2.0`).
- Apply only when the paper **itself proposes** the model or tool **and its name appears in the title or abstract.** Do not tag baselines, datasets or benchmarks.
- The same name may appear on several papers (e.g. two unrelated papers both called ProtoMIL).
- Hand-made model-name tags that predate the schema are kept (converted to this format) even if the abstract does not mention the name.

### `lab:` axis (closed vocabulary)
- Format: `lab:<PI surname>`, e.g. `lab:Mahmood`, `lab:Chen`. Only the labs listed under `labs` in `ontology.yaml` are allowed. Add a lab there first.
- Apply when the PI appears **anywhere in the author list** (corresponding status is not checked).
- Match the first name too, and for common names (e.g. Hao Chen) check the affiliation so namesakes are not tagged.
- Lab tags do not count toward the "at least 1 tag" minimum and are not subject to T1–T3 or H1.

### User-specified exceptions (`status: user-exception`)
These tags fall below the T1 threshold but are kept at the user's request. They are exempt from T3 pruning. They are marked in `ontology.yaml`.

### Typing tags in Zotero (checked against the Zotero 9.0.6 source)
- Tag **autocomplete is prefix matching** (`name LIKE 'input%'`). Typing `GAN` does not suggest `m:GAN`. Type `m:G` (or just `m:` and pick from the alphabetical list).
- The tag selector **filter is substring matching** (case-insensitive), so `GAN` finds it there.

---

## 3. Special collections and protected tags

### Protected tags: never touch
- **`/unread`** marks unread papers. **`/star`** marks favourites.
- Never add, remove, rename or delete these two tags. Always exclude them from bulk tag operations.
- Both are stored as **automatic** tags in Zotero. **Never use** "Delete Automatic Tags in This Library". Clean up automatic tags only with a script that explicitly excludes these two.
- **Merging duplicates:** if any copy is read (has no `/unread`), the merged item is read. If any copy has `/star`, keep it. Ask the user only for cases these rules do not cover.
- `zotero-cli duplicates merge` does not check item types. It unions tags and collections, moves children (notes, attachments) and trashes the duplicate. Because tags are unioned, compare `/unread` / `/star` first and apply the rule above. It does not record a `dc:replaces` relation, which matters only if links on other synced devices point to the removed item.

### 00_Inbox: staging new papers
- Drop new papers into `00_Inbox` without worrying about classification.
- When the user asks to triage ("triage the inbox", "정리해줘"), handle each Inbox paper as follows:
  1. Read the title and abstract (the first pages of the PDF if the abstract is missing or thin).
  2. Choose one home collection, the tags (each child tag with its parent tag, H1) and any `model:` and `lab:` tags. Draft the TL;DR note (§5-N).
  3. Check for duplicates. Merge them under the rules above.
  4. For a preprint, check whether a published version exists (§5-P).
  5. Show the change list and apply only after confirmation.
  6. Remove triaged papers from the Inbox. Never touch `/unread` or `/star`.
- The checker counts papers that are only in the Inbox as "awaiting triage", and reports papers that have a home collection but are still in the Inbox as an error (E7).

### 00_MyPublications: the user's own papers
- A paper written by the user sits here **in addition to** its home collection and is classified like any other paper (one home, tags, TL;DR).
- It is listed under `views` in `ontology.yaml`. The checker ignores it when counting homes, so it never triggers E1/E2. Never choose it as a home.

## 4. Evolving the taxonomy

### C1. Split a collection only when **all** hold
1. The leaf collection has **80 or more** items.
2. The bundle to split off has **15 or more** items.
3. The split criterion is a **problem**. If you want to split by method or modality, use tags or a Saved Search.
4. **The boundary is clear:** of 10 random papers from the bundle, at least 9 can be placed without hesitation.
5. What remains also has 15 or more items. Otherwise split the remainder into sub-collections too, and leave no papers in the parent.

### C2. General collection check
- When an `x9_General` exceeds **15%** of its domain, look for a bundle inside it that meets C1. If there is none, leave it as is.

### C3. Merging collections
- Merge a leaf with **fewer than 5** items into its closest sibling or `x9_General`.
- New collections get a **3-month** grace period.

### C4. New top-level domain
- Create one only when **30 or more** papers fit no existing domain and their main contribution is not domain-agnostic methodology (`90_Methods`).

### C5. Structural constraints
- At most 3 levels (domain / problem / sub-problem).
- Papers go only in leaf collections. To browse a whole parent, use View → "Show Items from Subcollections".
- Number within 10-blocks (`1x`, `2x`, …). The trailing `9` is reserved for General.
- Never name a collection after a method or modality (e.g. no `MIL`, `ST`, `JEPA`).

### T1. Add a new tag only when **all** hold
1. It would apply to **5 or more** papers.
2. There is a real need to filter by it or build a Saved Search on it.
3. The same view cannot be built from existing tags.
4. **It has a parent.** If no group fits, first consider whether the axis is wrong. Use `ungrouped` only as a last resort.

The user may override this explicitly (`status: user-exception`).

### T2. Refinement (hierarchy)
- Apply the **most specific** child tag together with its parent tag (H1). Do not add sibling tags just to describe something broader; the parent tag covers that.
- When a tag has **40 or more** papers and contains a sub-type worth filtering with **10 or more** papers, **promote** the tag to a group and split it. The hierarchy has only two levels, so a promoted group becomes a new parent tag on its axis (rename it if the name would clash) and its papers get the new parent plus their new child tags.
- If there is no sub-type worth filtering, leave the tag as is even above 40 (the checker only reports it as a candidate).

### T3. Merging and pruning tags
- A child or ungrouped tag with **fewer than 3** papers **6 months** after it was added is merged into another tag of the same group or dropped (its papers keep the parent tag).
- User-exception tags and domain-default tags are exempt.
- Tags with the same meaning are merged immediately.

### T4. Vocabulary management
- `ontology.yaml` is the source of truth. Make additions, changes and moves there, and log them in this document's changelog.
- Never apply a tag that is not in the vocabulary. Track candidates in the checker's "candidate tags" list and judge them against T1 at the quarterly review.
- Automatic tags (arXiv categories, journal subject headings) are not part of the vocabulary. Keep Zotero's auto-tagging off (Settings → General → "Automatically tag items with keywords and subject headings").

### T5. Omitting domain defaults
- A tag that applies to **70% or more** of a domain's papers is that domain's default. Omit it on papers whose home is in that domain.
- The omitted default does not bring in its parent tag (a pathology paper gets `d:tissue-imaging` only if it also has `d:IHC` etc.).
- Defaults are listed under `defaults` in `ontology.yaml`. Apply them normally to papers in other domains.

### Recording decisions
When a C1–C3 or T2 check is deliberately deferred, record the date and reason under `reviews` in `ontology.yaml`. The checker shows this record whenever it flags the same target again.

---

## 5. Metadata maintenance

### P. Replacing preprints with published versions
- **Targets:** items of type `preprint`.
- **Where to look** (external API lookups are allowed):
  1. The existing arXiv auto-note (`Comment: …`, `Other …`) for venue hints ("Accepted to ICML …"). Treat these only as first-pass candidates.
  2. bioRxiv/medRxiv: the published DOI from the official bioRxiv API.
  3. arXiv: Semantic Scholar or OpenAlex (look up by arXiv ID), with the arXiv API's `journal_ref` and `doi` fields as backup. These APIs rate-limit aggressively; batch and back off.
- **Auto-accept only when** the title similarity and the first author **both** match. Agreement between the note's venue and the API result is stronger evidence. Send everything else to a review list.
- **How to replace:** add the published version with `zotero-cli add doi <DOI>`, then merge the preprint into it. Collections, tags (including `/unread` and `/star`), notes and PDFs must move to the published item.
- Ask the user before replacing with a workshop-only version.
- Never put personal data such as the user's email address into external API requests.

### N. Notes
- **Existing notes are preserved.** arXiv auto-notes (`Comment:` / `Other`) are never deleted; they serve as venue hints. Notes the user wrote are never modified.
- **TL;DR note:** one per paper, titled `TL;DR`. Re-running updates the existing note instead of creating a new one.
  ```
  TL;DR
  Problem: … (1 line)
  Method:  … (1 line)
  Result:  … (key result or claim, 1 line)
  ```
- The label language is set with `--lang` (`ko`: 문제/방법/결과, `en`: Problem/Method/Result). The original library uses Korean.
- Write from the abstract. If the abstract is missing or thin, read the first pages of the PDF. The source used is not written in the note; keep it only in the `basis` column of the draft TSV.
- Writing notes never changes tags (`/unread` state is kept).
- Writer: `python tools/write_tldr.py <TSV...> [--only KEY,...] [--lang ko|en] --apply`. It creates missing notes and updates existing ones. Without `--apply` it only prints the counts.

---

## 6. Checking and review cadence

```bash
# Check a classification draft (and save it converted to canonical tags)
python3 tools/check_schema.py --draft audit/<date>/*_classification.tsv --out report.md --mapped mapped.tsv
# Check the live library (Zotero local API, GET only)
python3 tools/check_schema.py --live --out report.md
```

- **Per-item errors**
  - E1: not exactly one home collection
  - E2: collection does not exist or is not a leaf
  - E3: tag not in the vocabulary
  - E4: child tag without its parent tag (H1). In `--draft` mode the missing parents are added to the `--mapped` output instead
  - E5: too many tags on an axis
  - E6: no tags at all
  - E7: has a home collection but is still in `00_Inbox`
  - E8: numbered tag from v1.5 or earlier (`m:1104 GAN`). In `--draft` mode it is converted instead
- **Aggregate rules:** C1–C4, T2, T3, T5, and candidate-tag counts

Cadence:
- **On every addition:** set one home collection and the tags, or leave the paper in `00_Inbox` for triage.
- **Quarterly:** run `check_schema.py --live` and judge every flagged item. Record deferrals under `reviews`. Draft changes and apply them after confirmation.

---

## 7. Migrating an existing library to this schema

The order that worked for the original library. Every step that writes to the library shows its change list first and waits for confirmation. Keep drafts, backups and reports under `audit/<date>_<step>/` (git-ignored).

| Step | Work |
|---|---|
| 0 | Agree on the ontology (`ontology.yaml`). On first use, the `ontology-tailor` agent drafts one from the library |
| 1 | Merge duplicates (§3 rules for `/unread` / `/star`) |
| 2 | Draft a home collection and tags for every paper (parallel subagents work well), until `check_schema.py --draft` reports 0 errors, then user review |
| 3 | Back up collections and tags to JSON. Move the old tree to `_old`, build the new tree, apply memberships and tags |
| 4 | Run `check_schema.py --live` until it reports 0 errors, then delete `_old` |
| 5 | Remove automatic tags (excluding `/unread`, `/star`) and turn off auto-tagging |
| 6 | Create Saved Searches: one per parent tag (named after it, condition `tag is <parent>`), plus cross views as needed |
| 7 | Optional: replace preprints with published versions (§5-P) |
| 8 | Optional: write TL;DR notes (§5-N) |
