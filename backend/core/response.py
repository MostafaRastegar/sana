def success_response(data, message=None, status=200, extra=None):
    """Return a success response dict for custom actions."""
    result = {"success": True, "message": message, "data": data}
    if extra:
        result.update(extra)
    return result


def created_response(data, message="Created successfully."):
    """Return a 201 success response dict."""
    return success_response(data, message, status=201)


def deleted_response(message="Deleted successfully."):
    """Return a 200 success response dict for deletions."""
    return success_response(None, message, status=200)