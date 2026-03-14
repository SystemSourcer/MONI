import json
from datetime import datetime
from fastapi import FastAPI, Request, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="moni/static"), name="static")
templates = Jinja2Templates(directory="/workspace/moni/templates")

role_dict = {
    "Admin": {"password": "Admin"},
    "Worker": {"password": "0000",},
}

try:
    with open("/workspace/data/inventory.json", "r", encoding="utf-8") as inventory_file:
        inventory = json.load(inventory_file)

except: inventory = dict()

try:
    with open("/workspace/data/flow_log.json", "r", encoding="utf-8") as flow_log_file:
        flow_log  = json.load(flow_log_file)

except: flow_log = {0: {'time': datetime.now().isoformat(), 'type': 'init', 'role': 'System', 'user': 'System', 'item': 'Init', 'quantity': '0', 'price': '0'}}

print(inventory)
print(flow_log)

@app.get("/")
def root():
    return RedirectResponse(url="/login")


@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_post(request: Request, role: str = Form(...), user: str = Form(...), password: str = Form(...)):
    if not role in role_dict.keys() or role_dict[role]["password"] != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Ungültiger Benutzername oder Passwort"})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/dashboard")
def dashboard(request: Request):
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    if not role:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request, "role": role, "user": user, "inventory":inventory})

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user")
    return response

@app.get("/input")
def input(request: Request):
    return templates.TemplateResponse("input.html", {"request": request})

@app.post("/input")
def input_post(request: Request, category: str = Form(...), item: str = Form(...), quantity: str = Form(...)):
    role = request.cookies.get("role")
    user = request.cookies.get("user")

    if category not in inventory.keys(): inventory[category] = list()
    
    if item not in [id['item'] for id in inventory[category]]:
        inventory[category].append({'item':item,'quantity':0,'price': 0})

    for id in inventory[category]:
        if id['item'] == item:
            id['quantity'] += int(quantity)

    print(inventory[category])

    n = int(next(reversed(flow_log)))
    flow_log[n+1] = {'time':datetime.now().isoformat(), 'type':'input', 'role':role, 'user': user, 'item':item, 'quantity':quantity}

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/set_price")
def input(request: Request):
    return templates.TemplateResponse("set_price.html", {"request": request, "inventory": inventory})


@app.post("/set_price") 
async def set_price_post(request: Request):
    form = await request.form()

    for field_name, value in form.items():
        print(field_name, value)
        for idl in inventory.values():
            for id in idl:
                if id['item'] == field_name: id['price'] = value
    
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/output")
def output(request: Request, category: str):
    return templates.TemplateResponse("output.html", {"request": request, "assortment": inventory[category]})

@app.post("/output")
async def output_post(request: Request):
    form = await request.form()
    print(form)

    role = request.cookies.get("role")
    user = request.cookies.get("user")
    
    for field_name, value in form.items():
        print(flow_log)
        if 'item' in field_name:
            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().isoformat(), 'type':'output', 'role':role, 'user': user, 'item':value}

        elif 'quantity' in field_name: 
            flow_log[n+1]['quantity'] = value
            for idl in inventory.values():
                for id in idl:
                    if id['item'] in field_name: id['quantity'] -= int(value)

        elif 'price' in field_name:
            flow_log[n+1]['price'] = value 

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response




"""

# Imports

import sqlmodel
from passlib.context import CryptContext

# Functions
def main():
    # Config
    SECRET_KEY = '0000'
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    # DB (SQLite)
    DATABASE_URL = "sqlite:///./db.sqlite"
    engine = sqlmodel.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# Objects




# Global
if __name__ == '__main__': # 
    main() # 

# This is the last line of the Code :)
"""