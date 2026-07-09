def api_language(request):
    """
    Add current API language to template context.
    This is useful for API documentation templates.
    """
    return {
        'api_language': getattr(request, 'LANGUAGE_CODE', 'fa'),
        'available_languages': [
            {'code': 'fa', 'name': 'Persian'},
            {'code': 'en', 'name': 'English'}
        ]
    }
