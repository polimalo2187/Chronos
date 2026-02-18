from bson import ObjectId

def oid_str(oid: ObjectId) -> str:
    return str(oid)

def to_objectid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception as e:
        raise ValueError("Invalid ObjectId") from e
