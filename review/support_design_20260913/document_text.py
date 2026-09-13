"""Readable spacing for generated narrative; preserve code, links and identifiers."""
import re


def prose(text):
    words = ('all|and|at least|across|adds|are|batch|beyond|confirmed|Daily|each|every|exact|exactly|exit|exited|'
             'factors|fold|full|generated|horizon|IDs|JMLR|minimum|most|necessary|of|outer|'
             'persistence|priority|prioritized|record|records|request|representing|requires|retained|RICO|'
             'room|seed|seeds|separate|target|the|through|totals|Unchanged|version|window|with')
    chunks = re.split(r'(```[\s\S]*?```|`[^`]*`|\]\([^)]+\))', text)
    for i in range(0, len(chunks), 2):
        chunks[i] = re.sub(r'\b(' + words + r')(?=\d)', r'\1 ', chunks[i], flags=re.I)
        chunks[i] = re.sub(r'(?<=\d)(GiB|MiB|kWh|min|minutes|rows|seconds|s)\b', r' \1', chunks[i])
        chunks[i] = re.sub(r'(?<=[A-Za-z]):(?=\d)', ': ', chunks[i])
        chunks[i] = chunks[i].replace("C's21", "C's 21").replace("benchmark's3", "benchmark's 3")
        chunks[i] = chunks[i].replace('requires 005crosswalk', 'requires an amendment-005 crosswalk')
    return ''.join(chunks)
