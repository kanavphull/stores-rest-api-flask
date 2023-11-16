from copy import deepcopy
from functools import wraps

from flask_jwt_extended import jwt_required


def jwt_required_with_doc(*args, **kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*f_args, **f_kwargs):
            return jwt_required(*args, **kwargs)(func)(*f_args, **f_kwargs)

            """ In this expression applies the jwt_required decorator to the func function
                and then immediately calls the resulting decorated function with the provided 
                arguments f_args and f_kwargs."""

        wrapper._apidoc = deepcopy(getattr(func, "_apidoc", {}))
        wrapper._apidoc.setdefault("manual_doc", {})
        wrapper._apidoc["manual_doc"]["security"] = [{"Bearer Auth": []}]
        return wrapper

    return decorator
