# Paper: Can Uniform Meaning Representation still help Language Models translate when they already know the language well?
Extending the paper titled "Can Uniform Meaning Representation Help GPT-4 Translate from Indigenous Languages?"

Languages chosen: Portuguese, Latin, and Czech.

Portuguese and Czech are high resource languages meaning they are rich in both monolingual and parallel data which can be used to train the model. Whereas Latin is lopsided: a lot of classical work exists and hence, the models can potentially read it well. However, a very limited number of sentence-aligned Latin-English pairs exists.

## Datasets

|Dataset|Link|
|---|---|
|UMR 3.0 (Czech, Latin, and Portuguese), commit ae46502fe27c, 24 Aug 2026|https://github.com/umr4nlp/umr-data/tree/ae46502fe27c|
|PDT-C 2.0 (Source of the Czech UMR)|http://hdl.handle.net/11234/1-5813|


## Dataset Sourcing
Czech, Portuguese, and Latin graphs have been sourced from UMR 3.0. For the translations, we have relied on NLTK Penn Treebank sample (Czech), English PUD (Portuguese), UMR's own English translations (Latin). 

For the language pairs: 
- Czech:
    - The UMR graphs are an automatic conversion of the PCEDT part of PDT-C. PCEDT's Czech is a translation of the Wall Street Journal.
    - 3,914 sentences have been sourced from wsj_0001-wsj_0199 files
    - the English is the Penn Treebank original, paired by file number, then sentence position. 
- Latin: 50 manually annotated sentences, one document. The English translation is in the same file.
- Portuguese:
    - 96 sentences from many PUD articles but packaged as a single UMR document. 
    - Matched automatically to Portuguese PUD by difflib ratio on normalised text with 31 at >= 0.90
    - All of these 96 checked by hand with 1 wrong automatic match `(S000045)` excluded. So, we have 95 usable pairs.
    - English is taken from PUD by sent_id.


## Strategy around invalid Penman concepts

There are some invalid concepts that penman cannot parse (in this data: those starting with #, and the concepts `/` and `"`). If we keep them as it is, the penman decoder shall treat the ones starting with # as comments, and `/` as well `"` shall fail. Hence, they are quoted to preserve their meaning and keep their syntax as is.
The check run is automatic: each concept is tested with penman, and the ones it can't parse are wrapped in double quotes, with `\` and `"` escaped. The affected samples are present in the case of Czech only. The strategy adopted lets all the nodes pass with no node lost.


## Czech detokenization
The source text in the case of Czech is tokenized and hence, there is a need to detokenize it. The tool utilized is `sacremoses 0.2.0`, `MosesDetokenizer(lang="en")` which means utilizing English rules which are mostly around punctuation. The Czech rules merged numbers into adjacent words. The English rules caused no such issues.

## Checksum

```bash
shasum -a 256 data/interim/portuguese_pud_matches_reviewed.tsv
d74766be923f42e4666ee5e2a1c6e911ccc6953b4836bd3a76bdbb3c641c014d  data/interim/portuguese_pud_matches_reviewed.tsv

shasum -a 256 data/interim/portuguese_pairs.jsonl
cff162f7f46ae1f19113d02248d80e506ccf1979a7cc53eb4fff8d9af4651b1f  data/interim/portuguese_pairs.jsonl

shasum -a 256 data/processed/pairs_with_demos.jsonl
50205f79ba19d7c4dd99b684e90ab61c617fdcda64be883e8a32bba5d179a0f8  data/processed/pairs_with_demos.jsonl
```

## Duplicate sentence ids
Czech has 135 repeated sentence ids (same number repeats in different files, number restarts) and 1 in Latin (SlaT-2775).
The duplicate sentence ids have been taken care of by creating unique uid for each of the cases. The idea is described in the Processed Data Section.

## Processed Data Section
The processed data is available as a single file (`data/processed/pairs_with_demos.jsonl`) which consists of 4059 records (Czech 3914, Portuguese 95, Latin 50). The `data/processed/SHA256SUMS` file checks it (`shasum -a 256 -c SHA256SUMS`).
Sentence id is not unique and hence, a unique id was created for each using uid = UMR file stem + : + position (e.g. czech_umr-4775:0).
Following the paper "Can Uniform Meaning Representation Help GPT-4 Translate from Indigenous Languages?":
- The 5 nearest neighbours by sentence chrF (sacrebleu 2.6.0) on the source text within the same language. Ties are broken by uid.
- The sentence itself is excluded by uid.
- The candidate is the hypothesis and the query the reference.
- Additionally, we store `demo_uids` and `demo_scores` for each of the records.

Identical sentences have been allowed for demonstration, following the paper.

## Licences

|Data|License|
|---|---|
|Czech and Latin UMR|CC BY-NC-SA 4.0|
|Portuguese UMR|"CC" (version not stated), derived from PUD which is CC BY-SA 3.0|
|Penn Treebank sample|LDC, non-commercial|
|English PUD and Portuguese PUD|CC BY-SA 3.0|


## Caveats
- The 6 Czech records "Podmínky nebyly zveřejněny." each get the other 5 identical copies as demonstrations (chrF 100), so their five-shot prompts effectively contain the answer as a result of allowing the identical sentences.
- Contamination: WSJ, PUD, and Latin Classics are all public.
- Translationese: the Czech was translated from the English references.
- Converted graphs: the Czech graphs are automatic, not hand-annotated.
- Size: Latin has only 50 sentences, so the results are indicative.
- Original language: some PUD sentences were not originally English.


## References
|Reference|Link|
|---|---|
|Penn Treebank sample (NLTK, wsj_0001–wsj_0199, 3,914 sentences): English for Czech| https://github.com/nltk/nltk_data/blob/9373d812d4b7/packages/corpora/treebank.zip|
|English PUD: English for Portuguese|https://github.com/UniversalDependencies/UD_English-PUD/tree/f16eba4ae7f3|
|Portuguese PUD: for matching|https://github.com/UniversalDependencies/UD_Portuguese-PUD/tree/0fdcc057bcc7|
|Latin English|inside UMR 3.0 (latin/umr_data/latin_umr-0001.umr, Translation(English): lines)|


