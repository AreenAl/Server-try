from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
import json
from main import app
client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    # assert response.json() == "Ahalan! You can fetch some json by navigating to '/json'"

def test_url():
    response = client.get("/j")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_data():
    response = client.get("/json")
    assert response.status_code == 200
    with open('files/customers.json','r')as File:
        data = json.load(File)
    assert response.json() == data

def test_adduser():
    user_data = {
        "id": 1,
        "name": "John",
        "age": 30,
        "occupation": {
            "name": "b",
            "isSaint": True
        }
    }
    response = client.post("/add", json=user_data)
    assert response.status_code == 200

def test_saint_true():
    response=client.get("/saints?isSaint=True")
    # for i in response.json():
    #     if i['occupation']['isSaint']
    assert response.status_code == 200


def test_saint_false():
    response=client.get("/saints?isSaint=False")
    # for i in response.json():
    #     if i['occupation']['isSaint']
    assert response.status_code == 200


def test_getsaints():
    response=client.get("/saints")
    assert response.status_code == 200



def test_who_false():
    response=client.get("/who")
    assert response.status_code == 422

def test_who_true():
    response=client.get("/who?name=sara")
    assert response.status_code == 200
    assert response.json()=={
        "id": 2,
        "name": "Sara",
        "age": 90,
        "occupation": {
            "name": "Our Mother",
            "isSaint": True
        }
    }

def test_who_notexist():
    response=client.get("/who?name=Areen")
    assert response.status_code == 200
    assert response.json()== {"message": "No such customer with name Areen"}



def test_display_users():
    response=client.get("/users")
    assert response.status_code == 200  
    html_content = "<h1>Customer List</h1>"
    html_content += "<table border='1'><tr><th>ID</th><th>Name</th><th>Age</th></tr>"
    # for customer in data:
    #     html_content += f"<tr><td>{customer['id']}</td><td> <a href='/who?name={customer['name']}'> {customer['name']} </a></td><td>{customer['age']}</td></tr>"
    # html_content += "</table>"
    # assert response.content.decode("utf-8") == html_content
    assert response.headers["content-type"] == "text/html; charset=utf-8"  # Check content type





def test_short_desc():
    response=client.get("/short-desc")
    assert response.status_code == 200  
    # html_content = "<table ><tr><th>Name</th><th>occupation</th></tr>"
    # for i in data:
    #     html_content += f"<tr><td> {i['name']} </td> <td>{i['occupation']}</td></tr>"
    # html_content += "</table>"
    assert response.headers["content-type"] == "text/html; charset=utf-8"  # Check content type





def test_add_saint():
    saint = {
        "id": 9,
        "name": "Ddd",
        "age": 22,
        "occupation": {
            "name": "b",
            "isSaint": True
        }
    }
    response = client.post("/addSql", json=saint)
    assert response.status_code == 200
    assert response.json() == {"message": "Data added successfully"}
