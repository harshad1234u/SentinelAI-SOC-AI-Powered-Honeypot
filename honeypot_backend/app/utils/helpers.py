def get_pagination_params(page: int = 1, page_size: int = 50) -> tuple[int, int]:
    """Calculate skip and limit for pagination."""
    skip = (page - 1) * page_size
    limit = page_size
    return skip, limit
