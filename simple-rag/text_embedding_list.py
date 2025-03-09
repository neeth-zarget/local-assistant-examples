from langchain_community.embeddings import TextEmbedding

supported_models = TextEmbedding.list_supported_models()
print(supported_models)