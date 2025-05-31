import re
from typing import List

from pymorphy3 import MorphAnalyzer

morph = MorphAnalyzer()


def lemma_analyzer_with_numbers(text: str, max_n: int = 3) -> List[str]:
    """Генерирует лемматизированные n-граммы из текста."""
    tokens = re.findall(
        r"[A-Za-zА-Яа-яёЁ0-9]{2,}(?:-[A-Za-zА-Яа-яёЁ0-9]{2,})*|[^\w\s]",
        text,
        flags=re.UNICODE
    )

    ngrams = []
    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            window = tokens[i:i + n]
            if all(re.fullmatch(r"[A-Za-zА-Яа-яёЁ0-9-]+", tok) for tok in window):
                lemmas = []
                for tok in window:
                    if '-' in tok:
                        parts = [morph.parse(p)[0].normal_form for p in tok.split('-')]
                        lemmas.append('-'.join(parts))
                    else:
                        lemmas.append(morph.parse(tok)[0].normal_form)
                ngrams.append(' '.join(lemmas))
    return ngrams


# print(
#     lemma_analyzer_with_numbers('самой короткой дороге')[-1]
# )
#
# print(morph.parse('самой короткой дороге')[0].normal_form)

p = morph.parse('бабушки голос осип')[0]
print(p.tag.POS)

p = morph.parse(lemma_analyzer_with_numbers('деревне девочка красоты')[-1])[0]
print(p.word)
print(p.tag.case)
print(p.tag.POS)
print()

# 1 accs/nomn, 2 gent
print(morph.parse('факт')[0].tag.case)
print(morph.parse('заключения')[0].tag.case)
print(morph.parse('договора')[0].tag.case)
# print(morph.parse('аттестации')[0].tag.case)

# SINGLE_WORD: (сущ.) сущ. - p.tag.POS === NOUN
# ADJECTIVAL: (сущ., прил.) сущ - p.tag.POS === NOUN; прил - p.tag.POS === ADJF/ADJS
# GENITIVE: (сущ., сущ.), сущ. и сущ. - p.tag.POS === NOUN; сущ1. - nomn/accs, сущ2. - gent.
# ADJECTIVAL_WORDY: два ADJF/ADJS и один NOUN
# GENITIVE_WORDY: все NOUN; два gent и один nomn/accs
# ADJECTIVAL_GENITIVE: два NOUN, один ADJF/ADJS; два gent и один nomn
# GENITIVE_ADJECTIVAL: p.tag.POS === NOUN
