# *****************************************************************************
# lambda_function_app0.py
# *****************************************************************************

# Purpose:
# Learn how to use Lambda approach (locally, AWS).
# Author:
# Cedric H. David, Manu Tom, 2023-2025


# *****************************************************************************
# Example invocation
# *****************************************************************************
# {
#     "basin_id": "74",
#     "lsm_mod": "VIC"
#     "yyyy_mm": "2000-01"
#     "s3_name": "currnt-data"
# }


# *****************************************************************************
# lambda_handler
# *****************************************************************************
def lambda_handler(event, context):
    message = event['basin_id']
    return {
        'message': message
    }


# *****************************************************************************
# End
# *****************************************************************************
