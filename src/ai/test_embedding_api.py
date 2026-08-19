from __future__ import annotations

from src.ai.embedding_api import embed_query


def main() -> None:
    query = "Can a person with diabetes drink orange juice?"
    vector = embed_query(query)

    print("Embedding API OK")
    print("Vector length:", len(vector))
    print("First 5 values:", vector[:5])


if __name__ == "__main__":
    main()
