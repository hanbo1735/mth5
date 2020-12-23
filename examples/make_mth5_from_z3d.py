# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 09:56:40 2020

:author: Jared Peacock

:license: MIT

"""
# =============================================================================
# Imports
# =============================================================================
import zipfile

from mth5 import read_file
from mth5 import mth5
from mth5 import metadata
from mth5.utils.mttime import MTime
from mth5.utils.pathing import DATA_DIR

start = MTime()
start.now()
# =============================================================================
#
# =============================================================================
# set to true if you want to interact with the mth5 object in the console 
interact = True
nims_dir = DATA_DIR.joinpath("zen")
h5_fn = DATA_DIR.joinpath("from_zen.mth5")

if h5_fn.exists():
    h5_fn.unlink()
    print(f"INFO: Removed existing file {h5_fn}")

# need to unzip the data
with zipfile.ZipFile(nims_dir.joinpath("zen.zip"), "r") as zip_ref:
    zip_ref.extractall()

# write some simple metadata for the survey
survey = metadata.Survey()
survey.acquired_by.author = "MT Master"
survey.fdsn.id = "TST01"
survey.fdsn.network = "MT"
survey.name = "test"

# open mth5 file
m = mth5.MTH5(h5_fn)
m.open_mth5()

# add survey metadata
m.survey_group.metadata.from_dict(survey.to_dict())

# add station metadata from z3d files
ch_list = []
for fn in zip_ref.filelist:
    mtts_obj = read_file(fn.filename)

    station_group = m.add_station(
        mtts_obj.station_metadata.id, station_metadata=mtts_obj.station_metadata
    )

    run_id = station_group.locate_run(mtts_obj.sample_rate, mtts_obj.start)
    if run_id is None:
        run_id = station_group.make_run_name()
        mtts_obj.run_metadata.id = run_id

    run_group = station_group.add_run(run_id, mtts_obj.run_metadata)

    ch_list.append(run_group.from_channel_ts(mtts_obj))

    # need to update the station summary table entry
    station_group.summary_table.add_row(
        run_group.table_entry, station_group.summary_table.locate("id", run_id)
    )
    station_group.validate_station_metadata()


end = MTime()
end.now()

print(f"Conversion to MTH5 took {end-start:.2f} seconds")

if not interact:
    m.close_mth5()
