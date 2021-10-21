from uvicorn import Config, Server
import factory


if __name__ == '__main__':
    server = Server(
        Config(
            factory.prod_app(),
            host="0.0.0.0",
            port=8080,
            log_level='debug',
            reload=True,
        ),
    )
    server.run()
