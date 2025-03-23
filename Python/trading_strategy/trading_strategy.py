import ccxt
import requests
import pandas as pd
import talib
import json
import time

# Загрузка настроек из settings.json
try:
    with open('settings.json') as f:
        settings = json.load(f)
except FileNotFoundError:
    print("Файл settings.json не найден, используются параметры по умолчанию")
    settings = {
        "symbol": "BTCUSDT",                    # Символ торговой пары (например, BTCUSDT для Bitcoin к USDT) ETHUSDT XRPUSDT BNBUSDT
        "timeframe": "4h",                      # Таймфрейм для анализа (например, 4h - 4 часа)
        "fgi_threshold_low": 25,                # Нижний порог FGI (Fear and Greed Index) для определения страха (0-25)
        "fgi_threshold_high": 75,               # Верхний порог FGI для определения жадности (75-100)
        "rsi_threshold_low": 30,                # Нижний порог RSI для определения перепроданности (0-30)
        "rsi_threshold_high": 70,               # Верхний порог RSI для определения перекупленности (70-100)
        "rsi_period": 14,                       # Период для расчета RSI (Relative Strength Index), стандартное значение 14
        "ema_short_period": 12,                 # Период короткой EMA (Exponential Moving Average), используется для определения тренда
        "ema_long_period": 26,                  # Период длинной EMA, используется для сравнения с короткой EMA
        "macd_fast": 12,                        # Период быстрой линии MACD (Moving Average Convergence Divergence)
        "macd_slow": 26,                        # Период медленной линии MACD
        "macd_signal": 9,                       # Период сигнальной линии MACD
        "bollinger_period": 20,                 # Период для расчета Bollinger Bands (обычно 20)
        "bollinger_deviation": 2,               # Стандартное отклонение для Bollinger Bands (обычно 2)
        "support_resistance_window": 10,        # Окно для определения уровней поддержки и сопротивления (количество свечей)
        "show_explanations": False,             # Флаг, показывающий, нужно ли выводить пояснения (True/False)
        "historical_data_limit": 100,           # Количество свечей для анализа исторических данных
        "success_threshold": 0.02,              # Порог успеха в процентах (например, 2% роста/падения для определения успешности сигнала)
        "success_horizon": 5,                   # Горизонт для оценки успеха сигнала (количество свечей вперед)
        "adx_period": 14                        # Период для расчета ADX (Average Directional Index) для оценки силы тренда
    }

SYMBOL = settings.get("symbol", "BTCUSDT")
TIMEFRAME = settings.get("timeframe", "4h")
FGI_THRESHOLD_LOW = settings.get("fgi_threshold_low", 25)
FGI_THRESHOLD_HIGH = settings.get("fgi_threshold_high", 75)
RSI_THRESHOLD_LOW = settings.get("rsi_threshold_low", 30)
RSI_THRESHOLD_HIGH = settings.get("rsi_threshold_high", 70)
RSI_PERIOD = settings.get("rsi_period", 14)
EMA_SHORT_PERIOD = settings.get("ema_short_period", 12)
EMA_LONG_PERIOD = settings.get("ema_long_period", 26)
MACD_FAST = settings.get("macd_fast", 12)
MACD_SLOW = settings.get("macd_slow", 26)
MACD_SIGNAL = settings.get("macd_signal", 9)
BOLLINGER_PERIOD = settings.get("bollinger_period", 20)
BOLLINGER_DEVIATION = settings.get("bollinger_deviation", 2)
SUPPORT_RESISTANCE_WINDOW = settings.get("support_resistance_window", 10)
SHOW_EXPLANATIONS = settings.get("show_explanations", False)
HISTORICAL_DATA_LIMIT = settings.get("historical_data_limit", 100)
SUCCESS_THRESHOLD = settings.get("success_threshold", 0.02)
SUCCESS_HORIZON = settings.get("success_horizon", 5)
ADX_PERIOD = settings.get("adx_period", 14)

exchange = ccxt.bybit({'enableRateLimit': True})

def get_fgi():
    """Получение текущего значения FGI"""
    try:
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return int(data['data'][0]['value'])
    except Exception as e:
        print(f"Ошибка при получении текущего FGI: {e}")
        return None

def get_historical_fgi(limit=100):
    """Получение исторических значений FGI.
       Возвращает список значений, где индекс 0 – самое старое, а последний – текущее.
    """
    try:
        url = f"https://api.alternative.me/fng/?limit={limit}&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # API возвращает данные в обратном порядке (свежие данные первыми), переворачиваем список
        fgi_list = [int(item['value']) for item in data['data']]
        fgi_list.reverse()
        return fgi_list
    except Exception as e:
        print(f"Ошибка при получении исторических значений FGI: {e}")
        current = get_fgi()
        return [current] * limit if current is not None else [50] * limit

def fetch_ohlcv(symbol, timeframe, limit=HISTORICAL_DATA_LIMIT):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Ошибка при загрузке данных для {symbol}: {e}")
        return None

def calculate_rsi(df, period):
    if df is None or len(df) < period + 1:
        print(f"Недостаточно данных для расчета RSI с period={period}: {len(df) if df is not None else 'None'} свечей")
        return None
    return talib.RSI(df["close"], timeperiod=period)

def calculate_ema(df, short_period, long_period):
    if df is None or len(df) < max(short_period, long_period):
        print("Недостаточно данных для расчета EMA")
        return None, None
    ema_short = talib.EMA(df["close"].dropna(), timeperiod=short_period)
    ema_long = talib.EMA(df["close"].dropna(), timeperiod=long_period)
    return ema_short, ema_long

def calculate_macd(df, fast_period, slow_period, signal_period):
    if df is None or len(df) < slow_period:
        print("Недостаточно данных для расчета MACD")
        return None, None
    macd, macd_signal, _ = talib.MACD(df["close"].dropna(), fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    return macd, macd_signal

def calculate_bollinger_bands(df, period, deviation):
    if df is None or len(df) < period:
        print(f"Недостаточно данных для расчета Bollinger Bands с period={period}: {len(df) if df is not None else 'None'} свечей")
        return None, None, None
    upper, middle, lower = talib.BBANDS(df["close"].dropna(), timeperiod=period, nbdevup=deviation, nbdevdn=deviation, matype=0)
    return upper, middle, lower

def calculate_support_resistance(df, window):
    if df is None or len(df) < window * 2:
        print(f"Недостаточно данных для расчета уровней поддержки/сопротивления с window={window}: {len(df) if df is not None else 'None'} свечей")
        return None, None
    recent_data = df["close"].iloc[-window*2:]
    support = float(recent_data.min())
    resistance = float(recent_data.max())
    return support, resistance

def calculate_adx(df, period):
    if df is None or len(df) < period + 1:
        print(f"Недостаточно данных для расчета ADX с period={period}: {len(df) if df is not None else 'None'} свечей")
        return None
    adx = talib.ADX(df["high"], df["low"], df["close"], timeperiod=period)
    return adx

def get_price_volume(symbol, timeframe):
    df = fetch_ohlcv(symbol, timeframe, limit=2)
    if df is not None and len(df) >= 2:
        return df['close'].iloc[-1], df['volume'].iloc[-1]
    return None, None

def analyze_historical_signals(df, fgi_values):
    if df is None or len(df) < HISTORICAL_DATA_LIMIT:
        print("Недостаточно данных для исторического анализа")
        return {}
    
    rsi = calculate_rsi(df, RSI_PERIOD)
    ema_short, ema_long = calculate_ema(df, EMA_SHORT_PERIOD, EMA_LONG_PERIOD)
    macd, macd_signal = calculate_macd(df, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df, BOLLINGER_PERIOD, BOLLINGER_DEVIATION)
    adx = calculate_adx(df, ADX_PERIOD)
    
    if rsi is None or ema_short is None or macd is None or bb_upper is None or adx is None:
        print("Ошибка в расчетах индикаторов для исторического анализа")
        return {}

    historical_signals = []
    for i in range(len(df) - SUCCESS_HORIZON):
        if pd.isna(rsi.iloc[i]) or pd.isna(ema_short.iloc[i]) or pd.isna(macd.iloc[i]) or pd.isna(bb_upper.iloc[i]) or pd.isna(adx.iloc[i]):
            continue

        # Используем историческое значение FGI, если доступно, иначе последнее значение
        fgi = fgi_values[i] if i < len(fgi_values) else fgi_values[-1]
        current_rsi = rsi.iloc[i]
        current_price = df['close'].iloc[i]
        current_volume = df['volume'].iloc[i]
        prev_volume = df['volume'].iloc[i-1] if i > 0 else 0
        current_ema_short = ema_short.iloc[i]
        current_ema_long = ema_long.iloc[i]
        current_macd = macd.iloc[i]
        current_macd_signal = macd_signal.iloc[i]
        current_bb_upper = bb_upper.iloc[i]
        current_bb_lower = bb_lower.iloc[i]
        current_adx = adx.iloc[i]

        if fgi <= FGI_THRESHOLD_LOW and current_rsi <= RSI_THRESHOLD_LOW:
            scenario = "long"
        elif fgi >= FGI_THRESHOLD_HIGH and current_rsi >= RSI_THRESHOLD_HIGH:
            scenario = "short"
        elif fgi >= FGI_THRESHOLD_HIGH and current_rsi <= RSI_THRESHOLD_LOW:
            scenario = "divergence_long"
        elif fgi <= FGI_THRESHOLD_LOW and current_rsi >= RSI_THRESHOLD_HIGH:
            scenario = "divergence_short"
        else:
            scenario = "neutral"

        trend = "bullish" if current_ema_short > current_ema_long else "bearish"
        trend_strength = "strong" if current_adx > 25 else "weak"

        future_price = df['close'].iloc[i + SUCCESS_HORIZON]
        price_change = (future_price - current_price) / current_price
        if scenario in ["long", "divergence_long"]:
            success = price_change >= SUCCESS_THRESHOLD
        elif scenario in ["short", "divergence_short"]:
            success = price_change <= -SUCCESS_THRESHOLD
        else:
            continue

        signal = {
            "scenario": scenario,
            "trend": trend,
            "trend_strength": trend_strength,
            "success": success
        }
        historical_signals.append(signal)

    success_rates = {}
    for signal in historical_signals:
        key = (signal["scenario"], signal["trend"], signal["trend_strength"])
        if key not in success_rates:
            success_rates[key] = {"total": 0, "success": 0}
        success_rates[key]["total"] += 1
        if signal["success"]:
            success_rates[key]["success"] += 1

    return success_rates

def calculate_probability(scenario, trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed):
    key = (scenario, trend, trend_strength)
    base_probability = 50
    if key in success_rates and success_rates[key]["total"] > 0:
        base_probability = (success_rates[key]["success"] / success_rates[key]["total"]) * 100

    confirmed_count = sum([1 for c in [volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed] if c])
    total_indicators = 5
    confirmation_bonus = (confirmed_count / total_indicators) * 30
    probability = base_probability + confirmation_bonus
    return probability

def print_explanations(ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed, scenario):
    print("\n📝 <b>Пояснения</b>")
    if scenario in ["long", "short"]:
        scenario_text = "Согласованный сигнал (Long)" if scenario == "long" else "Согласованный сигнал (Short)"
        print(f"📋 <b>Сценарий:</b> {scenario_text}")
        print("➡️ FGI и RSI указывают в одном направлении.")
    elif scenario in ["divergence_long", "divergence_short"]:
        scenario_text = "Перекос сигналов (Long)" if scenario == "divergence_long" else "Перекос сигналов (Short)"
        print(f"📋 <b>Сценарий:</b> {scenario_text}")
        print("⚠️ FGI и RSI противоречат друг другу.")
    else:
        print("📋 <b>Сценарий:</b> Нейтральная зона")
        print("ℹ️ Значения индикаторов не дают чёткого сигнала.")
    
    print("🔍 <b>Дополнительные индикаторы:</b>")
    print("• <b>Объем:</b> Подтвержден, если текущий объем выше предыдущего на 20%.")
    print(f"• <b>EMA:</b> Короткая EMA выше длинной для бычьего тренда и наоборот. — {'✅ Подтверждено' if ema_confirmed else '❌ Не подтверждено'}.")
    print("• <b>MACD:</b> Бычий сигнал, если MACD выше сигнальной линии, и наоборот. — " + ("✅ Подтверждено" if macd_confirmed else "❌ Не подтверждено"))
    print("• <b>Bollinger Bands:</b> Цена у нижней полосы или ниже (для long) и у верхней полосы или выше (для short). — " + ("✅ Подтверждено" if bollinger_confirmed else "❌ Не подтверждено"))
    print("• <b>Поддержка/Сопротивление:</b> Цена близка к ключевым уровням (разница менее 2%). — " + ("✅ Подтверждено" if sr_confirmed else "❌ Не подтверждено"))


def trading_strategy(symbol, timeframe):
    # Загружаем исторические данные
    historical_df = fetch_ohlcv(symbol, timeframe, limit=HISTORICAL_DATA_LIMIT)
    if historical_df is None or historical_df.empty:
        print("❌ <b>Ошибка:</b> Не удалось загрузить исторические данные.")
        return

    # Получаем исторические значения FGI
    historical_fgi = get_historical_fgi(limit=len(historical_df))
    if historical_fgi is None or len(historical_fgi) != len(historical_df):
        print("⚠️ <b>Предупреждение:</b> Количество исторических значений FGI не совпадает с количеством свечей. Будет использовано последнее доступное значение.")
        historical_fgi = [historical_fgi[-1]] * len(historical_df) if historical_fgi else [50] * len(historical_df)

    current_fgi = get_fgi()
    if current_fgi is None:
        print("❌ <b>Ошибка:</b> Не удалось получить текущее значение FGI.")
        return

    # Дополнительные данные для расчета индикаторов
    required_limit = max(EMA_LONG_PERIOD + MACD_SIGNAL, BOLLINGER_PERIOD, SUPPORT_RESISTANCE_WINDOW * 2) + 1
    df = fetch_ohlcv(symbol, timeframe, limit=required_limit)
    if df is None or df.empty:
        print("❌ <b>Ошибка:</b> Не удалось загрузить данные для расчета индикаторов.")
        return

    rsi_series = calculate_rsi(df, RSI_PERIOD)
    if rsi_series is None:
        print("❌ <b>Ошибка:</b> Ошибка при расчете RSI.")
        return
    rsi = rsi_series.iloc[-1]

    price, volume = get_price_volume(symbol, timeframe)
    if price is None or volume is None:
        print("❌ <b>Ошибка:</b> Недоступны данные о цене или объеме.")
        return

    ema_short_series, ema_long_series = calculate_ema(df, EMA_SHORT_PERIOD, EMA_LONG_PERIOD)
    if ema_short_series is None or ema_long_series is None:
        print("❌ <b>Ошибка:</b> Ошибка при расчете EMA.")
        return
    ema_short = float(ema_short_series.iloc[-1])
    ema_long = float(ema_long_series.iloc[-1])

    macd_series, macd_signal_series = calculate_macd(df, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    if macd_series is None or macd_signal_series is None:
        print("❌ <b>Ошибка:</b> Ошибка при расчете MACD.")
        return
    macd = float(macd_series.iloc[-1])
    macd_signal = float(macd_signal_series.iloc[-1])

    bb_upper_series, bb_middle_series, bb_lower_series = calculate_bollinger_bands(df, BOLLINGER_PERIOD, BOLLINGER_DEVIATION)
    if bb_upper_series is None or bb_middle_series is None or bb_lower_series is None:
        print("❌ <b>Ошибка:</b> Ошибка при расчете Bollinger Bands.")
        return
    bb_upper = float(bb_upper_series.iloc[-1])
    bb_middle = float(bb_middle_series.iloc[-1])
    bb_lower = float(bb_lower_series.iloc[-1])

    support, resistance = calculate_support_resistance(df, SUPPORT_RESISTANCE_WINDOW)
    if support is None or resistance is None:
        print("❌ <b>Ошибка:</b> Ошибка при расчете уровней поддержки/сопротивления.")
        return

    adx_series = calculate_adx(df, ADX_PERIOD)
    if adx_series is None:
        print("❌ <b>Ошибка:</b> Ошибка при расчете ADX.")
        return
    adx = adx_series.iloc[-1]

    prev_volume = df['volume'].iloc[-2] if len(df) >= 2 else 0

    success_rates = analyze_historical_signals(historical_df, historical_fgi)

    scenario = None
    recommendation = None
    volume_confirmed = False
    ema_confirmed = False
    macd_confirmed = False
    bollinger_confirmed = False
    sr_confirmed = False
    trend = "bullish" if ema_short > ema_long else "bearish"
    trend_strength = "strong" if adx > 25 else "weak"

    # Логика формирования сигналов с проверкой подтверждений
    if current_fgi <= FGI_THRESHOLD_LOW and rsi <= RSI_THRESHOLD_LOW:
        scenario = "long"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short > ema_long
        macd_confirmed = macd > macd_signal
        bollinger_confirmed = price <= bb_lower
        sr_confirmed = abs(price - support) / price < 0.02
        confirmation_status = (f"Объем: {'✅' if volume_confirmed else '❌'}, "
                               f"EMA: {'✅' if ema_confirmed else '❌'}, "
                               f"MACD: {'✅' if macd_confirmed else '❌'}, "
                               f"Bollinger Bands: {'✅' if bollinger_confirmed else '❌'}, "
                               f"Поддержка/Сопротивление: {'✅' if sr_confirmed else '❌'}")
        confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
        if confirmed_count >= 3:
            recommendation = f"FGI = {current_fgi} (рынок в страхе), RSI = {rsi:.2f} (перепроданность). <b>Рекомендую покупку</b> ({confirmation_status})"
        else:
            recommendation = f"FGI = {current_fgi} (рынок в страхе), RSI = {rsi:.2f} (перепроданность). Сигнал на покупку <b>слабый</b>, ждем подтверждения ({confirmation_status})"

    elif current_fgi >= FGI_THRESHOLD_HIGH and rsi >= RSI_THRESHOLD_HIGH:
        scenario = "short"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short < ema_long
        macd_confirmed = macd < macd_signal
        bollinger_confirmed = price >= bb_upper
        sr_confirmed = abs(price - resistance) / price < 0.02
        confirmation_status = (f"Объем: {'✅' if volume_confirmed else '❌'}, "
                               f"EMA: {'✅' if ema_confirmed else '❌'}, "
                               f"MACD: {'✅' if macd_confirmed else '❌'}, "
                               f"Bollinger Bands: {'✅' if bollinger_confirmed else '❌'}, "
                               f"Поддержка/Сопротивление: {'✅' if sr_confirmed else '❌'}")
        confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
        if confirmed_count >= 3:
            recommendation = f"FGI = {current_fgi} (рынок в жадности), RSI = {rsi:.2f} (перекупленность). <b>Рекомендую продажу</b> ({confirmation_status})"
        else:
            recommendation = f"FGI = {current_fgi} (рынок в жадности), RSI = {rsi:.2f} (перекупленность). Сигнал на продажу <b>слабый</b>, ждем подтверждения ({confirmation_status})"

    elif current_fgi >= FGI_THRESHOLD_HIGH and rsi <= RSI_THRESHOLD_LOW:
        scenario = "divergence_long"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short > ema_long
        macd_confirmed = macd > macd_signal
        bollinger_confirmed = price <= bb_lower
        sr_confirmed = abs(price - support) / price < 0.02
        confirmation_status = (f"Объем: {'✅' if volume_confirmed else '❌'}, "
                               f"EMA: {'✅' if ema_confirmed else '❌'}, "
                               f"MACD: {'✅' if macd_confirmed else '❌'}, "
                               f"Bollinger Bands: {'✅' if bollinger_confirmed else '❌'}, "
                               f"Поддержка/Сопротивление: {'✅' if sr_confirmed else '❌'}")
        confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
        if confirmed_count >= 3:
            recommendation = f"Перекос: FGI = {current_fgi} (жадность), RSI = {rsi:.2f} (перепроданность). <b>Рекомендую покупку</b> ({confirmation_status})"
        else:
            recommendation = f"Перекос: FGI = {current_fgi} (жадность), RSI = {rsi:.2f} (перепроданность). Сигнал на покупку <b>слабый</b>, ждем подтверждения ({confirmation_status})"

    elif current_fgi <= FGI_THRESHOLD_LOW and rsi >= RSI_THRESHOLD_HIGH:
        scenario = "divergence_short"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short < ema_long
        macd_confirmed = macd < macd_signal
        bollinger_confirmed = price >= bb_upper
        sr_confirmed = abs(price - resistance) / price < 0.02
        confirmation_status = (f"Объем: {'✅' if volume_confirmed else '❌'}, "
                               f"EMA: {'✅' if ema_confirmed else '❌'}, "
                               f"MACD: {'✅' if macd_confirmed else '❌'}, "
                               f"Bollinger Bands: {'✅' if bollinger_confirmed else '❌'}, "
                               f"Поддержка/Сопротивление: {'✅' if sr_confirmed else '❌'}")
        confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
        if confirmed_count >= 3:
            recommendation = f"Перекос: FGI = {current_fgi} (страх), RSI = {rsi:.2f} (перекупленность). <b>Рекомендую продажу</b> ({confirmation_status})"
        else:
            recommendation = f"Перекос: FGI = {current_fgi} (страх), RSI = {rsi:.2f} (перекупленность). Сигнал на продажу <b>слабый</b>, ждем подтверждения ({confirmation_status})"

    else:
        scenario = "neutral"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short > ema_long
        macd_confirmed = macd > macd_signal
        bollinger_confirmed = price <= bb_lower
        sr_confirmed = abs(price - support) / price < 0.02
        confirmed_count_long = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
        ema_confirmed_short = ema_short < ema_long
        macd_confirmed_short = macd < macd_signal
        bollinger_confirmed_short = price >= bb_upper
        sr_confirmed_short = abs(price - resistance) / price < 0.02
        confirmed_count_short = sum([volume_confirmed, ema_confirmed_short, macd_confirmed_short, bollinger_confirmed_short, sr_confirmed_short])
        if confirmed_count_long >= 3:
            confirmation_status = (f"Объем: {'✅' if volume_confirmed else '❌'}, "
                                   f"EMA: {'✅' if ema_confirmed else '❌'}, "
                                   f"MACD: {'✅' if macd_confirmed else '❌'}, "
                                   f"Bollinger Bands: {'✅' if bollinger_confirmed else '❌'}, "
                                   f"Поддержка/Сопротивление: {'✅' if sr_confirmed else '❌'}")
            recommendation = f"Нейтральная зона: FGI = {current_fgi}, RSI = {rsi:.2f}. Возможна покупка ({confirmation_status})"
        elif confirmed_count_short >= 3:
            confirmation_status = (f"Объем: {'✅' if volume_confirmed else '❌'}, "
                                   f"EMA: {'✅' if ema_confirmed_short else '❌'}, "
                                   f"MACD: {'✅' if macd_confirmed_short else '❌'}, "
                                   f"Bollinger Bands: {'✅' if bollinger_confirmed_short else '❌'}, "
                                   f"Поддержка/Сопротивление: {'✅' if sr_confirmed_short else '❌'}")
            recommendation = f"Нейтральная зона: FGI = {current_fgi}, RSI = {rsi:.2f}. Возможна продажа ({confirmation_status})"
        else:
            recommendation = f"Нейтральная зона: FGI = {current_fgi}, RSI = {rsi:.2f}. Воздержитесь или ждите пробоя с объемом."

    # Вывод с эмодзи и HTML‑форматированием:
    print("🔍 <b>Анализ рынка</b>")
    print(f"💰 <b>Актив:</b> {symbol} | <b>Таймфрейм:</b> {timeframe}")
    print(f"💵 <b>Текущая цена:</b> {price:.2f} USDT | <b>Объем:</b> {volume:.2f}")
    print(f"📊 <b>EMA:</b> Short={ema_short:.2f}, Long={ema_long:.2f} - {'🐂 Бычий тренд' if ema_short > ema_long else '🐻 Медвежий тренд'}")
    print(f"📉 <b>MACD:</b> Line={macd:.2f}, Signal={macd_signal:.2f} - {'📈 Бычий сигнал' if macd > macd_signal else '📉 Медвежий сигнал'}")
    print(f"📈 <b>Bollinger Bands:</b> Upper={bb_upper:.2f}, Middle={bb_middle:.2f}, Lower={bb_lower:.2f}")
    print(f"📌 <b>Поддержка/Сопротивление:</b> Поддержка={support:.2f}, Сопротивление={resistance:.2f}")
    print(f"🤖 <b>Рекомендация:</b> {recommendation}")
    print("")
    
    print("🔢 <b>Рекомендации от ИИ</b>")
    probability = calculate_probability(scenario, trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed)
    confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
    
    if scenario in ["long", "divergence_long"]:
        if confirmed_count >= 3:
            if probability >= 50:
                print(f"✅ <b>Сильный сигнал для покупки.</b> Шанс успеха: {probability:.0f}%. Рекомендуется действовать.")
            else:
                print(f"⚠️ <b>Сигнал для покупки есть, но шансы успеха низкие:</b> {probability:.0f}%. Лучше подождать благоприятных условий.")
        else:
            print(f"❌ <b>Сигнал для покупки слабый</b> из-за недостатка подтверждений. Шанс успеха: {probability:.0f}%.")
    elif scenario in ["short", "divergence_short"]:
        if confirmed_count >= 3:
            if probability >= 50:
                print(f"✅ <b>Сильный сигнал для продажи.</b> Шанс успеха: {probability:.0f}%. Рекомендуется действовать.")
            else:
                print(f"⚠️ <b>Сигнал для продажи есть, но шансы успеха низкие:</b> {probability:.0f}%. Лучше подождать благоприятных условий.")
        else:
            print(f"❌ <b>Сигнал для продажи слабый</b> из-за недостатка подтверждений. Шанс успеха: {probability:.0f}%.")
    else:
        probability_long = calculate_probability("long", trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed)
        probability_short = calculate_probability("short", trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed)
        if confirmed_count >= 3 and probability_long >= 50:
            print(f"ℹ️ <b>Нейтральная зона,</b> но есть слабый сигнал для покупки. Шанс успеха: {probability_long:.0f}%.")
        elif confirmed_count >= 3 and probability_short >= 50:
            print(f"ℹ️ <b>Нейтральная зона,</b> но есть слабый сигнал для продажи. Шанс успеха: {probability_short:.0f}%.")
        else:
            print(f"ℹ️ <b>Нейтральная зона.</b> Шанс успеха для покупки: {probability_long:.0f}%, для продажи: {probability_short:.0f}%. Воздержитесь или ждите пробоя с объемом.")
    
    key = (scenario, trend, trend_strength)
    base_probability = 50
    if key in success_rates and success_rates[key]["total"] > 0:
        base_probability = (success_rates[key]["success"] / success_rates[key]["total"]) * 100
    total_indicators = 5
    confirmation_bonus = (confirmed_count / total_indicators) * 30

    print("")
    print("🎯 <b>Расчет вероятности успеха</b>")
    print(f"✅ <b>Базовая вероятность:</b> {base_probability:.2f}%")
    print(f"🔔 <b>Бонус за подтверждения:</b> {confirmation_bonus:.2f}%")
    print(f"🎯 <b>Итоговая вероятность:</b> {probability:.2f}%")

    if SHOW_EXPLANATIONS:
        print_explanations(ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed, scenario)

if __name__ == "__main__":
    trading_strategy(SYMBOL, TIMEFRAME)
