# main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize FastAPI
app = FastAPI(
    title="Todo List API",
    description="REST API untuk mengelola Todo List dengan FastAPI & Firebase",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: str
    updated_at: str

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Todo List API with FastAPI & Firebase",
        "docs": "/docs",
        "version": "1.0.0"
    }

# CREATE - Tambah todo baru
@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate):
    try:
        todo_data = {
            "title": todo.title,
            "description": todo.description,
            "completed": todo.completed,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        doc_ref = db.collection("todos").document()
        doc_ref.set(todo_data)
        
        todo_data["id"] = doc_ref.id
        return todo_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")

# READ - Ambil semua todos
@app.get("/todos", response_model=List[TodoResponse])
async def get_todos(completed: Optional[bool] = None):
    try:
        todos_ref = db.collection("todos")
        
        if completed is not None:
            todos_ref = todos_ref.where("completed", "==", completed)
        
        todos = []
        for doc in todos_ref.stream():
            todo_data = doc.to_dict()
            todo_data["id"] = doc.id
            todos.append(todo_data)
        
        return todos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching todos: {str(e)}")

# READ - Ambil todo berdasarkan ID
@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str):
    try:
        doc_ref = db.collection("todos").document(todo_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        todo_data = doc.to_dict()
        todo_data["id"] = doc.id
        return todo_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching todo: {str(e)}")

# UPDATE - Update todo
@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: str, todo: TodoUpdate):
    try:
        doc_ref = db.collection("todos").document(todo_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        update_data = {k: v for k, v in todo.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now().isoformat()
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        todo_data = updated_doc.to_dict()
        todo_data["id"] = todo_id
        return todo_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating todo: {str(e)}")

# DELETE - Hapus todo
@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: str):
    try:
        doc_ref = db.collection("todos").document(todo_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        doc_ref.delete()
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting todo: {str(e)}")

# EXTRA - Mark todo as completed
@app.patch("/todos/{todo_id}/complete")
async def complete_todo(todo_id: str):
    try:
        doc_ref = db.collection("todos").document(todo_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        doc_ref.update({
            "completed": True,
            "updated_at": datetime.now().isoformat()
        })
        
        return {"message": "Todo marked as completed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing todo: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)