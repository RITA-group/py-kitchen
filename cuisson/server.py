from aiohttp import web
routes = web.RouteTableDef()


@routes.get('/')
async def home(request):
    return web.Response(text="py-kitchen is running.")


def start_server():
    app = web.Application()
    app.add_routes(routes)

    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == '__main__':
    start_server()
