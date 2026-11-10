import traceback
from cycle import daily_cycle
from db import init_schema
from notify import send

if __name__ == "__main__":
    try:
        init_schema()
        result = daily_cycle()
        print(result, flush=True)
        if "analysis_id" not in result:
            send(f"WebSat daily run incomplete: {result}")
    except Exception as e:
        detail = "".join(traceback.format_exception_only(type(e), e)).strip()
        send(f"WebSat daily run FAILED: {detail}")
        raise
