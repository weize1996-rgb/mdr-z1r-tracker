seen = set()

def is_valid(item):
    name = item["title"].lower()
    price = item["price"]

    if any(x in name for x in ["耳罩","線","盒","收納","支架","套"]):
        return False

    if "z1r" not in name:
        return False

    if price < 15000:
        return False

    return True

def is_used(item):
    name = item["title"].lower()
    return any(k in name for k in ["二手","中古","used","9成","8成"])

def seen_before(id):
    if id in seen:
        return True
    seen.add(id)
    return False