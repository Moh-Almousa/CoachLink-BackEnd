import inspect


def match_methods_to_pk_urls(endpoints):
    """
    Some APIViews are routed on both 'items/' and 'items/<pk>/'.
    Keep a method on the URL with {pk} only if the method takes pk, and vice versa,
    so Swagger doesn't offer calls that crash with a missing/unexpected pk.
    """
    result = []
    for path, path_regex, method, callback in endpoints:
        view_cls = getattr(callback, 'cls', None)
        handler = getattr(view_cls, method.lower(), None)
        if handler is not None:
            takes_pk = 'pk' in inspect.signature(handler).parameters
            if takes_pk != ('{pk}' in path):
                continue
        result.append((path, path_regex, method, callback))
    return result
