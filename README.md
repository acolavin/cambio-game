cambio-backend is Flask-SocketIO back-end service, which takes care of game logic. 

cambio-frontend is a React.js front-end rendering and user interface. 

Development Instructions.


## Cambio Backend
1) Install miniconda (or whatever python package manager)
2) `conda env create -f environment.yaml` (or install the dependencies in that file)
3) Enter into the environment with `conda activate cambio`
3) Run the server with `python -m cambio-backend.app` 

## Cambio-Frontend
1) Install node (e.g. `brew install node`)
2) Install required packageds: `npm install package-lock.json`
3) `npm run start`
