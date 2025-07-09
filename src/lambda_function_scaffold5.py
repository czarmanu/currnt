# *****************************************************************************
# lambda_function_scaffold5.py
# *****************************************************************************

# Purpose:
# Use a python driver to:
# 1) download a file to /tmp/ using Earthaccess library (uisng credentials))
# 2) upload the same file to s3 bucket using s3 credentials.
# 3) download the same file from s3 bucket to /tmp folder.
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
import drv_scaffold5 as drv


# *****************************************************************************
# lambda handler
# *****************************************************************************
def lambda_handler(event, context):
    yyyy_mm = event['yyyy_mm']
    s3_bucket_name = event['s3_name']
    # *************************************************************************
    # invoke drivers
    # *************************************************************************
    file = drv.drv_dwn_ED(yyyy_mm)
    drv.drv_upl_S3(s3_bucket_name, file)
    drv.drv_dwn_S3(s3_bucket_name, file)
    message = (
        'Downloaded the file from {} as {}, uploaded it to the S3 bucket {}, '
        'and re-downloaded it'.format(yyyy_mm, file, s3_bucket_name)
        )
    return {
        'Success: ': message
    }


# *****************************************************************************
# End
# *****************************************************************************
