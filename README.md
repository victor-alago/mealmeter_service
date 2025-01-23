# mealmeter_service
Repo for meal meter services

## BETA DOCUMENTATION

`!!!! This is a beta documentation !!!!`

#### Setup:

- Complete .env file with required parameters

- Install all dependencies listed in the requirements file:
```bash
    pip install -r requirements.txt
```

- Start the application
```bash
    python3 -m uvicorn app.main:app --reload
```


#### AUTH ROUTES

- ##### Register
    - Route:
    ```js
        POST http://127.0.0.1:8000/auth/signup
    ```

    - Body:
    ```json
        {
            "email": "your_verifiable_email",
            "password": "your_password"
        }
    ```

    - Verification email is sent and registration is completed after verification.

    - Returned Details:
        1. user created sucessfully
        2. user id generated


- ##### Login
    - Route:
    ```js
        POST http://127.0.0.1:8000/auth/login
    ```

    - Body:
    ```json
        {
            "email": "your_registered_email",
            "password": "your_password"
        }
    ```

    - Returned Details:
        1. login successful message
        2. id_token
        3. refresh_token
        4. user's email