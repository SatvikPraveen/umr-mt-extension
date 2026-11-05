"""Prompt text from the paper "Can Uniform Meaning Representation Help GPT-4 Translate from Indigenous Languages?",
Fig. 2 (Appendix A). Instructions are single line, newlines separate the parts (instruction, demonstrations, test sentence,
UMR line, answer cue)."""

SYSTEM_PROMPT = "You are a machine translation system from {language} to English that translates sentences from narrative documents."
INSTRUCTION = "Please provide the English translation for this {language} sentence. Do not provide any explanations or text apart from the translation."
INSTRUCTION_UMR = "Please provide the English translation for this {language} sentence (which is accompanied by a Uniform Meaning Representation parse). Do not provide any explanations or text apart from the translation."
SOURCE_LINE = "{language}: {sentence}"
UMR_LINE = "Uniform Meaning Representation: {graph}"
ANSWER_CUE = "English:"
DEMO_LINE = "{language}: {sentence} English: {translation}"
DEMO_LINE_UMR = "{language}: {sentence} Uniform Meaning Representation: {graph} English: {translation}"
LANGUAGE_NAMES = {"czech": "Czech", "portuguese": "Portuguese", "latin": "Latin"}
PROTOCOLS = ("zero_shot", "zero_shot_umr", "five_shot", "five_shot_umr")
