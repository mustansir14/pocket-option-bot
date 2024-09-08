# This is a sample Python script.
import asyncio
import logging
import operator
import random
import threading
# import pocketoptionapi.country_id as Country
# import threading
import time
from collections import defaultdict, deque

# from pocketoptionapi.expiration import get_expiration_time, get_remaning_time
import pandas as pd
from tzlocal import get_localzone

import pocketoptionapi.constants as OP_code
import pocketoptionapi.global_value as global_value
from pocketoptionapi.api import PocketOptionAPI

# Obtener la zona horaria local del sistema como una cadena en el formato IANA
local_zone_name = get_localzone()


def nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n - 1, type))


def get_balance():
    # balances_raw = self.get_balances()
    return global_value.balance


class PocketOption:
    __version__ = "1.0.0"

    def __init__(self, ssid):
        self.size = [
            1,
            5,
            10,
            15,
            30,
            60,
            120,
            300,
            600,
            900,
            1800,
            3600,
            7200,
            14400,
            28800,
            43200,
            86400,
            604800,
            2592000,
        ]
        global_value.SSID = ssid
        self.suspend = 0.5
        self.thread = None
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        # for digit
        self.get_digital_spot_profit_after_sale_data = nested_dict(2, int)
        self.get_realtime_strike_list_temp_data = {}
        self.get_realtime_strike_list_temp_expiration = 0
        self.SESSION_HEADER = {
            "User-Agent": r"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            r"Chrome/66.0.3359.139 Safari/537.36"
        }
        self.SESSION_COOKIE = {}
        self.api = PocketOptionAPI()
        self.loop = asyncio.get_event_loop()
        self.is_demo = False
        if '"isDemo":1' in ssid:
            self.is_demo = True

        #

        # --start
        # self.connect()
        # this auto function delay too long

    # --------------------------------------------------------------------------

    def get_server_timestamp(self):
        return self.api.time_sync.server_timestamp

    def get_server_datetime(self):
        return self.api.time_sync.server_datetime

    def set_session(self, header, cookie):
        self.SESSION_HEADER = header
        self.SESSION_COOKIE = cookie

    def get_async_order(self, buy_order_id):
        # name': 'position-changed', 'microserviceName': "portfolio"/"digital-options"
        if self.api.order_async["deals"][0]["id"] == buy_order_id:
            return self.api.order_async["deals"][0]
        else:
            return None

    def get_async_order_id(self, buy_order_id):
        return self.api.order_async["deals"][0][buy_order_id]

    def start_async(self):
        asyncio.run(self.api.connect())

    def connect(self):
        """
        Método síncrono para establecer la conexión.
        Utiliza internamente el bucle de eventos de asyncio para ejecutar la coroutine de conexión.
        """
        try:
            # Iniciar el hilo que manejará la conexión WebSocket
            websocket_thread = threading.Thread(
                target=self.api.connect, daemon=True, args=(self.is_demo,)
            )
            websocket_thread.start()

        except Exception as e:
            print(f"Error al conectar: {e}")
            return False
        return True

    @staticmethod
    def check_connect():
        # True/False
        if global_value.websocket_is_connected == 0:
            return False
        elif global_value.websocket_is_connected is None:
            return False
        else:
            return True

        # wait for timestamp getting

    # self.update_ACTIVES_OPCODE()
    @staticmethod
    def get_balance():
        if global_value.balance_updated:
            return global_value.balance
        else:
            return None

    async def buy(self, amount, active, action, expirations):
        self.api.buy_multi_option = {}
        self.api.buy_successful = None
        req_id = "buy"

        try:
            if req_id not in self.api.buy_multi_option:
                self.api.buy_multi_option[req_id] = {"id": None}
            else:
                self.api.buy_multi_option[req_id]["id"] = None
        except Exception as e:
            logging.error(f"Error initializing buy_multi_option: {e}")
            return False, None

        global_value.order_data = None
        global_value.result = None
        global_value.request_id = random.randint(10000000, 30000000)

        await self.api.buyv3(
            amount, active, action, expirations, global_value.request_id, self.is_demo
        )

        start_t = time.time()
        while True:
            if global_value.result is not None and global_value.order_data is not None:
                break
            if time.time() - start_t >= 5:
                if (
                    isinstance(global_value.order_data, dict)
                    and "error" in global_value.order_data
                ):
                    logging.error(global_value.order_data["error"])
                else:
                    logging.error(
                        "Unknown error occurred during buy operation "
                        + str(global_value.websocket_error_reason)
                    )
                return False, None
            await asyncio.sleep(0.1)  # Sleep for a short period to prevent busy-waiting

        return global_value.result, global_value.order_data.get("id", None)

    def check_win(self, id_number):
        """Return amount of deals and win/lose status."""

        start_t = time.time()
        order_info = None

        while True:
            try:
                order_info = self.get_async_order(id_number)
                if order_info and "id" in order_info and order_info["id"] is not None:
                    break
            except:
                pass
            # except Exception as e:
            #    logging.error(f"Error retrieving order info: {e}")

            if time.time() - start_t >= 120:
                logging.error("Timeout: Could not retrieve order info in time.")
                return None, "unknown"

            time.sleep(0.1)  # Sleep for a short period to prevent busy-waiting

        if order_info and "profit" in order_info:
            status = "win" if order_info["profit"] > 0 else "lose"
            return order_info["profit"], status
        else:
            logging.error("Invalid order info retrieved.")
            return None, "unknown"

    @staticmethod
    def last_time(timestamp, period):
        # Divide por 60 para convertir a minutos, usa int() para truncar al entero más cercano (redondear hacia abajo),
        # y luego multiplica por 60 para volver a convertir a segundos.
        timestamp_redondeado = (timestamp // period) * period
        return int(timestamp_redondeado)

    async def get_candles(
        self, active, period, start_time=None, count=6000, count_request=1
    ):
        """
        Realiza múltiples peticiones para obtener datos históricos de velas y los procesa.
        Devuelve un Dataframe ordenado de menor a mayor por la columna 'time'.

        :param active: El activo para el cual obtener las velas.
        :param period: El intervalo de tiempo de cada vela en segundos.
        :param count: El número de segundos a obtener en cada petición, max: 9000 = 150 datos de 1 min.
        :param start_time: El tiempo final para la última vela.
        :param count_request: El número de peticiones para obtener más datos históricos.
        """
        if start_time is None:
            time_sync = self.get_server_timestamp()
            time_red = self.last_time(time_sync, period)
        else:
            time_red = start_time
            time_sync = self.get_server_timestamp()

        all_candles = []

        for _ in range(count_request):
            self.api.history_data = None
            while True:
                # try:
                # Enviar la petición de velas
                await self.api.getcandles(active, 30, count, time_red)

                # Esperar hasta que history_data no sea None
                sleep_count = 0
                while self.check_connect and self.api.history_data is None:
                    await asyncio.sleep(0.1)
                    sleep_count += 1
                    if sleep_count >= 100:
                        logging.error("Error fetching candle data")
                        return None

                if self.api.history_data is not None:
                    all_candles.extend(self.api.history_data)
                    break

                # except Exception as e:
                #     logging.error(e)
                # Puedes agregar lógica de reconexión aquí si es necesario

            # Ordenar all_candles por 'index' para asegurar que estén en el orden correcto
            all_candles = sorted(all_candles, key=lambda x: x["time"])

            # Asegurarse de que se han recibido velas antes de actualizar time_red
            if all_candles:
                # Usar el tiempo de la última vela recibida para la próxima petición
                time_red = all_candles[0]["time"]

        # Crear un DataFrame con todas las velas obtenidas
        df_candles = pd.DataFrame(all_candles)

        # Ordenar por la columna 'time' de menor a mayor
        df_candles = df_candles.sort_values(by="time").reset_index(drop=True)
        df_candles["time"] = pd.to_datetime(df_candles["time"], unit="s")
        df_candles.set_index("time", inplace=True)
        df_candles.index = df_candles.index.floor("1s")

        # Resamplear los datos en intervalos de 30 segundos y calcular open, high, low, close
        df_resampled = df_candles["price"].resample(f"{period}s").ohlc()

        # Resetear el índice para que 'time' vuelva a ser una columna
        df_resampled.reset_index(inplace=True)

        return df_resampled

    @staticmethod
    def process_data_history(data, period):
        """
        Este método toma datos históricos, los convierte en un DataFrame de pandas, redondea los tiempos al minuto más cercano,
        y calcula los valores OHLC (Open, High, Low, Close) para cada minuto. Luego, convierte el resultado en un diccionario
        y lo devuelve.

        :param dict data: Datos históricos que incluyen marcas de tiempo y precios.
        :param int period: Periodo en minutos
        :return: Un diccionario que contiene los valores OHLC agrupados por minutos redondeados.
        """
        # Crear DataFrame
        df = pd.DataFrame(data["history"], columns=["timestamp", "price"])
        # Convertir a datetime y redondear al minuto
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        # df['datetime'] = df['datetime'].dt.tz_convert(str(local_zone_name))
        df["minute_rounded"] = df["datetime"].dt.floor(f"{period / 60}min")

        # Calcular OHLC
        ohlcv = (
            df.groupby("minute_rounded")
            .agg(
                open=("price", "first"),
                high=("price", "max"),
                low=("price", "min"),
                close=("price", "last"),
            )
            .reset_index()
        )

        ohlcv["time"] = ohlcv["minute_rounded"].apply(lambda x: int(x.timestamp()))
        ohlcv = ohlcv.drop(columns="minute_rounded")

        ohlcv = ohlcv.iloc[:-1]

        ohlcv_dict = ohlcv.to_dict(orient="records")

        return ohlcv_dict

    @staticmethod
    def process_candle(candle_data, period):
        """
        Resumen: Este método estático de Python, denominado `process_candle`, toma datos de velas financieras y un período de tiempo específico como entrada.
        Realiza varias operaciones de limpieza y organización de datos utilizando pandas, incluyendo la ordenación por tiempo, eliminación de duplicados,
        y reindexación. Además, verifica si las diferencias de tiempo entre las entradas consecutivas son iguales al período especificado y retorna tanto el DataFrame procesado
        como un booleano indicando si todas las diferencias son iguales al período dado. Este método es útil para preparar y verificar la consistencia de los datos de velas financieras
        para análisis posteriores.

        Procesa los datos de las velas recibidos como entrada.
        Convierte los datos de entrada en un DataFrame de pandas, los ordena por tiempo de forma ascendente,
        elimina duplicados basados en la columna 'time', y reinicia el índice del DataFrame.
        Adicionalmente, verifica si las diferencias de tiempo entre las filas consecutivas son iguales al período especificado,
        asumiendo que el período está dado en segundos, e imprime si todas las diferencias son de 60 segundos.
        :param list candle_data: Datos de las velas a procesar.
        :param int period: El período de tiempo entre las velas, usado para la verificación de diferencias de tiempo.
        :return: DataFrame procesado con los datos de las velas.
        """
        # Convierte los datos en un DataFrame y los añade al DataFrame final
        data_df = pd.DataFrame(candle_data)
        # datos_completos = pd.concat([datos_completos, data_df], ignore_index=True)
        # Procesa los datos obtenidos
        data_df.sort_values(by="time", ascending=True, inplace=True)
        data_df.drop_duplicates(subset="time", keep="first", inplace=True)
        data_df.reset_index(drop=True, inplace=True)
        data_df.ffill(inplace=True)
        data_df.drop(columns="symbol_id", inplace=True)
        # Verificación opcional: Comprueba si las diferencias son todas de 60 segundos (excepto el primer valor NaN)
        diferencias = data_df["time"].diff()
        diff = (diferencias[1:] == period).all()
        return data_df, diff

    def change_symbol(self, active, period):
        return self.api.change_symbol(active, period)

    def sync_datetime(self):
        return self.api.synced_datetime
