"""Debug technical analysis data structure"""

import asyncio
import json
from app.services.data_collectors.manager import data_manager


async def main():
    ta_data = await data_manager.collect_for_ta_agent()
    print(json.dumps(list(ta_data.keys()), indent=2))
    print("\nIndicators keys:")
    print(json.dumps(list(ta_data["indicators"].keys()), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
