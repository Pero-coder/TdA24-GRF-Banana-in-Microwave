from app import activities_db, credentials_db
import pymongo
import bcrypt
import models


def add_activity_to_db(activity: models.ActivityModel) -> bool:
    try:
        activity_json = activity.model_dump()
        activity_json["_id"] = activity.uuid

        activities_db.insert_one(activity_json)
        return True
    
    except Exception as e:
        print(e)
        return False

def get_specific_activity(activity_uuid: str) -> dict:
    activity_uuid = activity_uuid.strip()
    found_activity = activities_db.find_one({"_id": {"$eq": activity_uuid}})

    if found_activity is None:
        return {"code": 404, "message": "User not found"}, 404
    else:
        
        activity_object = models.ActivityModel(**found_activity)
        return activity_object.model_dump(), 200

def delete_activity(activity_uuid: str) -> bool:
    result = activities_db.delete_one({"_id": activity_uuid})
    return result.deleted_count > 0

def hash_password_bcrypt(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_hash_bcrypt(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def add_user_credentials_to_db(uuid: str, username: str, password: str) -> bool:
    hashed_password = hash_password_bcrypt(password)
    try:
        credentials_db.create_index("username", unique=True)
        credentials_db.insert_one({"_id": uuid, "username": username, "hashed_password": hashed_password})
        return True
    
    except pymongo.errors.DuplicateKeyError:
        print("Username already exists.")
        return False
    
def change_user_password_in_db(uuid: str, new_password: str) -> bool:
    hashed_password = hash_password_bcrypt(new_password)
    try:
        result = credentials_db.update_one({"_id": uuid}, {"$set": {"hashed_password": hashed_password}})
        return result.modified_count > 0
    
    except pymongo.errors.PyMongoError as e:
        return False