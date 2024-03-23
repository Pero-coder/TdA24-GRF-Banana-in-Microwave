from app import activities_to_approve_db, activities_db, credentials_db, ai_summaries_db, openai_client
import pymongo
import bcrypt
import models


def add_activity_to_db(activity: models.ActivityModel) -> bool:
    try:
        activity_json = activity.model_dump()
        activity_json["_id"] = activity.uuid

        activities_to_approve_db.insert_one(activity_json)
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

def delete_ai_description(activity_uuid: str) -> bool:
    result = ai_summaries_db.delete_one({"_id": activity_uuid})
    return result.deleted_count > 0

def hash_password_bcrypt(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_hash_bcrypt(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def add_user_credentials_to_db(username: str, password: str) -> bool:
    hashed_password = hash_password_bcrypt(password)
    try:
        credentials_db.create_index("username", unique=True)
        credentials_db.insert_one({"username": username, "hashed_password": hashed_password})
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

def create_ai_description(activity_object: models.ActivityModel):

    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Správce systému pro sdílení různých nápadů na aktivity mezi nadšenými uživateli"},
            {"role": "user", "content": "Potřebuji vygenerovat shrnutí či popisek aktivity, který bude na hlavní stránce a bude ji reprezentovat. Délka musí být 3 věty. Nezahrnuj zde prosím zbytečné informace jako uuid. Klidně informace více zkrášli. Zde je JSON ve kterém najdeš informace o aktivitě: " + activity_object.model_dump_json()} 
        ]
    )

    return completion.choices[0].message.content



def add_ai_generated_description(activity_uuid: str, ai_description: str):
    try:
        ai_summaries_db.update_one({"_id": activity_uuid}, {"$set": {"summary": ai_description}}, upsert=True)
        return True
    
    except pymongo.errors.PyMongoError as e:
        return False


def get_ai_generated_description(activity_uuid: str):
    found_description = ai_summaries_db.find_one({"_id": {"$eq": activity_uuid}})

    return found_description

def ai_search_activities(search_text: str) -> list[str]:

    all_activities = list(activities_db.find())

    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Správce systému pro sdílení různých nápadů na aktivity mezi nadšenými uživateli, který má vybrat záznamy na základě nejlepší shody z tohoto listu jsonů: {all_activities}. Pokud se vyloženě nějaké neshodují, nedávej je sem."},
            {"role": "user", "content": f"Vypiš pouze uuid záznamů (oddělených čárkou), které se nejvíce hodí pro toto konkrétní hledání: '{search_text}'"}
        ]
    )

    return completion.choices[0].message.content



def approve_activity(activity_uuid: str) -> bool:
    try:
        activity_to_approve = activities_to_approve_db.find_one({"_id": {"$eq": activity_uuid}})

        if activity_to_approve is not None:
            activities_db.insert_one(activity_to_approve)
            activities_to_approve_db.delete_one({"_id": activity_uuid})

            new_activity_object = models.ActivityModel(**activity_to_approve)
        
            ai_generated_description = create_ai_description(new_activity_object)
            success_ai_generated_description = add_ai_generated_description(new_activity_object.uuid, ai_generated_description)


            return True
        else:
            print(f"No activity found with uuid: {activity_uuid}")
            return False

    except Exception as e:
        print(e)
        return False