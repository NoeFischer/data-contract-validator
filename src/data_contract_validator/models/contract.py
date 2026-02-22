from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ColumnType = Literal["string", "integer", "float", "boolean", "date", "datetime"]


class ColumnConstraints(BaseModel):
    required: bool = False
    unique: bool = False
    enum: list[str] | None = None


class ColumnDefinition(BaseModel):
    name: str = Field(..., min_length=1)
    type: ColumnType
    format: str | None = None
    constraints: ColumnConstraints = Field(default_factory=ColumnConstraints)

    @model_validator(mode="after")
    def format_only_for_temporal(self) -> "ColumnDefinition":
        if self.format is not None and self.type not in ("date", "datetime"):
            raise ValueError(
                f"'format' is only valid for date/datetime columns, not '{self.type}'"
            )
        return self


class SchemaDefinition(BaseModel):
    columns: list[ColumnDefinition] = Field(..., min_length=1)

    @field_validator("columns")
    @classmethod
    def no_duplicate_column_names(
        cls, cols: list[ColumnDefinition],
    ) -> list[ColumnDefinition]:
        seen: set[str] = set()
        dupes: set[str] = set()
        for col in cols:
            if col.name in seen:
                dupes.add(col.name)
            seen.add(col.name)
        if dupes:
            raise ValueError(f"Duplicate column names: {sorted(dupes)}")
        return cols


class ContractMetadata(BaseModel):
    name: str = Field(..., min_length=1)
    version: str
    description: str | None = None
    owner: str | None = None


class DataContract(BaseModel):
    contract: ContractMetadata
    schema_: SchemaDefinition = Field(..., alias="schema")

    model_config = {"populate_by_name": True}

    @property
    def column_map(self) -> dict[str, ColumnDefinition]:
        return {col.name: col for col in self.schema_.columns}
