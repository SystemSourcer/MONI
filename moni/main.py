# Imports
import uuid
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
def print_order(order_key, address=None): #https://python-escpos.readthedocs.io/en/latest/api/escpos.html#escpos.escpos.Escpos.image
    """ 
    Prits the order on the corresponding printer (via category or addres if given)
    """
    order = order_history[order_key]
    keywords = keywords_dict[settings_dict['Language']]
    if address == None: printer = Network(settings_dict[f'Printer-{order['category']}'])
    else: printer = Network(address)
    printer.profile.media['width']['pixels'] = 567 # or 384, depending to the printer
    printer.set(align='center', bold = True, custom_size=True, width=2, height=2)
    printer.textln(settings_dict['Event'])
    printer.set(bold=False, custom_size=True, width=1, height=1)
    printer.textln(settings_dict['Host'])
    printer.set(align='left')
    printer.ln(1)
    printer.textln(datetime.now().strftime("%d. %B %Y %H:%M"))
    printer.textln(f'{keywords['order']}: {order_key}')
    printer.textln(f'{keywords['negotiator']}: {order['negotiator']} - {order['ordered']}')
    printer.textln(f'{keywords['organizer']}: {order['organizer']} - {order['prepared']}')
    printer.textln("-" * int(settings_dict['Bon_Row_Chars']))
    printer.set(bold = True, custom_size=True, width=2, height=2)
    for item in order['items']:
        printer.textln(f'{item['quantity']}x {item['item']} # {item['custom']}')

    printer.set(bold=False, custom_size=True, width=1, height=1)
    printer.textln("-" * int(settings_dict['Bon_Row_Chars']))
    printer.set(align='center')
    printer.textln(f'{keywords['place']}:')
    printer.set(bold = True, custom_size=True, width=8, height=8)
    printer.textln(f'{order['place']}')
    printer.set(bold=False, custom_size=True, width=1, height=1)
    # printer.qr(json.dumps(order, ensure_ascii=False, indent=2), size = 4,  center=True ) # defualt size = 3 # digital bon 7 ebon
    printer.cut(mode='PART', feed=False)
    printer.close()

def print_output(output, address): #https://python-escpos.readthedocs.io/en/latest/api/escpos.html#escpos.escpos.Escpos.image
    """ 
    Prits the output on the corresponding printer (via addres)
    """
    printer = Network(address)
    printer.profile.media['width']['pixels'] = 567 # or 384, depending to the printer
    printer.set(align='center', bold = True, custom_size=True, width=2, height=2)
    printer.textln(settings_dict['Event'])
    printer.set(bold=False, custom_size=True, width=1, height=1)
    printer.textln(settings_dict['Host'])
    printer.set(align='left')
    printer.ln(1)
    printer.textln(datetime.now().strftime("%d. %B %Y %H:%M"))
    printer.textln("-" * int(settings_dict['Bon_Row_Chars']))
    printer.set(bold = True, custom_size=True, width=2, height=2)
    for item in output:
        printer.textln(f'{item['quantity']}x {item['item']}')

    printer.set(bold=False, custom_size=True, width=1, height=1)
    printer.textln("-" * int(settings_dict['Bon_Row_Chars']))
    # printer.set(align='center')
    # printer.qr(json.dumps(order, ensure_ascii=False, indent=2), size = 4,  center=True ) # defualt size = 3 # digital bon 7 ebon
    printer.cut(mode='PART', feed=False)
    printer.close()

def print_message(message, address): #https://python-escpos.readthedocs.io/en/latest/api/escpos.html#escpos.escpos.Escpos.image
    """ 
    Prits a message on the corresponding printer (via category or addres if given)
    """
    keywords = keywords_dict[settings_dict['Language']]
    printer = Network(address)
    printer.profile.media['width']['pixels'] = 567 # or 384, depending to the printer
    printer.set(align='center', bold = True, custom_size=True, width=2, height=2)
    printer.textln(keywords['message'])
    printer.set(bold=False, custom_size=True, width=1, height=1)
    printer.textln(keywords['from'] + message['user'])
    printer.set(align='left')
    printer.ln(1)
    printer.textln(datetime.now().strftime("%d. %B %Y %H:%M"))
    printer.textln("-" * int(settings_dict['Bon_Row_Chars']))
    printer.textln(message['content'])
    printer.textln("-" * int(settings_dict['Bon_Row_Chars']))
    printer.cut(mode='PART', feed=False)
    printer.close()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_addr = s.getsockname()[0]
s.close()
qrc = qrcode.QRCode()
qrc.add_data('http://' + ip_addr + ':8000')
qrc.make()
qrc_img = qrc.make_image()
qrc_img.save('/workspace/moni/static/images/qrcode.png')

app = FastAPI()
app.mount("/static", StaticFiles(directory="moni/static"), name="static")
templates = Jinja2Templates(directory="./moni/templates")

role_dict = {
    'master': {'password': '887375daec62a9f02d32a63c9e14c7641a9a8a42e4fa8f6590eb928d9744b57bb5057a1d227e4d40ef911ac030590bbce2bfdb78103ff0b79094cee8425601f5'},
    'organizer': {'password': '90fbf0437ab78f1225d82922259cc59006d6f2da2b6ea775bb5e3d69e333c64fb64d0d1c534b6bf2c335fff54f036a4fe195ab95d74434c6ee7720a75c27ece0'},
    'negotiator': {'password': '5cfaeeaacc1626610030d4c4f2a701d2aba37fb28d5d861ab29707e5c9e4d0b6883abba4887ae9460bdd37195576a9eacf389948e2d295ef82b5ce59d63115f1'},
    'issuer': {'password': '90dace0b9ded9e083f602834e45aaaec05623d928d85dd41e61f70f9229629ad93ff29ecf6a2e3039f354cd94b279c50f63c2cee3c176c07126d028ee39bb705'},
}

keywords_dict = {'en':{'order':'Order', 'place':'Place', 'negotiator':'Negotiator', 'organizer':'Preparer', 'message':'Message', 'from':'from'}, 
                 'de':{'order':'Bestellung', 'place':'Platz', 'negotiator':'Besteller', 'organizer':'Vorbereiter', 'message':'Nachricht', 'from':'von'}
                }

last_subform_dict = dict()

try: 
    with open("/workspace/data/settings.json", "r", encoding="utf-8") as settings_file:
        settings_dict  = json.load(settings_file)

except: settings_dict = {'Event':'MONI-Event', 'Host':'Musikverein Scharnestetten e.V. 1925', 'Issuer': 'Off', 'Language': 'en', 'Bon_Row_Chars': 48}

try:
    with open("/workspace/data/place.json", "r", encoding="utf-8") as place_file:
        place_dict  = json.load(place_file)

except:
    place_dict = {'To-Go':False, 'Take':False, 'cat_1':False, 'cat_2':False, 'cat_3':False, 'cat_4':False, 'cat_5':False, 'cat_6':False, 'cat_7':False, 'cat_8':False}
    for letter in ['A','B','C','D','E','F','G','H']:
        for number in range(10):
            place_dict[letter+'-'+str(number)]=False

try:
    with open("/workspace/data/inventory.json", "r", encoding="utf-8") as inventory_file:
        inventory = json.load(inventory_file)

except: inventory = {}

try:
    with open("/workspace/data/flow_log.json", "r", encoding="utf-8") as flow_log_file:
        flow_log  = json.load(flow_log_file)
    
    flow_log = {int(k): v for k, v in flow_log.items()} # because key are streings after loding but int wen createt thru the system

except: flow_log = {0: {'time': datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type': 'init', 'role': 'System', 'user': 'System', 'category':'Init', 'item': 'Init', 'quantity': '0', 'price': '0'}} # need init entry becaus counts with last entry...

try:
    with open("/workspace/data/order_history.json", "r", encoding="utf-8") as order_history_file:
        order_history = json.load(order_history_file)
    
    order_history = {int(k): v for k, v in order_history.items()} # because key are strings after loding but int wen createt thru the system

except: order_history = {0: {'place':'init', 'category':'Init', 'items':[{'category':'Init', 'item':'Init', 'quantity':'2', 'custom':'No real Order'},{'category':'Init_1', 'item':'Init_1', 'quantity':'1', 'custom':'No real Order'},{'category':'Init_2', 'item':'Init_2', 'quantity':'3', 'custom':'No real Order'}], 'negotiator':'System_n', 'organizer':'System_o' ,'issuer':'System_i', 'ordered':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'prepared':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'issued':datetime.now().strftime("%Y-%m-%dT%H:%M")}}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("/workspace/moni/static/images/favicon.ico")


@app.get("/")
def root():
    return RedirectResponse(url="/login")


@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/login.html")


@app.post("/login")
def login_post(request: Request, role: str = Form(...), user: str = Form(...), password: str = Form(...)):
    
    if not role in role_dict.keys() or role_dict[role]["password"] != hashlib.sha512((password).encode()).hexdigest():
        return templates.TemplateResponse(request, f"{settings_dict['Language']}/login.html", {"error": "Invalid passwort (for selected role)"})
    
    if role == 'issuer' and not settings_dict["issuer"]:
        return templates.TemplateResponse(request, f"{settings_dict['Language']}/login.html", {"error": "Issuer is not activated..."})

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=hashlib.sha512((password).encode()).hexdigest(), httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/dashboard")
def dashboard(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/dashboard.html", {"role": role, "user": user, "inventory":inventory, "settings": settings_dict})


@app.post("/dashboard")
def dashboard_post(request: Request, category: str = Form(...), action: str = Form(...)):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    cat_param = quote_plus(category)
    if action == "Output":
        response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    
    if action == "Return":
        response = RedirectResponse(url=f"/return?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)

    if action == "Set_Price":
        response = RedirectResponse(url=f"/set_price?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)

    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("role")
    response.delete_cookie("password")
    response.delete_cookie("user")
    return response


@app.get("/input")
def input(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/input.html", {"inventory": inventory})


@app.post("/input")
def input_post(request: Request, category: str = Form(...), item: str = Form(...), quantity: str = Form(...)):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    if category not in inventory.keys(): 
        inventory[category] = list()
        place_added = False
        for key in list(place_dict.keys()):
            if 'cat' in key and not place_added: 
                place_dict[category] = place_dict.pop(key)
                place_added = True

            else: place_dict[key] = place_dict.pop(key)

    if item not in [id['item'] for id in inventory[category]]:
        inventory[category].append({'item':item,'quantity':0,'ordered':0,'price':0})

    for id in inventory[category]:
        if id['item'] == item:
            id['quantity'] += int(quantity)

    print(inventory[category])

    n = int(next(reversed(flow_log)))
    flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'Input', 'role':role, 'user': user, 'category':category, 'item':item, 'quantity':quantity}

    with open("/workspace/data/place.json", "w", encoding="utf-8") as place_file:
        json.dump(place_dict, place_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/set_price")
def set_price(request: Request, category: str):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/set_price.html", {"assortment": inventory[category]})


@app.post("/set_price") 
async def set_price_post(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()

    for field_name, value in form.items():
        print(f"New price for {field_name}: {value}")
        for idl in inventory.values():
            for id in idl:
                if id['item'] == field_name: id['price'] = value
                   
    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/settings")
def settings(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    
    for key in inventory.keys():
        if f'Order-{key}' not in settings_dict: settings_dict[f'Order-{key}'] = 'Off'  # color code
        if f'Color-{key}' not in settings_dict: settings_dict[f'Color-{key}'] = ''  # color code
        if f'Printer-{key}' not in settings_dict: settings_dict[f'Printer-{key}'] = ''  # Off or Ip-Adress
        if f'Order_Bon-{key}' not in settings_dict: settings_dict[f'Order_Bon-{key}'] = 'Off' # Off, Order or Prepare
        if f'Output_Bon-{key}' not in settings_dict: settings_dict[f'Output_Bon-{key}'] = 'Off' # Off or On
        if f'Auto_Prepare-{key}' not in settings_dict: settings_dict[f'Auto_Prepare-{key}'] = '0' # time in seconds

    del_key_list = []
    for key in settings_dict.keys():
        if 'Order-' in key and key.removeprefix('Order-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Color-' in key and key.removeprefix('Color-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Printer-' in key and key.removeprefix('Printer-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Order_Bon-' in key and key.removeprefix('Order_Bon-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Output_Bon-' in key and key.removeprefix('Output_Bon-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
        if 'Auto_Prepare-' in key and key.removeprefix('Auto_Prepare-') not in inventory.keys(): del_key_list.append(key) # remove settings for no longer existing categorys
    
    #print(del_key_list)
    for key in del_key_list:
        del [settings_dict[key]]

    return templates.TemplateResponse(request, f"{settings_dict['Language']}/settings.html", {"settings": settings_dict})


@app.post("/settings")
async def settings_post(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()

    for field_name, value in form.items():
        if value == "#000000": value = '' # if no value choosen, then empy sring... this wil lead to deafult in java scipt
        print(f"New setting for {field_name}: {value}")
        settings_dict[field_name] = value

    if settings_dict['Language'] == 'de': locale.setlocale(locale.LC_TIME, "de_DE.UTF-8") # for german month names

    with open("/workspace/data/settings.json", "w", encoding="utf-8") as settings_file:
        json.dump(settings_dict, settings_file, ensure_ascii=False, indent=2)    

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/place_management")
def place_management(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/place_management.html", {"place_dict": place_dict})


@app.post("/place_management") 
async def place_management_post(request: Request, place: str = Form(...)):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    if place_dict[place] == True: place_dict[place] = False
    else: place_dict[place] = True

    with open("/workspace/data/place.json", "w", encoding="utf-8") as place_file:
        json.dump(place_dict, place_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url="/place_management", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/output")
def output(request: Request, category: str):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    prepare_order_key_list = [key for key, order in order_history.items() if order['organizer'] == user and order['prepared'] == None]
    # print(prepare_order_key_list)
    if not prepare_order_key_list: 
    
        open_order_key_list = [key for key, order in order_history.items() if order['organizer'] == None and order['category'] == category]
        # print(open_order_key_list, category)
        for n, key in enumerate(open_order_key_list):
            if n == 0: 
                order_history[key]['organizer'] = user
                prepare_order_key_list = [key]

            elif n < 10 and order_history[key]['place'] == order_history[prepare_order_key_list[0]]['place']: 
                order_history[key]['organizer'] = user
                prepare_order_key_list.append(key)
                
            if len(prepare_order_key_list) >= 3: break

    prepare_order_list = [order_history[key] for key in prepare_order_key_list]

    return templates.TemplateResponse(request, f"{settings_dict['Language']}/output.html", {"form_uuid":str(uuid.uuid4()), "category":category, "inventory": inventory, "prepare_order_key_list":prepare_order_key_list, "prepare_order_list": prepare_order_list, "settings": settings_dict})


@app.post("/output")
async def output_post(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()
    print(form)
    last_subform_dict[user] = dict(form)
    category = form.get("category")

    output_item_list = list()

    for field_name, value in form.items():
        if 'item' in field_name:
            if 'ret' in field_name: out_type = 'Return'
            else: out_type = 'Output'
            if 'free' in field_name: out_type = out_type + '_free'

            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':out_type, 'role':role, 'user': user, 'category':category, 'item':value}

        elif 'quantity' in field_name: 
            flow_log[n+1]['quantity'] = value
            output_item_list.append({'item':flow_log[n+1]['item'], 'quantity':flow_log[n+1]['quantity']})
            for idl in inventory.values():
                for id in idl:
                    if id['item'] in field_name: id['quantity'] -= int(value)

        elif 'price' in field_name:
            flow_log[n+1]['price'] = value 


    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    if settings_dict[f'Output_Bon-{category}'] == 'On': print_output(output_item_list,settings_dict[f'Printer-{category}'])

    #cat_param = quote_plus(category)
    response = RedirectResponse(url=f"/check_output", status_code=status.HTTP_303_SEE_OTHER)
    #response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.post("/prepared")
async def prepared_post(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()
    print(form)

    order_key = int(form.get("order_key"))
    category = form.get("category")
    print(category)

    order = order_history[order_key]
    order['organizer'] = user
    order['prepared'] = datetime.now().strftime("%Y-%m-%dT%H:%M")

    for item in order['items']:
        for item_dict in inventory[category]:
            if item_dict['item'] == item['item']: 
                item_dict['ordered'] -= int(item['quantity'])
                item_dict['quantity'] -= int(item['quantity'])

    if settings_dict[f'Order_Print-{category}'] == 'Prepare': print_order(order_key)

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    cat_param = quote_plus(category)
    response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/balance_sheet")
def balance_sheet(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/balance_sheet.html", {"flow_log": flow_log, "inventory": inventory})


@app.get("/order_place")
def order_place(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    return templates.TemplateResponse(request, f"{settings_dict['Language']}/order_place.html", {"place_dict": place_dict})


@app.post("/order_place") 
async def order_place_post(request: Request, place: str = Form(...)):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    return templates.TemplateResponse(request,f"{settings_dict['Language']}/order_goods.html", {"form_uuid":str(uuid.uuid4()),"place": place, "inventory": inventory, "settings": settings_dict})


@app.post("/order_goods")
async def order_goods_post(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()
    last_subform_dict[user] = dict(form)
    print(form)

    itemwise_order_list = []
    for field_name, value in form.items():
        
        if 'category' in field_name:
            n = int(next(reversed(flow_log)))
            flow_log[n+1] = {'time':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'type':'Order', 'role':role, 'user': user, 'category':value}
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
                    if id['item'] in field_name:
                        if settings_dict[f'Order_Bon-{flow_log[n+1]['category']}'] == 'Order': id['quantity'] -= int(value)
                        else: id['ordered'] += int(value)
            
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
        
        if catwise_order:
            order_history[n+1] = {'place':form.get('place'), 'category':key,  'items':catwise_order, 'negotiator':user, 'organizer':None, 'issuer':None, 'ordered':datetime.now().strftime("%Y-%m-%dT%H:%M"), 'prepared':None, 'issued': None}
            if settings_dict[f'Order_Bon-{key}'] == 'Order': 
                order_history[n+1]['organizer'] = 'direct_print'
                print_order(n+1)

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/inventory.json", "w", encoding="utf-8") as inventory_file:
        json.dump(inventory, inventory_file, ensure_ascii=False, indent=2)

    with open("/workspace/data/flow_log.json", "w", encoding="utf-8") as flow_log_file:
        json.dump(flow_log, flow_log_file, ensure_ascii=False, indent=2)

    response = RedirectResponse(url=f"/check_order", status_code=status.HTTP_303_SEE_OTHER)
    #response = RedirectResponse(url=f"/order_place", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/issue")
def issue(request:Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    issue_order_key_list = [key for key, order in order_history.items() if order['issuer'] == user and order['issued'] == None]
    
    if not issue_order_key_list: 
        prepare_order_key_list = [key for key, order in order_history.items() if order['organizer']!= None and order['issued'] == None]
        for n, key in enumerate(prepare_order_key_list):
            if n == 0: 
                order_history[key]['issuer'] = user
                issue_order_key_list = [key]

            elif n < 10 and order_history[key]['place'] == order_history[issue_order_key_list[0]]['palce']: 
                order_history[key]['issuer'] = user
                issue_order_key_list.append(key)
                
            if len(issue_order_key_list) >= 3: break


    issue_order_list = [order_history[key] for key in issue_order_key_list]

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    return templates.TemplateResponse(request, f"{settings_dict['Language']}/issue.html", {"issue_order_key_list":issue_order_key_list, "issue_order_list": issue_order_list})


@app.post("/issue")
async def issue_post(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()
    print(form)

    action = form.get("action")

    if action == "Issue_Last":
        last_issue_key = [key for key, i in order_history.items() if i['issuer'] == user and i['issued'] != None ][-1]
        order_history[last_issue_key]['issued'] = None
        if order_history[last_issue_key]['prepared'] == 'auto_issue_log': order_history[last_issue_key]['prepared'] = None

        response = RedirectResponse(url=f"/issue", status_code=status.HTTP_303_SEE_OTHER)
    
    else:   
        order_key = int(form.get("order_key"))
        
        order = order_history[order_key]
        if order['prepared'] == None: order['prepared'] = 'auto_issue_log'
        order['issued'] = datetime.now().strftime("%Y-%m-%dT%H:%M")

    with open("/workspace/data/order_history.json", "w", encoding="utf-8") as order_hisotry_file:
        json.dump(order_history, order_hisotry_file, ensure_ascii=False, indent=2)

    if action == "Issue_Next": response = RedirectResponse(url=f"/issue", status_code=status.HTTP_303_SEE_OTHER)
    elif action == "Issue_Dashboard": response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/test_print")
def test_print(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
   
    printer_list = []
    for key, val in settings_dict.items():
        if 'Printer-' in key and val != '': printer_list.append({'printer':key, 'address':val}) 

    if printer_list:
        return templates.TemplateResponse(request,f"{settings_dict['Language']}/test_print.html", {"printers": printer_list})
    else:
        return templates.TemplateResponse(request, f"{settings_dict['Language']}/test_print.html", {"error": "Bon printing is not activated..."})


@app.post("/test_print")
async def post_test_print(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()

    address = form.get("address")
    print_order(0,address) # 0 is the init system order

    response = RedirectResponse(url=f"/test_print", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/check_output")
def check(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    return templates.TemplateResponse(request, f"{settings_dict['Language']}/check_output.html", {"last_form": last_subform_dict[user]})

@app.post("/check_output")
async def post_check(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    form = await request.form()
    category = form.get('category')

    cat_param = quote_plus(category)
    response = RedirectResponse(url=f"/output?category={cat_param}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response


@app.get("/check_order")
def check(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 

    return templates.TemplateResponse(request, f"{settings_dict['Language']}/check_order.html", {"last_form": last_subform_dict[user]})

@app.post("/check_order")
async def post_check(request: Request):
    role = request.cookies.get("role")
    password = request.cookies.get("password")
    user = request.cookies.get("user")
    if not role or password != role_dict[role]["password"]: return RedirectResponse(url="/login") 
    
    response = RedirectResponse(url=f"/order_place", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="role", value=role, httponly=True, samesite="lax")
    response.set_cookie(key="password", value=password, httponly=True, samesite="lax")
    response.set_cookie(key="user", value=user, httponly=True, samesite="lax")
    return response





# This is the last line of the Code :)