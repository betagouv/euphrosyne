from typing import Literal, NewType

Method = NewType("Method", str)
Detector = NewType("Detector", str)
Filter = NewType("Filter", str)


OTHER_VALUE: Literal["_"] = "_"
