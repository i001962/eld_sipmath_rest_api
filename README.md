# Risk Management Volatility Service
Solace Risk Management Volatility Service.

### To Run App (Linux and Mac)
You can build and run app using [**make**](https://www.gnu.org/software/make/) software. You need to install on your local 
```shell
make up_build
```
Or you can build and run with docker-compose.
```shell
docker-compose up --build -d
```

### To Stop App (Linux and Mac)
With **make**
```shell
make down
```

Or with **docker-compose**
```shell
docker-compose down
```

### Local Test
````shell
 http://localhost:8089/volatility/?protocols=solace,bluebit&window=365&terms=3
````

### App Deployment
The CI/CD pipeline is triggered when the code is merged into the **main** branch.
