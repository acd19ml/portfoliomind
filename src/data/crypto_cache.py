from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class CryptoCache:
    """In-memory cache for cryptocurrency API responses."""

    def __init__(self):
        self._coins_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._last_update: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=5)  # Cache duration of 5 minutes

    def _is_cache_valid(self, key: str) -> bool:
        """Check if the cache for a given key is still valid."""
        if key not in self._last_update:
            return False
        return datetime.now() - self._last_update[key] < self._cache_duration

    def _merge_data(self, existing: Optional[List[Dict[str, Any]]], new_data: List[Dict[str, Any]], key_field: str) -> List[Dict[str, Any]]:
        """Merge existing and new data, avoiding duplicates based on a key field.
        
        Args:
            existing: Existing cached data
            new_data: New data to merge
            key_field: Field to use for identifying duplicates (e.g., 'id' for coins)
            
        Returns:
            Merged data with duplicates removed
        """
        if not existing:
            return new_data

        # Create a set of existing keys for O(1) lookup
        existing_keys = {item[key_field] for item in existing}

        # Only add items that don't exist yet
        merged = existing.copy()
        merged.extend([item for item in new_data if item[key_field] not in existing_keys])
        return merged

    def get_coins(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached coins data if available and valid."""
        if not self._is_cache_valid("coins"):
            return None
        return self._coins_cache.get("coins")

    def set_coins(self, data: List[Dict[str, Any]]) -> None:
        """Set coins data in cache with current timestamp."""
        # Merge new data with existing cache
        self._coins_cache["coins"] = self._merge_data(
            self._coins_cache.get("coins"),
            data,
            key_field="id"  # Use coin's id as the unique identifier
        )
        self._last_update["coins"] = datetime.now()


# Global cache instance
_crypto_cache = CryptoCache()


def get_crypto_cache() -> CryptoCache:
    """Get the global crypto cache instance."""
    return _crypto_cache 