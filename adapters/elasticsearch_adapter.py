from dataclasses import dataclass

from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch

from domain.models.config import LunaMemoriesIndexSchema
from domain.models.memory import Memory, MemoryQuery, MemoryResult, EpisodicMemory, SemanticMemory


class ElasticsearchAdapter:

    cluster_name = "luna-memory"
    index_name = "luna-memories"

    def __init__(
            self,
            rebuild_index: bool = False
    ):
        self.es = Elasticsearch(hosts="http://localhost:9200")
        if not self.es.ping():
            raise ConnectionError("Elasticsearch connection failed.")

        if rebuild_index:
            self.es.indices.delete(index=self.index_name, ignore=[400, 404])
            self.es.indices.create(
                index=self.index_name,
                body={
                    "mappings": {**LunaMemoriesIndexSchema.mappings},
                    "settings": {**LunaMemoriesIndexSchema.settings}
                }
            )

    def store_memory(
            self,
            memory: Memory
    ) -> ObjectApiResponse:
        doc = memory.to_document()

        response = self.es.index(index=self.index_name, body=doc)

        return response