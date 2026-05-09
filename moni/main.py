# Imports
import json 
import locale
import socket
import qrcode
import hashlib
from datetime import datetime
from escpos.printer import Network
from urllib.parse import quote_plus
from fastapi import FastAPI, Request, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

# Functions
def print_bon(order_key): #https://python-escpos.readthedocs.io/en/latest/api/escpos.html#escpos.escpos.Escpos.image
    """ 
    Prits the order on the corresponding printer (via category)
    """
    order = order_history[order_key]
    printer = Network(settings_dict[f'Printer-{order['category']}'])
    printer.set(align='center', bold = True, width=2, height=2)
    printer.textln(settings_dict['Event'])
    printer.set(bold=False, width=1, height=1)
    printer.textln(settings_dict['Host'])
    printer.set(align='left')
    printer.ln(1)
    printer.text(datetime.now().strftime("%d. %B %Y"))
    printer.set(align='right')
    printer.textnl(datetime.now().strftime("%H:%M"))
    printer.qr(json.dumps(order))
    #printer.image('/workspace/moni/static/favicon.ico', high_density_vertical=False, high_density_horizontal=False, impl='graphics')
    printer.cut()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_addr = s.getsockname()[0]
s.close()
qrc = qrcode.QRCode()
qrc.add_data('http://' + ip_addr + ':8000')
qrc.make()
qrc_img = qrc.make_image()
qrc_img.save('/workspace/moni/static/images/qrcode.png')


#p1 = Network("192.168.178.14") 
#bon(p1)
app = FastAPI()
app.mount("/static", StaticFiles(directory="moni/static"), name="static")
templates = Jinja2Templates(directory="./moni/templates")

role_dict = {
    'master': {'password': '887375daec62a9f02d32a63c9e14c7641a9a8a42e4fa8f6590eb928d9744b57bb5057a1d227e4d40ef911ac030590bbce2bfdb78103ff0b79094cee8425601f5'},
    'organizer': {'password': '90fbf0437ab78f1225d82922259cc59006d6f2da2b6ea775bb5e3d69e333c64fb64d0d1c534b6bf2c335fff54f036a4fe195ab95d74434c6ee7720a75c27ece0'},
    'negotiator': {'password': '5cfaeeaacc1626610030d4c4f2a701d2aba37fb28d5d861ab29707e5c9e4d0b6883abba4887ae9460bdd37195576a9eacf389948e2d295ef82b5ce59d63115f1'},
    'issuer': {'password': '90dace0b9ded9e083f602834e45aaaec05623d928d85dd41e61f70f9229629ad93ff29ecf6a2e3039f354cd94b279c50f63c2cee3c176c07126d028ee39bb705'},
}

keywords_dict = {'English':{'order':'Order', 'place':'Place', 'negotiator':'negotiator'}, 
                 'German':{'order':'Order', 'place':'Place', 'negotiator':'negotiator'}}


try: 
    with open("/workspace/data/settings.json", "r", encoding="utf-8") as settings_file:
        settings_dict  = json.load(settings_file)

except: settings_dict = {'Event':'MONI-Event', 'Host':'Musikverein Scharnestetten e.V. 1925', 'Issuer': False, 'Bon': True, 'Bon_Language': 'German'}

place_dict = dict()
for letter in ['A','B','C','D','E','F','G','H']:
    for number in range(10):
        place_dict[letter+str(number)]=False

try:
    with open("/workspace/data/inventory.json", "r", encoding="utf-8") as inventory_file:
        inventory = json.load(inventory_file)

except: inventory = dict()

try:
    with open("/workspace/data/flow_log.json", "r", encoding="utf-8") as flow_log_file:
        flow_log  = json.load(flow_log_file)
    
    flow_log = {int(k): v for k, v in flow_log.items()} # because key are streings after loding but int wen createt thru the system

except: flow_log = {0: {'time': datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type': 'init', 'role': 'System', 'user': 'System', 'category':'Init', 'item': 'Init', 'quantity': '0', 'price': '0'}} # need init entry becaus counts with last entry...

try:
    with open("/workspace/data/order_history.json", "r", encoding="utf-8") as order_history_file:
        order_history = json.load(order_history_file)
    
    order_history = {int(k): v for k, v in order_history.items()} # because key are strings after loding but int wen createt thru the system

except: order_history = {0: {'place':'init', 'category':'Init', 'items':[{'category':'Init', 'item':'Init', 'quantitiy':'2', 'custom':'No real Order'},{'category':'Init_1', 'item':'Init_1', 'quantitiy':'1', 'custom':'No real Order'},{'category':'Init_2', 'item':'Init_2', 'quantitiy':'3', 'custom':'No real Order'}], 'negotiator':'System_n', 'organizer':'System_o' ,'issuer':'System_i', 'ordered':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'prepared':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'issued':datetime.now().strftime("%Y-%m-%dT%H:%M")}}

print('Inventory:',inventory)
print('Log_Flow:',flow_log)
print('Oder_History:',order_history)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("/workspace/moni/static/images/favicon.ico")

@app.get("/")
def root():
    return RedirectResponse(url="/login")

@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse(request,"login.html")

@app.post("/login")
def login_post(request: Request, role: str = Form(...), user: str = Form(...), password: str = Form(...)):
    
    if not role in role_dict.keys() or role_dict[role]["password"] != hashlib.sha512((password).encode()).hexdigest():
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid passwort (for selected role)"})
    
    if role == 'issuer' and not settings_dict["issuer"]:
        return templates.TemplateResponse(request, "login.html", {"error": "Issuer is not activated..."})

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

    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
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
    return templates.TemplateResponse(request, "input.html", {"inventory": inventory})

@app.post("/input")
def input_post(request: Request, category: str = Form(...), item: str = Form(...), quantity: str = Form(...)):
    role = request.cookies.get("role")
    user = request.cookies.get("user")

    if category not in inventory.keys(): inventory[category] = list()
    
    if item not in [id['item'] for id in inventory[category]]:
        inventory[category].append({'item':item,'quantity':0,'ordered':0,'price':0})

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
        print(f"New price for {field_name}: {value}")
        for idl in inventory.values():
            for id in idl:
                if id['item'] == field_name: id['price'] = value
    
    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/settings")
def settings(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    if settings_dict['Bon']:
        for key in inventory.keys():
            if f'Printer-{key}' not in settings_dict: settings_dict[f'Printer-{key}'] = None  # None or Ip-Adress
            if f'Auto_Print-{key}' not in settings_dict: settings_dict[f'Auto_Print-{key}'] = False # True or False
            if f'Auto_Prepare-{key}' not in settings_dict: settings_dict[f'Auto_Prepare-{key}'] = None # None or time in seconds

    del_key_list = []
    for key in settings_dict.keys():
        if 'Printer-' in key and key.removeprefix('Printer-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Direct_Print-' in key and key.removeprefix('Direct_Print-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Auto_Prepare-' in key and key.removeprefix('Auto_Prepare-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
    
    for key in del_key_list:
        del [settings_dict[key]]

    return templates.TemplateResponse(request, "settings.html", {"settings": settings_dict})

@app.post("/settings")
async def settings_post(request: Request):
    form = await request.form()

    for field_name, value in form.items():
        print(f"New setting for {field_name}: {value}")
        settings_dict[field_name] = value

    if settings_dict['Bon_Language'] == 'Gemran': locale.setlocale(locale.LC_TIME, "de_DE.UTF-8") # for german month names

    with open("/workspace/data/settings.json", "w", encoding="utf-8") as settings_file:
        json.dump(settings_dict, settings_file, ensure_ascii=False, indent=2)    

    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/place_management")
def place_management(request: Request):
    role = request.cookies.get("role")
    if not role: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "place_management.html", {"place_dict": place_dict})

@app.post("/place_management") 
async def place_management_post(request: Request, place: str = Form(...)):
    if place_dict[place] == True: place_dict[place] = False
    else: place_dict[place] = True
    
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    response = RedirectResponse(url="/place_management", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/output")
def output(request: Request, category: str):
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    if not role: return RedirectResponse(url="/login")

    prepare_order_key_list = [key for key, order in order_history.items() if order['organizer'] == user and order['prepared'] == None]
    if not prepare_order_key_list: 
    
        open_order_key_list = [key for key, order in order_history.items() if order['organizer'] == None]
        for n, key in enumerate(open_order_key_list):
            if n == 0: 
                order_history[key]['organizer']
                prepare_order_key_list = list(key)

            elif n < 10 and order_history[key]['place'] == order_history[prepare_order_key_list[0]]['palce']: 
                order_history[key]['organizer'] = user
                prepare_order_key_list.append(key)
                
            if len(prepare_order_key_list) >= 3: break

    prepare_order_list = [order_history[key] for key in prepare_order_key_list]

    assigned_order_key_list = [key for key, order in order_history.items() if order["issuer"] != None and order["prepared"]== None and order['category'] == category]
    assigned_order_list = [order_history[order_key] for order_key in assigned_order_key_list]
    print(assigned_order_list)
    return templates.TemplateResponse(request, "output.html", {"category":category, "assortment": inventory[category], "prepare_order_key_list":prepare_order_key_list, "prepare_order_list": prepare_order_list})

@app.post("/output")
async def output_post(request: Request):
    form = await request.form()
    print(form)
    category = form.get("category")
    print(category)
    role = request.cookies.get("role")
    user = request.cookies.get("user")

    for field_name, value in form.items():
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

@app.post("/prepared")
async def prepared_post(request: Request):
    form = await request.form()
    print(form)

    order_key = int(form.get("order_key"))
    category = form.get("category")
    print(category)

    role = request.cookies.get("role")
    user = request.cookies.get("user")

    order = order_history[order_key]
    order['organizer'] = user
    order['prepared'] = datetime.now().strftime("%Y-%m-%dT%H:%M")

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    cat_param = quote_plus(category)
    response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/return")
def output_return(request: Request, category: str):
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
    return templates.TemplateResponse(request,"order_place.html", {"place_dict": place_dict})

@app.post("/order_place") 
async def order_place_post(request: Request, place: str = Form(...)):
    return templates.TemplateResponse(request,"order_goods.html", {"inventory": inventory, "place": place})

@app.post("/order_goods")
async def order_goods_post(request: Request):
    form = await request.form()
    print(form)

    role = request.cookies.get("role")
    user = request.cookies.get("user")

    itemwise_order_list = []
    for field_name, value in form.items():
        
        if 'category' in field_name:
            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'order', 'role':role, 'user': user, 'category':value}
            itemwise_order = dict()
            itemwise_order['category'] = value

        elif 'item' in field_name:
            flow_log[n+1]['item'] = value
            itemwise_order['item'] = value

        elif 'quantity' in field_name: 
            flow_log[n+1]['quantity'] = value
            itemwise_order['quantity'] = value
            for idl in inventory.values():
                for id in idl:
                    if id['item'] in field_name: id['ordered'] += int(value)
            
        elif 'price' in field_name:
            flow_log[n+1]['price'] = value 

        elif 'custom' in field_name:
            itemwise_order['custom'] = value
            itemwise_order_list.append(itemwise_order)

    for key in inventory.keys():
        n = int(next(reversed(order_history)))
        catwise_order = []
        for itemwise_order in itemwise_order_list:
            if itemwise_order['category'] == key: catwise_order.append(itemwise_order)
        
        order_history[n+1] = {'place':form.get('place'), 'category':key,  'items':catwise_order, 'negotiator':user, 'organizer':None, 'issuer':None, 'ordered':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'prepared':None, 'issued': None}

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url=f"/order_place", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response

@app.get("/issue")
def issue(request:Request):
    role = request.cookies.get("role")
    user = request.cookies.get("user")
    if not role: return RedirectResponse(url="/login")
    issuer_order_list = [key for key, order in order_history.items() if order['issuer'] == user and order['issued'] == None]
    if issuer_order_list: return templates.TemplateResponse(request,"issue.html", {"order_key": issuer_order_list[0], "order": order_history[issuer_order_list[0]]})
    order_key = 0
    for k,o in order_history.items():
        if o['issuer'] == None: 
            o['issuer'] = user
            order_key = k
            break

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    return templates.TemplateResponse(request,"issue.html", {"order_key":order_key, "order": order_history[order_key]})

@app.post("/issue")
async def issue_post(request: Request):
    form = await request.form()
    print(form)

    action = form.get("action")

    role = request.cookies.get("role")
    user = request.cookies.get("user")

    if action == "Issue_Last":
        last_issue_key = [key for key, i in order_history.items() if i['issuer'] == user and i['issued'] != None ][-1]
        order_history[last_issue_key]['issued'] = None
        if order_history[last_issue_key]['prepared'] == 'auto_issue_log': order_history[last_issue_key]['prepared'] = None

        n = int(next(reversed(flow_log)))
        for item in order_history[last_issue_key]['items']:
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'order_stage_3', 'role':role, 'user': user, 'category':item['category'], 'item':item['item'], 'quantity':- int(item['quantity']), 'price':0}
            for id in inventory[item['category']]:
                if id['item'] == item['item']:
                        id['quantity'] += int(item['quantity'])
                        id['ordered'] += int(item['quantity'])

        response = RedirectResponse(url=f"/issue", status_code=status.HTTP_303_SEE_OTHER)
    
    else:   
        order_key = int(form.get("order_key"))
        for field_name, value in form.items():
            if 'category' in field_name:
                n = int(next(reversed(flow_log)))
                flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'order_stage_3', 'role':role, 'user': user, 'category':value}

            elif 'item' in field_name:
                flow_log[n+1]['item'] = value

            elif 'quantity' in field_name: 
                flow_log[n+1]['quantity'] = value
                for idl in inventory.values():
                    for id in idl:
                        if id['item'] in field_name: 
                            id['quantity'] -= int(value)
                            id['ordered'] -= int(value)
        
        order = order_history[order_key]
        if order['prepared'] == None: order['prepared'] = 'auto_issue_log'
        order['issued'] = datetime.now().strftime("%Y-%m-%dT%H:%M")

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    if action == "Issue_Next": response = RedirectResponse(url=f"/issue", status_code=status.HTTP_303_SEE_OTHER)
    elif action == "Issue_Dashboard": response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response













# This is the last line of the Code :)