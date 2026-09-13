"""No-fit regression for nullable source groups at CSV boundaries."""
import io
import numpy as np
import pandas as pd
from src.matched_data005 import export_identifiers
from src.unit_checkpoint import UnitCheckpoint

def test_python_none_literal_none_and_empty_identifiers_are_explicit():
 frame=pd.DataFrame(dict(group_id=[None,'None','','run1'],row_id=['a','b','c','d'],point=[.1,.2,.3,.4]))
 original=frame.copy(deep=True);encoded=export_identifiers(frame)
 assert encoded.group_id.tolist()==['None','None','','run1']
 restored=pd.read_csv(io.StringIO(encoded.to_csv(index=False)),keep_default_na=False,float_precision='round_trip')
 assert restored.group_id.tolist()==encoded.group_id.tolist()
 np.testing.assert_array_equal(restored.point,frame.point)
 pd.testing.assert_frame_equal(frame,original)

def test_actual_checkpoint_csv_roundtrip_keeps_none_visible(tmp_path):
 frame=export_identifiers(pd.DataFrame(dict(row_id=['a'],group_id=[None],point=[.125])))
 store=UnitCheckpoint(tmp_path/'run',{'schema':'canonical_group_strings'},string_columns=('group_id',))
 store.save('example',{'test':True},{'predictions':frame})
 _,frames=store.load('example')
 assert frames['predictions'].group_id.tolist()==['None']
 assert frames['predictions'].point.tolist()==[.125]
