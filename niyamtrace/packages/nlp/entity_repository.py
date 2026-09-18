from typing import Optional

class EntityRepository:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        
    def check_vendor_exists(self, vendor_id: str) -> bool:
        # Replace with actual DB lookup.
        if str(vendor_id) == "9999":
            return False
        return True

    def find_vendor_candidates(self, vendor_name: str) -> list[str]:
        # Replace with actual DB lookup.
        return []

    def check_user_exists(self, user_id: str) -> bool:
        return True
