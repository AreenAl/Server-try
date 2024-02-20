import json
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from db import connect
from pydantic import BaseModel
from cryptography.fernet import Fernet
from shutil import copyfileobj
from pathlib import Path as path
from fastapi import File, UploadFile, FastAPI, HTTPException,Query,Path, Request, Response,Cookie,Form
from fastapi.staticfiles import StaticFiles


key = b'uzeXlq2ZX6cJ8JSc06XbU_LpsHOP6TMqA5NpbMICBEI='
fernet = Fernet(key)
app = FastAPI()
class User(BaseModel):
    name: str
    id: int 

@app.get("/upload", response_class=HTMLResponse)
async def upload_form():
    return """
    <form action="/upload" enctype="multipart/form-data" method="post">
        <input name="file" type="file" multiple>
        <input name="file_name" type="text">
        <input type="submit">
    </form>
    """

@app.post("/upload")
async def upload_file(file: UploadFile = File(...),file_name : str=Form(...)):
    if not file:
        return {"message": "No upload file sent"}
    suf= path(file.filename).suffix
    if not file_name:
        file_name = file.filename
    file_path = f"assets/{file_name+suf}"
    with open(file_path, "wb") as buffer:
        copyfileobj(file.file, buffer)

    return {"filename": file_name+suf}

# Route to display saint details
@app.get("/saints/{saint_id}", response_class=HTMLResponse)
async def read_saint(saint_id: int):
    result=[]
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT u.name, u.age, o.name,u.image_path
        FROM users u
        JOIN occupations o ON u.occupation_id = o.id
        WHERE u.id = %s 
        """
    cursor.execute(query, saint_id)
    html_content = "<h1>saint details</h1>"

    for row in cursor.fetchall():
        html_content += f"<p>name = {row[0]}, age: {row[1]}, occupation_name: {row[2]}</p>"
        html_content += f'<img src="{row[3]}" alt="Saint Image">'
    conn.close()
    return HTMLResponse(content=html_content)

@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        encrypted_username = request.cookies.get("encrypted_username")
        encrypted_user_id = request.cookies.get("encrypted_user_id")
        if not encrypted_username or not encrypted_user_id:
            return RedirectResponse(url="/login", status_code=302)
        try:
            decrypted_username = fernet.decrypt(eval(encrypted_username)).decode()
            decrypted_user_id = fernet.decrypt(eval(encrypted_user_id)).decode()
            request.state.decrypted_username = decrypted_username
            request.state.decrypted_user_id = decrypted_user_id
        except Exception as e:
            print(f"Error during decryption: {e}")
            return RedirectResponse(url="/login", status_code=302)

    response = await call_next(request)
    return response 


@app.get("/login")    
async def login_page():
    return {"message": "This is the login page"}

procedure_login = """
DROP PROCEDURE IF EXISTS checkuser;
CREATE PROCEDURE checkuser(
    IN Uname VARCHAR(255),
    IN Uid INT)
BEGIN
    SELECT * FROM users
    WHERE id = Uid AND name = Uname;
END;
"""

@app.post("/login")
async def login(user: User, response: Response):
    conn = connect()
    cursor = conn.cursor()
    username=user.name
    userid=str(user.id)
    try:
        cursor.callproc("checkuser", (user.name, user.id))
        result = next(cursor.stored_results())
        rows = result.fetchall()     
        if rows:
            encrypted_username = fernet.encrypt(username.encode())
            encrypted_user_id = fernet.encrypt(userid.encode())
            content = {"message": "Login successful"}
            response = JSONResponse(content=content)
            response.set_cookie(key="encrypted_username", value=encrypted_username)
            response.set_cookie(key="encrypted_user_id", value=encrypted_user_id)
            return response
        else:
            raise HTTPException(status_code=404, detail="User not found")
    finally:
        conn.close()

@app.get("/admin")
async def admin(request: Request):
    decrypted_username = request.state.decrypted_username
    decrypted_user_id = request.state.decrypted_user_id
    if not decrypted_username or not decrypted_user_id:
        # Redirect to login if cookies are not present
        return JSONResponse(status_code=302, headers={"Location": "/login"})
    
    return {"message": f"Welcome, {decrypted_username}! Your user ID is {decrypted_user_id}."}
      
with open('files/customers.json','r+')as File:
    data = json.load(File)

@app.get("/")
async def index():
    return "Ahalan! You can fetch some json by navigating to '/json'"

@app.get("/json")
async def getjson():
    return data

@app.post("/addSql")
async def addSaint(saint:dict):
    conn = connect()
    cursor = conn.cursor()
    query = """
    INSERT INTO occupations (name, isSaint) VALUES (%s, %s)
    """
    cursor.execute(query, (saint['occupation']['name'], saint['occupation']['isSaint']))

    conn.commit()  

    query = """
    INSERT INTO users (id,name, age,occupation_id)
    SELECT %s, %s, %s, id FROM occupations WHERE name = %s
    """
    cursor.execute(query, (saint['id'],saint['name'], saint['age'], saint['occupation']['name']))
    
    conn.commit()  
    return {"message": "Data added successfully"}



@app.post("/add")
async def adduser(userD: dict):
    data.append(userD)
    # with open("files/customers.json", "w") as out_file:
    #     json.dump(data, out_file)
    return data

@app.get("/saints")
async def check(isSaint: bool=None):
    if isSaint is None:
        return await getsaints()
    saint=[]
    for i in data:
        if i['occupation']['isSaint'] == isSaint:
            saint.append(i)
    return saint

@app.get("/saints")
async def getsaints():
    saint=[]
    for i in data:
         if i['occupation']['isSaint']:
             saint.append(i)
    return saint


@app.get("/short-desc")
async def short_desc():
    html_content = "<table ><tr><th>Name</th><th>occupation</th></tr>"
    for i in data:
        html_content += f"<tr><td> {i['name']} </td> <td>{i['occupation']}</td></tr>"
    html_content += "</table>"
    return HTMLResponse(content=html_content)

@app.get("/who")
async def who(name: str = Query(..., min_length=2, max_length=11)):
    if name is None:
        return "Name parameter is required"
    for customer in data:
        if customer["name"].lower() == name.lower():
            return customer
    return {"message": f"No such customer with name {name}"}

@app.get("/users")
async def display_users():
    html_content = "<h1>Customer List</h1>"
    html_content += "<table border='1'><tr><th>ID</th><th>Name</th><th>Age</th></tr>"
    for customer in data:
        html_content += f"<tr><td>{customer['id']}</td><td> <a href='/who?name={customer['name']}'> {customer['name']} </a></td><td>{customer['age']}</td></tr>"
    html_content += "</table>"
    return HTMLResponse(content=html_content)


@app.get("/admin/saint/age/{num1}/{num2}")
async def ageBetween(num1: int = Path(..., ge=0), num2: int = Path(..., ge=0)):
    result=[]
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT u.name, u.age, o.name
        FROM users u
        JOIN occupations o ON u.occupation_id = o.id
        WHERE u.age > %s AND u.age < %s AND o.isSaint = 1
        """
    cursor.execute(query, (num1, num2))
    for row in cursor.fetchall():
        result.append({"name": row[0],"age":row[1], "occupation_name": row[2]})
    conn.close()
    return result


@app.get("/admin/notsaint/age/{num1}/{num2}")
async def NageBetween(num1: int = Path(..., ge=0), num2: int = Path(...,ge=0)):
    result=[]
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT u.name, u.age, o.name
        FROM users u
        JOIN occupations o ON u.occupation_id = o.id
        WHERE u.age > %s AND u.age < %s AND o.isSaint = 0
        """
    cursor.execute(query, (num1, num2))
    for row in cursor.fetchall():
        result.append({"name": row[0],"age":row[1], "occupation_name": row[2]})
    conn.close()
    return result


@app.get("/admin/name/{str}")
async def namecheck(str: str = Path(..., title="Name", description="Name for filtering")):
    result=[]
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT u.name, u.age, o.name
        FROM users u
        JOIN occupations o ON u.occupation_id = o.id
        WHERE u.name like %s AND o.isSaint = 1
        """
    cursor.execute(query, ('%' + str + '%',))
    for row in cursor.fetchall():
        result.append({"name": row[0],"age":row[1], "occupation_name": row[2]})
    conn.close()
    return result


@app.get("/admin/average")
async def average():
    result=[]
    conn = connect()
    cursor = conn.cursor()
    query = """
        SELECT AVG(u.age)
        FROM users u
        JOIN occupations o ON u.occupation_id = o.id
        WHERE o.isSaint = 1
        """
    cursor.execute(query)
    result.append({"saints average:": cursor.fetchone()[0]})
    query = """
        SELECT AVG(u.age)
        FROM users u
        JOIN occupations o ON u.occupation_id = o.id
        WHERE o.isSaint = 0
        """
    cursor.execute(query)
    result.append({"Not saints average:": cursor.fetchone()[0]})
    conn.close()
    return result


