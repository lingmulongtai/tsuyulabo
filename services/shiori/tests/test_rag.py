from __future__ import annotations

import math

from tsuyu_shiori.rag import BM25Retriever, PgVectorRetriever, hashing_embed, load_papers


async def test_bm25_ranking_and_corpus() -> None:
    papers = load_papers()
    assert len(papers) == 20
    assert len({p.id for p in papers}) == 20
    assert all(p.url.startswith("https://") and p.authors and p.year for p in papers)
    search = BM25Retriever()
    assert (await search.search("MN9 口吻", 1))[0].id in {"#p-09", "#p-10"}
    assert (await search.search("Winding larval connectome", 1))[0].id == "#p-15"
    assert (await search.search("2017 Nobel circadian", 1))[0].id == "#p-14"
    assert await search.search("zzzzunknown") == []
    assert await BM25Retriever([]).search("brain") == []


async def test_vector_contract_and_stable_hashing() -> None:
    vector = hashing_embed("キノコ体 dopamine")
    assert vector == hashing_embed("キノコ体 dopamine")
    assert len(vector) == 384
    assert math.isclose(sum(v * v for v in vector), 1)

    class Index:
        async def nearest(self, embedding: list[float], k: int) -> list:
            assert embedding == vector
            return load_papers()[:k]

    assert len(await PgVectorRetriever(Index()).search("キノコ体 dopamine", 2)) == 2
