from cycle import daily_cycle
from db import init_schema

if __name__ == "__main__":
    init_schema()
    print(daily_cycle(), flush=True)
