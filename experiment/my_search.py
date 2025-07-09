import time

from database import get_session
from src.services.search_service import SearchService

db = next(get_session())
search_service = SearchService()
start = time.time()

print(search_service.search_by_query(db, "шапочка"))

end = time.time()
search_time = end - start
print(f"Time: {search_time}")
