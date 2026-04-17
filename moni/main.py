import json
import hashlib
from datetime import datetime
from urllib.parse import quote_plus
from fastapi import FastAPI, Request, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="moni/static"), name="static")
templates = Jinja2Templates(directory="./moni/templates")

role_dict = {
    'admin': {'password': '887375daec62a9f02d32a63c9e14c7641a9a8a42e4fa8f6590eb928d9744b57bb5057a1d227e4d40ef911ac030590bbce2bfdb78103ff0b79094cee8425601f5'},
    'worker': {'password': 'c6001d5b2ac3df314204a8f9d7a00e1503c9aba0fd4538645de4bf4cc7e2555cfe9ff9d0236bf327ed3e907849a98df4d330c4bea551017d465b4c1d9b80bcb0'},
}

tabel_dict = {}
for letter in ['A','B','C','D','E','F','G','H']:
    for number in range(10):
        tabel_dict[letter+str(number)]=False

order_temp_list = [],

try:
    with open("/workspace/data/inventory.json", "r", encoding="utf-8") as inventory_file:
        inventory = json.load(inventory_file)

except: inventory = dict()

try:
    with open("/workspace/data/flow_log.json", "r", encoding="utf-8") as flow_log_file:
        flow_log  = json.load(flow_log_file)
    
    flow_log = {int(k): v for k, v in flow_log.items()} # because key are streings after loding but int wen createt thru the system

except: flow_log = {0: {'time': datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type': 'init', 'role': 'System', 'user': 'System', 'category':'Init', 'item': 'Init', 'quantity': '0', 'price': '0'}} # need init entry becaus counts with last entry...

print(inventory)
print(flow_log)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("/workspace/moni/static/favicon.ico")

@app.get("/")
def root():
    return RedirectResponse(url="/login")

@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse(request,"login.html")

@app.post("/login")
def login_post(request: Request, role: str = Form(...), user: str = Form(...), password: str = Form(...)):
    
    if not role in role_dict.keys() or role_dict[role]["password"] != hashlib.sha512((password).encode()).hexdigest():
        return templates.TemplateResponse(request, "login.html", {"error": "Ungültiger Benutzername oder Passwort"})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/dashboard")
def dashboard(request: Request):
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "dashboard.html", {"role": role, "user": user, "inventory":inventory})

@app.post("/dashboard")
def dashboard_post(request: Request, category: str = Form(...), action: str = Form(...)):
    cat_param = quote_plus(category)
    if action == "Output":
        response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    
    if action == "Return":
        response = RedirectResponse(url=f"/return?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)

    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user")
    return response

@app.get("/input")
def input(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "input.html")

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
    flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'input', 'role':role, 'user': user, 'category':category, 'item':item, 'quantity':quantity}

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/set_price")
def set_price(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "set_price.html", {"inventory": inventory})

@app.post("/set_price") 
async def set_price_post(request: Request):
    form = await request.form()

    for field_name, value in form.items():
        print(f"New price vor {field_name}: {value}")
        for idl in inventory.values():
            for id in idl:
                if id['item'] == field_name: id['price'] = value
    
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/tabel_management")
def tabel_management(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "tabel_management.html", {"tabel_dict": tabel_dict})

@app.post("/tabel_management") 
async def tabel_management_post(request: Request, tabel: str = Form(...)):
    if tabel_dict[tabel] == True: tabel_dict[tabel] = False
    else: tabel_dict[tabel] = True
    
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response = RedirectResponse(url="/tabel_management", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/output")
def output(request: Request, category: str):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "output.html", {"category":category, "assortment": inventory[category]})

@app.post("/output")
async def output_post(request: Request):
    form = await request.form()
    print(form)
    category = form.get("category")

    role = request.cookies.get("role")
    user = request.cookies.get("user")

    for field_name, value in form.items():
        print(flow_log)
        if 'item' in field_name:
            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'output', 'role':role, 'user': user, 'category':category, 'item':value}

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

    cat_param = quote_plus(category)
    response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/return")
def output(request: Request, category: str):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "return.html", {"category":category, "assortment": inventory[category]})

@app.post("/return")
async def return_post(request: Request):
    form = await request.form()
    print(form)
    category = form.get("category")

    role = request.cookies.get("role")
    user = request.cookies.get("user")

    for field_name, value in form.items():
        print(flow_log)
        if 'item' in field_name:
            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'return', 'role':role, 'user': user, 'category':category, 'item':value}

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

    response = RedirectResponse(url=f"/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/balance_sheet")
def balance_sheet(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request,"balance_sheet.html", {"flow_log": flow_log})

@app.get("/order_place")
def order_place(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request,"order_place.html", {"tabel_dict": tabel_dict})

@app.post("/order_place") 
async def order_place_post(request: Request, tabel: str = Form(...)):
    return templates.TemplateResponse(request,"order_goods.html", {"inventory": inventory, "tabel": tabel})

@app.post("/order_goods")
async def order_goods_post(request: Request):
    form = await request.form()
    print(form)

    role = request.cookies.get("role")
    user = request.cookies.get("user")

    for field_name, value in form.items():
        print(flow_log)
        if 'category' in field_name:
            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'order_stage_1', 'role':role, 'user': user, 'category':value}

        elif 'item' in field_name:
            flow_log[n+1]['item'] = value

        elif 'quantity' in field_name: 
            flow_log[n+1]['quantity'] = 0

        elif 'price' in field_name:
            flow_log[n+1]['price'] = value 

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

  
    response = RedirectResponse(url=f"/order_place", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

# This is the last line of the Code :)