def get_backend():
    from ..settings import BACKEND_CLASS
    from ..utils import load_class

    backend = load_class(BACKEND_CLASS)

    return backend
