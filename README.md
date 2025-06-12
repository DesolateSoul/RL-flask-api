Lunar Lander Flask app

This is a flask app and API for creating videos of LunarLanderV3 environment of gymnasium library


## Deployment

To deploy this project

download RL_App and RL_Restful_API folders into two different projects

in each project run
```bash
  pip install -r requirements.txt
```

in RL_Restful_API run
```bash
  pip install swig gymnasium[box2d]
```
if there are any errors install "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

configure hosts and ports in rest_api.py and app.py
run rest_api.py and app.py
