import traceback

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def ok(data=None, msg="成功", status=200):
    return Response({"code": 0, "msg": msg, "data": data}, status=status)


def fail(msg, code=40001, status=400, data=None):
    return Response({"code": code, "msg": msg, "data": data}, status=status)


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        if settings.DEBUG:
            traceback.print_exc()
        return fail("服务器内部错误", 50000, 500)
    detail = (
        response.data.get("detail", response.data)
        if isinstance(response.data, dict)
        else response.data
    )
    response.data = {"code": response.status_code * 100, "msg": str(detail), "data": None}
    return response
