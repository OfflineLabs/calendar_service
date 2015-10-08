
def get_detail_routes(viewset, exclude_routes=None):
    ''' examines the viewset and returns a list of detail routes
    not included in exclude_routes '''
    exclude_routes = exclude_routes or ['create', 'update', 'partial_update', 'list', 'detail']
    methods = []
    for methodname in dir(viewset):
        if methodname not in exclude_routes:
            attr = getattr(viewset, methodname)
            detail_route = getattr(attr, 'bind_to_methods', None) and getattr(attr, 'detail', True)
            if detail_route and methodname:
                methods.append(methodname)
    return methods