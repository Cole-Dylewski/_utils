
def request_to_dict(request):
    import pandas as pd
    return pd.DataFrame([request.__dict__]).to_dict('records')[0]