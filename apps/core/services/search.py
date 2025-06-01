from config.elasticsearch import es

def index_product(product: dict):
    es.index(index="products", id=product["id"], body=product)
