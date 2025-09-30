import firebase_admin
from firebase_admin import credentials, firestore

# Load service account key JSON
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
todo_collection = db.collection("todos")
