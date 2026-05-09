
# MONI 
This is MONI, the Main Organsisational Networking Interface  

# Logo / Icon
![Icon](moni/static/images/favicon.ico)  

## Descibtion
MONI originally came about from the idea of creating a sort of “[Kassenka](https://play.google.com/store/apps/details?id=com.ankele.kassenka&hl=de)” version for the computer.  
However, even shortly after development began, the thinking went beyond this initial scope.  
Instead of using [Tkinter](https://docs.python.org/fr/3/library/tkinter.html) to design a local GUI, the decision was made to to work with HTML.  
This enabels a multi-user environment within a local network. 

## Getting Started

### Build Docker image:
Open a terminal in the cloned Git repo folder or cd in it.  
Then execute:  
```bash
docker build -t moni ./
```

### Start the Docker container:
On WIndows (only without printers and qrcode)
```bash 
docker run -it --rm -p 8000:8000 C:\Path\to\GitHub\MONI:/workspace moni bash
```
On Linux (with all functions)
```bash 
docker run -it --rm --net=host /Path/to/GitHub/MONI:/workspace moni bash
```

### Creat password hashs
So far MONI works with a quit basic and simple password handling.  
The Passwords for Admin and Worker are saved directly in the python file as hashed srings. 
You can create a new password with:
```python
import hashlib
print(hashlib.sha512(('Your_PW').encode()).hexdigest())
```
Then replace the hashed string in the python file with it to update the password.

### Start MONI
```bash
uvicorn moni.main:app --reload --host 0.0.0.0
```

## Authors
This project / repo was developed by SystemSourcer.

## License (LRU)
The entire project is under a LRU  (limited right of use) License. 
More information in the [License file](LICENSE.md)...

## Acknowledgments
This project would not have been possible without the support of the [Musikverein Scharenstetten e.V. 1925](https://mv-scharenstetten.de/). I am deeply grateful for their initiative in conceiving this project and their ongoing dedication to its success. Their collaborative spirit and constructive feedback have significantly contributed to the quality and direction of this work.  
I would also like to thank Stefan Ankele, the programmer and publisher of the [Kassenka](https://play.google.com/store/apps/details?id=com.ankele.kassenka&hl=de) app. The exchange with him was instrumental in shaping the initial concept and design of this project. His insights and expertise have greatly influenced the approach of this project. 