from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data.species_db import species_by_id, species_list, _regions

router = APIRouter()


@router.get("/species")
async def list_species():
    return {"species": species_list()}


# NOTE: must be declared BEFORE /species/{species_id} so "all" isn't captured by the int path param.
@router.get("/species/all")
async def species_collection():
    regions = _regions()
    return {
        "species": species_list(),
        "profiles": species_list(),
        "regions": regions,
    }


@router.get("/species/{species_id}")
async def get_species(species_id: int):
    s = species_by_id(species_id)
    if not s:
        raise HTTPException(status_code=404, detail="Species not found")
    return s


@router.get("/regions")
async def list_regions():
    return {"regions": _regions()}
