from nsepython import *

import json

# =====================================
# DEBUG NSE RESPONSE
# =====================================

try:

    data = nse_optionchain_scrapper(
        "NIFTY"
    )

    print(
        "\nFULL RESPONSE:\n"
    )

    print(
        json.dumps(
            data,
            indent=2,
        )[:5000]
    )

    print(
        "\nTYPE:\n"
    )

    print(type(data))

    print(
        "\nKEYS:\n"
    )

    if isinstance(data, dict):

        print(data.keys())

except Exception as error:

    print(
        "\nERROR:\n"
    )

    print(error)