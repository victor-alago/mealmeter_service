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



#### FOOD LOG ROUTES


#### PROFILE ROUTES

- ##### Create Profile
    - Route:
    ```js
        POST http://127.0.0.1:8000/users/profile
    ```

    - Body:
    ```json
       {
            "gender": "male",
            "birthdate": "2000-01-01",
            "height_cm": 180.0,
            "weight_kg": 80.0,
            "activity_level": "moderately active",
            "goal": "weight maintenance",
            "diet_type": "standard",
            "food_preferences": ["chicken", "rice"],
            "allergies": ["nuts"],
            "health_metrics": {
                "medical_conditions": ["none"],
                "medications": ["none"]
            }
        }
    ```
    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        {
            "message": "Profile created successfully",
            "profile_data": {
                "gender": "male",
                "birthdate": "2000-01-01",
                "height_cm": 180.0,
                "weight_kg": 80.0,
                "activity_level": "moderately active",
                "goal": "weight maintenance",
                "diet_type": "standard",
                "food_preferences": ["chicken", "rice"],
                "allergies": ["nuts"],
                "health_metrics": {
                    "medical_conditions": ["none"],
                    "medications": ["none"]
                },
                "is_setup": true
            }
        }
    ```
    - 201 Success Code


- ##### Update Profile
    - Route:
    ```js
        PUT http://127.0.0.1:8000/users/profile
    ```

    - Body:
    ```json
       {
            "weight_kg": 82.0,
            "food_preferences": ["fish", "vegetables"]
        }
    ```
    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        {
            "message": "Profile updated successfully"
        }
    ```
    - 200 Ok Code


#### INSIGHTS ROUTES

- ##### Get Nutrition Insights
    - Route:
    ```js
        GET http://127.0.0.1:8000/insights/nutrition
    ```

    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        {
            "tdee": 2500.0,
            "protein_grams": 150.0,
            "carbs_grams": 250.0,
            "fats_grams": 55.0
        }
    ```
    - 200 Ok Code


#### FOOD SEARCH ROUTES

- ##### Search Food
    - Route:
    ```js
        GET http://127.0.0.1:8000/food/search?query=apple
    ```

    - Query Params:
    ```
        query: "food to search"
    ```

    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        {
            "results": [
                {
                    "food_id": "54321",
                    "food_name": "Apple",
                    "food_description": "per 1 medium apple (approx 182g) - Calories: 95kcal | Carbs: 25.13g | Fat: 0.3g | Protein: 0.47g",
                },
                {
                    "food_id": "12345",
                    "food_name": "Apple Juice",
                    "food_description": "per 8 fl oz (240ml) - Calories: 110kcal | Carbs: 28g | Fat: 0g | Protein: 0g",
                }
            ]
        }
    ```
    - 200 Ok Code

- ##### Add Food
    - Route:
    ```js
        POST http://127.0.0.1:8000/food-log/entry
    ```

    - Body:
    ```json
        {
            "food_name": "Pasta",
            "meal_type": "Lunch",
            "calories": 750,
            "serving_size": "1 plate",
            "date": "2024-01-25"
        }
    ```
    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        {
            "message": "Food entry logged successfully"
        }
    ```
    - 201 Success Code


- ##### Get Food By Day
    - Route:
    ```js
        GET http://127.0.0.1:8000/food-log/daily/2024-01-25   //date format -> yyyy-mm-dd
    ```

    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        [
            {
                "date": "2024-01-25",
                "total_calories": 750.0,
                "target_calories": 2000.0,
                "remaining_calories": 1250.0,
                "meals": {
                    "breakfast": [
                        {
                            "food_name": "Oatmeal with banana",
                            "calories": 300.0,
                            "serving_size": "1 bowl"
                        }
                    ],
                    "lunch": [
                        {
                            "food_name": "Chicken Caesar Salad",
                            "calories": 450.0,
                            "serving_size": "1 plate"
                        }
                    ],
                    "dinner": [],
                    "snacks": [],
                    "drinks": []
                }
            }
        ]
    ```
    - 200 Ok Code


- ##### Get All Food Logged By User
    - Route:
    ```js
        GET http://127.0.0.1:8000/food-log/all
    ```

    - Remember to add Auth Token in the Header !

    - Returned Details:
    ```json
        [
            {
                "date": "2024-01-27",
                "total_calories": 900.0,
                "target_calories": 2000.0,
                "remaining_calories": 1100.0,
                "meals": {
                    "breakfast": [],
                    "lunch": [],
                    "dinner": [],
                    "snacks": [
                        {
                            "food_name": "Mayonnaise Pam",
                            "calories": 450.0,
                            "serving_size": "1 plate"
                        }
                    ],
                    "drinks": [
                        {
                            "food_name": "Orange Juice",
                            "calories": 450.0,
                            "serving_size": "1 bottle"
                        }
                    ]
                }
            },
            {
                "date": "2024-01-25",
                "total_calories": 750.0,
                "target_calories": 2000.0,
                "remaining_calories": 1250.0,
                "meals": {
                    "breakfast": [
                        {
                            "food_name": "Oatmeal with banana",
                            "calories": 300.0,
                            "serving_size": "1 bowl"
                        }
                    ],
                    "lunch": [
                        {
                            "food_name": "Chicken Caesar Salad",
                            "calories": 450.0,
                            "serving_size": "1 plate"
                        }
                    ],
                    "dinner": [],
                    "snacks": [],
                    "drinks": []
                }
            }
        ]
    ```
    - 200 Ok Code
