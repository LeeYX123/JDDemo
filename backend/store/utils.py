"""通用工具：订单号、统一分页。"""

import uuid

from django.utils import timezone


def gen_no(prefix=""):
    return prefix + timezone.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6].upper()


def paginate(queryset, request, serializer_class, context=None, default_size=20, max_size=60):
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        size = int(request.query_params.get("size", default_size))
    except (TypeError, ValueError):
        size = default_size
    size = min(max_size, max(1, size))
    total = queryset.count()
    rows = queryset[(page - 1) * size : page * size]
    data = serializer_class(rows, many=True, context=context or {}).data
    return {"page": page, "size": size, "total": total, "results": data}


def category_scope(category):
    """返回该类目及其所有后代 id，用于筛选商品。"""
    if not category:
        return []
    ids = [category.id]
    children = list(category.children.all())
    ids.extend(c.id for c in children)
    for child in children:
        ids.extend(g.id for g in child.children.all())
    return ids
