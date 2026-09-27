from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from importlib.resources import files
from typing import Protocol


@dataclass(frozen=True)
class Paper:
    id: str
    title: str
    authors: list[str]
    year: int
    doi: str | None
    url: str
    summary: str


def load_papers() -> list[Paper]:
    source = files("tsuyu_shiori").joinpath("data/papers.jsonl").read_text(encoding="utf-8")
    return [Paper(**json.loads(line)) for line in source.splitlines() if line.strip()]


def tokenize(text: str) -> list[str]:
    """Latin words plus Japanese character bigrams, without a tokenizer dependency."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for run in re.findall(r"[\u3040-\u30ff\u3400-\u9fff]+", text):
        tokens.extend(run[i : i + 2] for i in range(max(1, len(run) - 1)))
    return tokens


class Retriever(Protocol):
    async def search(self, query: str, k: int = 3) -> list[Paper]: ...


class BM25Retriever:
    def __init__(self, papers: list[Paper] | None = None) -> None:
        self.papers = load_papers() if papers is None else papers
        self.counts = [Counter(tokenize(p.title + " " + p.summary)) for p in self.papers]
        self.lengths = [sum(count.values()) for count in self.counts]
        self.average = sum(self.lengths) / max(1, len(self.lengths)) or 1
        self.frequency: Counter[str] = Counter()
        for count in self.counts:
            self.frequency.update(count.keys())

    async def search(self, query: str, k: int = 3) -> list[Paper]:
        if not 1 <= k <= 20:
            raise ValueError("k must be between 1 and 20")
        scores = []
        for index, count in enumerate(self.counts):
            score = 0.0
            for token in set(tokenize(query)):
                tf = count[token]
                if tf:
                    df = self.frequency[token]
                    idf = math.log(1 + (len(self.papers) - df + 0.5) / (df + 0.5))
                    score += (
                        idf
                        * tf
                        * 2.5
                        / (tf + 1.5 * (0.25 + 0.75 * self.lengths[index] / self.average))
                    )
            if score > 0:
                scores.append((score, index))
        scores.sort(key=lambda pair: (-pair[0], self.papers[pair[1]].id))
        return [self.papers[index] for _, index in scores[:k]]


def hashing_embed(text: str, dimensions: int = 384) -> list[float]:
    if dimensions < 1:
        raise ValueError("dimensions must be positive")
    vector = [0.0] * dimensions
    for token in tokenize(text):
        digest = hashlib.sha256(token.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % dimensions] += 1 if digest[4] & 1 else -1
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


class VectorIndex(Protocol):
    async def nearest(self, embedding: list[float], k: int) -> list[Paper]:
        """Host queries pgvector cosine distance; keep database imports out of Shiori."""
        ...


class PgVectorRetriever:
    def __init__(self, index: VectorIndex) -> None:
        self.index = index

    async def search(self, query: str, k: int = 3) -> list[Paper]:
        if not 1 <= k <= 20:
            raise ValueError("k must be between 1 and 20")
        return await self.index.nearest(hashing_embed(query), k)
