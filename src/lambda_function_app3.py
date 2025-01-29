# *****************************************************************************
# lambda_function_app3.py
# *****************************************************************************

# Purpose:
# Use a python driver and download files from Earthdata
# to /tmp/ using credentials.
# Authors:
# Manu Tom, Cedric H. David, 2023-2025


# *****************************************************************************
# Example invocation
# *****************************************************************************
# {
#      "basin_id": "74",
#      "lsm_mod": "VIC"
#      "yyyy_mm": "2000-01"
#      "s3_name": "currnt-data"
# }


# *****************************************************************************
# Import libraries
# *****************************************************************************
import drv_app3 as drv


# *****************************************************************************
# lambda handler
# *****************************************************************************
def lambda_handler(event, context):
    yyyy_mm = event['yyyy_mm']
    # *************************************************************************
    # invoke driver
    # *************************************************************************
    filename = drv.drv_dwn_ED(yyyy_mm)
    message = 'Dowloaded file: {}'.format(filename)
    return {
        'Success: ': message
    }


# *****************************************************************************
# End
# *****************************************************************************
