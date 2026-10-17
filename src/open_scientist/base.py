"""Shared strict schema primitives for records and workflow checkpoints."""
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Ref(StrictModel):
    id: Annotated[str, StringConstraints(pattern=ID_PATTERN)]
    version: int = Field(ge=1)
