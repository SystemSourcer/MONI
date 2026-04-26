# MONI
This is MONI, the Main Organsisational Networking Interface

## Descibtion
MONI originally came about from the idea of creating a sort of “Kassenka” version for the computer.  
However, even shortly after development began, the thinking went beyond this initial scope.  
Instead of using Tkinter to design a local GUI, the decision was made to to work with HTML.  
This enabels a multi-user environment within a local network. 



## Getting Started

### Build Docker image:
Open a terminal in the cloed Git repo folder or cd in it.  
Then execute:  
```bash
docker build -t moni ./
```

### Start the Docker container:
```bash 
docker run -it --rm -p 8000:8000 C:\Path\to\GitHub\MONI:/workspace moni bash
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

## License

## Acknowledgments