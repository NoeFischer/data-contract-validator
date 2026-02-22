"""Pydantic models for parsing and validating YAML data contracts.

A data contract is a YAML file with two sections: ``contract`` (metadata)
and ``schema`` (column definitions with types and constraints).  These
models ensure the contract itself is well-formed before any data
validation begins.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ColumnType = Literal["string", "integer", "float", "boolean", "date", "datetime"]
"""Allowed column type literals for a contract column definition."""


class ColumnConstraints(BaseModel):
    """Constraints that can be applied to a single column.

    Attributes:
        required: If ``True``, the column may not contain empty cells.
        unique: If ``True``, all non-empty values must be distinct.
        enum: If set, every non-empty value must be one of the listed
            strings.  Only valid on ``string`` columns.
    """

    required: bool = False
    unique: bool = False
    enum: list[str] | None = None


class ColumnDefinition(BaseModel):
    """Definition of a single column in the contract schema.

    Attributes:
        name: Column header as it appears in the CSV.
        type: Expected data type (see ``ColumnType``).
        format: ``strptime`` format string, only for ``date``/``datetime``.
        constraints: Optional validation constraints for this column.
    """

    name: str = Field(..., min_length=1)
    type: ColumnType
    format: str | None = None
    constraints: ColumnConstraints = Field(default_factory=ColumnConstraints)

    @model_validator(mode="after")
    def validate_column_options(self) -> "ColumnDefinition":
        if self.format is not None and self.type not in ("date", "datetime"):
            raise ValueError(
                f"'format' is only valid for date/datetime columns, not '{self.type}'"
            )
        if self.constraints.enum is not None and self.type != "string":
            raise ValueError(
                f"'enum' is only valid for string columns, not '{self.type}'"
            )
        return self


class SchemaDefinition(BaseModel):
    """Schema section of a data contract, containing column definitions.

    Attributes:
        columns: One or more column definitions.  Column names must be unique.
    """

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
    """Metadata header of a data contract.

    Attributes:
        name: Human-readable dataset name.
        version: Semantic version string (e.g. ``"1.0.0"``).
        description: Optional free-text description.
        owner: Optional team or individual owner.
    """

    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    description: str | None = None
    owner: str | None = None


class DataContract(BaseModel):
    """Top-level model representing a complete data contract.

    Attributes:
        contract: Metadata section (name, version, owner, etc.).
        schema_: Schema section with column definitions.  Aliased from
            ``"schema"`` in the YAML source.
    """

    contract: ContractMetadata
    schema_: SchemaDefinition = Field(..., alias="schema")

    model_config = {"populate_by_name": True}

    @property
    def column_map(self) -> dict[str, ColumnDefinition]:
        """Return a mapping of column name to its definition for fast lookup."""
        return {col.name: col for col in self.schema_.columns}
