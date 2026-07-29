def find_duplicate(store, position, proposed_employee):
    for req in store.list_all():
        if req.position == position and req.proposed_employee.lower() == proposed_employee.lower():
            return req
    return None


def find_existing_requests_for_seat(store, position):
    return [req for req in store.list_all() if req.position == position]
