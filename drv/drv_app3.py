# !/usr/bin/env python3
# *****************************************************************************
# drv_app3.py
# *****************************************************************************

# Purpose:
# Python driver to:
# Download a file (GLDAS_VIC_3H) using Earthaccess library.
# Authors:
# Manu Tom, Cedric H. David, 2023-2025


# *****************************************************************************
# Import libraries
# *****************************************************************************
import os
import earthaccess
import subprocess


# *****************************************************************************
# Driver for downloading a file to /tmp from Earthdata
# *****************************************************************************
def drv_dwn_ED(yyyy_mm):
    # *************************************************************************
    # earth access parameters from input events
    # *************************************************************************
    date_beg = yyyy_mm+"-01T00:00:00"  # eg. "2000-01-01T00:00:00"
    # eg. "2000-02-01T00:00:00"
    date_end = date_beg.split("-")[0] + "-" + \
        str(int(date_beg.split("-")[1]) + 1).zfill(2)
    # *************************************************************************
    # search for LDAS data
    # *************************************************************************
    results = earthaccess.search_data(
        short_name='GLDAS_VIC10_3H',
        cloud_hosted=True,
        bounding_box=(-180, -60, 180, 90),
        temporal=(date_beg, date_end),
        count=1
        )
    # *************************************************************************
    # make folder, download files, list files downloaded
    # *************************************************************************
    dwnld_fldr = "/tmp"
    if not os.path.exists(dwnld_fldr):
        os.makedirs(dwnld_fldr)
    files = earthaccess.download(results, dwnld_fldr)
    print("Files downloaded: ", files)
    # *************************************************************************
    # check downloaded files
    # *************************************************************************
    result_chk_dwnld = subprocess.run(["ls", "-lR", "/tmp"],
                                      capture_output=True, text=True)
    print("Checking download folder contents:\n", result_chk_dwnld.stdout)
    return files[0]


# *****************************************************************************
# End
# *****************************************************************************
