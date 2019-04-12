import asyncio
import websockets
import numpy as np
import json

x_aim = [1, 40, 49.567, 57.677, 63.096, 65, 63.096, 57.677, 49.5, 40, 25, 17, 0]
y_aim = [0, 0, -1.903, -7.322, -15.432, -25, -34.567, -42, -48.09, -50, -50, - 50, -50]

L = 2.4  # База ТС
B = 1.2  # Колея ТС


def traek(tetta, x, y, x_aim, y_aim, dot_count):
    # tetta - угол между продольной осью и осью Х
    # x - координата Х центра масс автомобиля
    # y - координата У центра масс автомобиля
    # x_aim - координата Х целевой точки
    # y_aim - координата У целевой точки

    tetta_k1 = 0
    tetta_k2 = 0
    tetta = -tetta

    e = [x - x_aim[dot_count], y - y_aim[dot_count]]

    M = ([[np.cos(tetta), -np.sin(tetta)], [np.sin(tetta), np.cos(tetta)]])
    r = np.sqrt((e[0]**2) + (e[1]**2))

    if r <= 0.5:
        dot_count += 1

    e = ([i/r for i in e])
    e = np.dot(M, e)
    gamma = [np.arccos(e[0]), np.arcsin(e[1])]
    tetta_r = gamma[0] * np.sign(gamma[1])

    if tetta_r == 0:
        tetta_k1 = 0
        tetta_k2 = 0
    if tetta_r <= 0:
        Rm = L / (2 * np.tan(abs(tetta_r)))
        tetta_k1 = -np.arctan(L / (Rm - B / 2))
        tetta_k2 = -np.arctan(L / (Rm + B / 2))
    else:
        Rm = L / (2 * np.tan(tetta_r))
        tetta_k1 = np.arctan(L / (Rm + B / 2))
        tetta_k2 = np.arctan(L / (Rm - B / 2))

    return tetta_k1, tetta_k2, tetta_r, dot_count


async def steering_command(ws, tetta):
    if tetta < 0:
        await ws.send("{\"action\":\"turn_left_up\", \"params\":{}}")
        await ws.send("{\"action\":\"turn_right_down\", \"params\":{\"steering_angle\":" + str(max(tetta, -45.0)) + "}}")
    elif tetta > 0:
        await ws.send("{\"action\":\"turn_right_up\", \"params\":{}}")
        await ws.send("{\"action\":\"turn_left_down\", \"params\":{\"steering_angle\":" + str(min(tetta, 45.0)) + "}}")


async def on_message():
    async with websockets.connect("ws://192.168.12.49:6789") as websocket:
        await websocket.send('{\"action\":\"racing_down\", \"params\":{\"throttle_proc\":4}}')
        count = 0
        while True:
            greeting = await websocket.recv()
            json_message = json.loads(greeting)

            releative_location = json_message['releative_location']
            y = float(releative_location['x'])/2.0
            x = float(releative_location['z'])/2.0
            yaw = float(json_message['yaw']) * 3.14159/180.0
            tetta_k1, tetta_k2, tetta_r, count = traek(yaw, x, y, x_aim, y_aim, count)
            tetta = (tetta_k1 + tetta_k2)/2.0
            await steering_command(websocket, np.degrees(tetta))
            print(np.degrees(tetta_k1), np.degrees(tetta_k2), np.degrees(tetta), np.degrees(tetta_r))


asyncio.get_event_loop().run_until_complete(on_message())
asyncio.get_event_loop().run_forever()

