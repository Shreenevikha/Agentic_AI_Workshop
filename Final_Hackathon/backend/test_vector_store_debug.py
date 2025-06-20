import logging
logging.basicConfig(level=logging.DEBUG)

from agents.regulation_fetcher_agent import initialize_regulation_fetcher_agent, vector_store

print("Before initialization:")
print(f"Vector store is None: {vector_store is None}")
print(f"Vector store type: {type(vector_store)}")

print("\nCalling initialize_regulation_fetcher_agent()...")
try:
    result = initialize_regulation_fetcher_agent()
    print(f"\nInitialization result: {result}")
    print(f"Vector store after init: {vector_store is not None}")
    print(f"Vector store type after init: {type(vector_store)}")
    
    if vector_store is not None:
        print(f"Vector store collection name: {vector_store._collection.name}")
    else:
        print("Vector store is still None!")
        
except Exception as e:
    print(f"Exception during initialization: {e}")
    import traceback
    traceback.print_exc() 