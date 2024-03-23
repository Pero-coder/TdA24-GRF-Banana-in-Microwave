from app import activities_db, credentials_db
import pymongo
import bcrypt
import models


def add_activity_to_db(Activity: models.NewActivity) -> bool:
    try:
        activities_db.insert_one(Activity.model_dump())
        return True
    
    except Exception as e:
        print(e)
        return False

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