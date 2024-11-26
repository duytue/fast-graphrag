from itertools import chain
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic._internal import _model_construction

####################################################################################################
# LLM Models
####################################################################################################

def _json_schema_slim(schema: dict[str, Any]) -> None:
    schema.pop("required")
    schema.pop("type")
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)


class _BaseModelAliasMeta(_model_construction.ModelMetaclass):
    def __new__(
        cls, name: str, bases: tuple[type[Any], ...], dct: Dict[str, Any], alias: Optional[str] = None, **kwargs: Any
    ) -> type:
        if alias:
            dct["__qualname__"] = alias
            name=alias
        return super().__new__(cls, name, bases, dct, json_schema_extra=_json_schema_slim, **kwargs)


class BaseModelAlias:
    class Model(BaseModel, metaclass=_BaseModelAliasMeta):
        @staticmethod
        def to_dataclass(pydantic: Any) -> Any:
            raise NotImplementedError

    def to_str(self) -> str:
        raise NotImplementedError


####################################################################################################
# LLM Dumping to strings
####################################################################################################

def dump_to_csv(
    data: Iterable[object],
    fields: List[str],
    separator: str = "\t",
    with_header: bool = False,
    **values: Dict[str, List[Any]],
) -> List[str]:
    rows = list(
        chain(
            (separator.join(chain(fields, values.keys())),) if with_header else (),
            chain(
                separator.join(
                    chain(
                        (str(getattr(d, field)).replace("\t", "    ") for field in fields),
                        (str(v).replace("\t", "    ") for v in vs),
                    )
                )
                for d, *vs in zip(data, *values.values())
            ),
        )
    )
    return rows


def dump_to_reference_list(data: Iterable[object], separator: str = "\n=====\n\n"):
    return [f"[{i + 1}]  {d}{separator}" for i, d in enumerate(data)]


####################################################################################################
# Response Models
####################################################################################################


class TEditRelation(BaseModel):
    ids: List[int] = Field(..., description="Ids of the facts that you are combining into one")
    description: str = Field(
        ..., description="Summarized description of the combined facts, in detail and comprehensive"
    )


class TEditRelationList(BaseModel):
    groups: List[TEditRelation] = Field(
        ...,
        description="List of new fact groups; include only groups of more than one fact",
        alias="grouped_facts",
    )

class TQueryEntities(BaseModel):
    entities: List[str] = Field(
        ...,
        description=("List of entities extracted from the query"),
    )
    n: int = Field(..., description="Number of named entities found")  # So that the LLM can answer 0.

    @field_validator("entities", mode="before")
    @classmethod
    def uppercase_source(cls, value: List[str]):
        return [e.upper() for e in value] if value else value