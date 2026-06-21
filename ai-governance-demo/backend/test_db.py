import sys
import uuid
sys.path.append('.')
from database import SessionLocal
from routers.admin import get_user_permissions

db = SessionLocal()
try:
    print(get_user_permissions(uuid.UUID('7a0615aa-0d61-4522-91ad-3f7590ef99e8'), db))
except Exception as e:
    import traceback
    traceback.print_exc()
