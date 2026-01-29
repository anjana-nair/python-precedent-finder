"""
Utility functions for the Precedent Finder application.
"""


def sanitize_search_query(query):
    """
    Sanitize search query to prevent SQL injection.
    
    Args:
        query (str): Raw search query
        
    Returns:
        str: Sanitized search query
    """
    # Remove leading/trailing whitespace
    query = query.strip()
    
    # Remove multiple spaces
    query = ' '.join(query.split())
    
    return query


def highlight_search_terms(text, terms):
    """
    Highlight search terms in text.
    
    Args:
        text (str): Text to highlight
        terms (list): List of terms to highlight
        
    Returns:
        str: HTML with highlighted terms
    """
    highlighted = text
    for term in terms:
        highlighted = highlighted.replace(
            term,
            f'<mark>{term}</mark>'
        )
    return highlighted


def paginate_results(results, page=1, per_page=20):
    """
    Paginate results list.
    
    Args:
        results (list): List of results
        page (int): Page number (1-indexed)
        per_page (int): Results per page
        
    Returns:
        dict: Paginated results with metadata
    """
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'results': results[start:end],
        'total': total,
        'page': page,
        'pages': (total + per_page - 1) // per_page,
        'per_page': per_page
    }
