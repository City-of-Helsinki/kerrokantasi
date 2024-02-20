def get_current_request():
    from kerrokantasi.gdpr import _thread_locals

    return getattr(_thread_locals, "request", None)
