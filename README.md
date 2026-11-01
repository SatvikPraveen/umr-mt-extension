# Paper: can Uniform Meaning Representation still help Language Models when they already know the language well?
Extending the paper titled "Can Uniform Meaning Representation Help GPT-4 Translate from Indigenous Languages?"

Languages chosen: Portuguese, Latin, and Czech.

Portuguese and Czech are high resource languages meaning they are rich in both monolingual and parallel data which can be used to train the model. Whereas Latin is lopsided: a lot of classical work exists and hence, the models read them well. However, a very limited sentence-aligned Latin-English pairs exist.

## Datasets

|Dataset|Link|
|---|---|
|UMR2.0 (Czech and Latin)|http://hdl.handle.net/11234/1-5902 (LINDAT)|
|UMR 3.0 (Portuguese)|https://github.com/umr4nlp/umr-data/tree/ae46502fe27c/portuguese|
|PDT-C 2.0 (Source of the Czech UMR)|http://hdl.handle.net/11234/1-5813|



## References
|Reference|Link|
|---|---|
|Penn Treebank sample (NLTK, wsj_0001–0199, 3,914 sentences): English for Czech|https://github.com/nltk/nltk_data|
|English PUD: English for Portuguese|https://github.com/UniversalDependencies/UD_English-PUD|
|Portuguese PUD: for matching|https://github.com/UniversalDependencies/UD_Portuguese-PUD|
|Latin English|(inside UMR 2.0)|
