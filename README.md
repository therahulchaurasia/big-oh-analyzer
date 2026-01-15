COMMAND TO RUN THE CODE

TO INSTALL THE PACKAGES:

```bash
pip install -r requirements.txt
```

TO RUN THE CODE:

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

```bash
Windows: venv\Scripts\activate
Linux/Mac: source venv/bin/activate
```

We are using uvicorn to run the application:

```bash
uvicorn main:app --reload
```
