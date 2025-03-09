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
        "symbol": "BTCUSDT",                    # Символ торговой пары (например, BTCUSDT для Bitcoin к USDT) ETHUSDT XRP/USDT BNB/USDT
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

# Подключение к Bybit
exchange = ccxt.bybit({
    'enableRateLimit': True,
})

# Функция для получения FGI
def get_fgi():
    url = "https://api.alternative.me/fng/?limit=1"
    response = requests.get(url)
    data = response.json()
    return int(data['data'][0]['value'])

# Функция для получения данных OHLCV
def fetch_ohlcv(symbol, timeframe, limit=HISTORICAL_DATA_LIMIT):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Ошибка при загрузке данных для {symbol}: {e}")
        return None

# Функция для расчета RSI
def calculate_rsi(df, period):
    if df is None or len(df) < period + 1:
        print(f"Недостаточно данных для расчета RSI с period={period}: {len(df) if df is not None else 'None'} свечей")
        return None
    return talib.RSI(df["close"], timeperiod=period)

# Функция для расчета EMA
def calculate_ema(df, short_period, long_period):
    ema_short = talib.EMA(df["close"].dropna(), timeperiod=short_period)
    ema_long = talib.EMA(df["close"].dropna(), timeperiod=long_period)
    return ema_short, ema_long

# Функция для расчета MACD
def calculate_macd(df, fast_period, slow_period, signal_period):
    macd, macd_signal, _ = talib.MACD(df["close"].dropna(), fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period)
    return macd, macd_signal

# Функция для расчета Bollinger Bands
def calculate_bollinger_bands(df, period, deviation):
    if df is None or len(df) < period:
        print(f"Недостаточно данных для расчета Bollinger Bands с period={period}: {len(df) if df is not None else 'None'} свечей")
        return None, None, None
    upper, middle, lower = talib.BBANDS(df["close"].dropna(), timeperiod=period, nbdevup=deviation, nbdevdn=deviation, matype=0)
    return upper, middle, lower

# Функция для расчета уровней поддержки и сопротивления
def calculate_support_resistance(df, window):
    if df is None or len(df) < window * 2:
        print(f"Недостаточно данных для расчета уровней поддержки/сопротивления с window={window}: {len(df) if df is not None else 'None'} свечей")
        return None, None
    recent_data = df["close"].iloc[-window*2:]
    support = float(recent_data.min())
    resistance = float(recent_data.max())
    return support, resistance

# Функция для расчета ADX (сила тренда)
def calculate_adx(df, period):
    if df is None or len(df) < period + 1:
        print(f"Недостаточно данных для расчета ADX с period={period}: {len(df) if df is not None else 'None'} свечей")
        return None
    adx = talib.ADX(df["high"], df["low"], df["close"], timeperiod=period)
    return adx

# Функция для получения текущей цены и объема
def get_price_volume(symbol, timeframe):
    df = fetch_ohlcv(symbol, timeframe, limit=2)
    if df is not None and len(df) >= 2:
        return df['close'].iloc[-1], df['volume'].iloc[-1]
    return None, None

# Функция для анализа исторических сигналов
def analyze_historical_signals(df, fgi_values):
    if df is None or len(df) < HISTORICAL_DATA_LIMIT:
        print("Недостаточно данных для исторического анализа")
        return {}

    # Рассчитываем индикаторы для исторических данных
    rsi = calculate_rsi(df, RSI_PERIOD)
    ema_short, ema_long = calculate_ema(df, EMA_SHORT_PERIOD, EMA_LONG_PERIOD)
    macd, macd_signal = calculate_macd(df, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df, BOLLINGER_PERIOD, BOLLINGER_DEVIATION)
    adx = calculate_adx(df, ADX_PERIOD)

    historical_signals = []
    for i in range(len(df) - SUCCESS_HORIZON):
        # Пропускаем, если данных недостаточно
        if pd.isna(rsi.iloc[i]) or pd.isna(ema_short.iloc[i]) or pd.isna(macd.iloc[i]) or pd.isna(bb_upper.iloc[i]) or pd.isna(adx.iloc[i]):
            continue

        # Получаем значения индикаторов на момент i
        fgi = fgi_values[i] if i < len(fgi_values) else 50  # Если FGI нет, используем нейтральное значение
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

        # Определяем сценарий
        scenario = None
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

        # Определяем тренд
        trend = "bullish" if current_ema_short > current_ema_long else "bearish"
        trend_strength = "strong" if current_adx > 25 else "weak"

        # Проверяем успешность сигнала
        future_price = df['close'].iloc[i + SUCCESS_HORIZON]
        price_change = (future_price - current_price) / current_price
        success = None
        if scenario in ["long", "divergence_long"]:
            success = price_change >= SUCCESS_THRESHOLD
        elif scenario in ["short", "divergence_short"]:
            success = price_change <= -SUCCESS_THRESHOLD
        else:
            continue  # Пропускаем нейтральные сигналы

        # Сохраняем сигнал
        signal = {
            "scenario": scenario,
            "trend": trend,
            "trend_strength": trend_strength,
            "success": success
        }
        historical_signals.append(signal)

    # Агрегируем результаты
    success_rates = {}
    for signal in historical_signals:
        key = (signal["scenario"], signal["trend"], signal["trend_strength"])
        if key not in success_rates:
            success_rates[key] = {"total": 0, "success": 0}
        success_rates[key]["total"] += 1
        if signal["success"]:
            success_rates[key]["success"] += 1

    return success_rates

# Функция для расчета вероятности на основе исторических данных
def calculate_probability(scenario, trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed):
    # Базовая вероятность на основе исторических данных
    key = (scenario, trend, trend_strength)
    base_probability = 50  # Если нет исторических данных
    if key in success_rates and success_rates[key]["total"] > 0:
        base_probability = (success_rates[key]["success"] / success_rates[key]["total"]) * 100

    # Корректировка на основе текущих подтверждений индикаторов
    confirmed_count = sum([1 for c in [volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed] if c])
    total_indicators = 5
    confirmation_bonus = (confirmed_count / total_indicators) * 30  # Максимум +30% за подтверждения
    probability = base_probability + confirmation_bonus

    # Ограничиваем вероятность
    return min(max(probability, 20), 90)

# Функция для вывода пояснений
def print_explanations(ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed, scenario):
    print("\n--- Пояснения ---")
    if scenario == "long" or scenario == "short":
        print(f"Сценарий: {'Согласованный сигнал (Long)' if scenario == 'long' else 'Согласованный сигнал (Short)'}")
        print("- FGI и RSI указывают в одном направлении (FGI низкий и RSI низкий для long, или FGI высокий и RSI высокий для short).")
        print("- В этом случае EMA, MACD, Bollinger Bands и уровни поддержки/сопротивления не проверяются, так как сигнал уже сильный.")
    elif scenario == "divergence_long" or scenario == "divergence_short":
        print(f"Сценарий: Перекос сигналов ({'Long' if scenario == 'divergence_long' else 'Short'})")
        print("- Перекос: FGI и RSI противоречат друг другу (например, FGI высокий (жадность), но RSI низкий (перепроданность)).")
        print("- Проверяются дополнительные индикаторы для подтверждения:")
        print("  * Объем: Подтверждается, если текущий объем больше предыдущего на 20% (volume > prev_volume * 1.2).")
        print("  * EMA (Экспоненциальная скользящая средняя):")
        print("    - Бычий тренд: Короткая EMA (EMA Short) выше длинной EMA (EMA Long) — указывает на восходящий тренд.")
        print("    - Медвежий тренд: Короткая EMA ниже длинной EMA — указывает на нисходящий тренд.")
        print(f"    - {'Подтверждено' if ema_confirmed else 'Не подтверждено'}: {'EMA поддерживает сигнал' if ema_confirmed else 'EMA не поддерживает сигнал (тренд противоположный)'}.")
        print("  * MACD (Схождение/расхождение скользящих средних):")
        print("    - Бычий сигнал: MACD Line выше Signal Line — указывает на восходящий импульс.")
        print("    - Медвежий сигнал: MACD Line ниже Signal Line — указывает на нисходящий импульс.")
        print(f"    - {'Подтверждено' if macd_confirmed else 'Не подтверждено'}: {'MACD поддерживает сигнал' if macd_confirmed else 'MACD не поддерживает сигнал (импульс противоположный)'}.")
        print("  * Bollinger Bands (Полосы Боллинджера):")
        print("    - Цена у нижней полосы или ниже: Указывает на перепроданность (поддерживает long).")
        print("    - Цена у верхней полосы или выше: Указывает на перекупленность (поддерживает short).")
        print(f"    - {'Подтверждено' if bollinger_confirmed else 'Не подтверждено'}: {'Bollinger Bands поддерживают сигнал' if bollinger_confirmed else 'Bollinger Bands не поддерживают сигнал (цена не в экстремальной зоне)'}.")
        print("  * Уровни поддержки/сопротивления:")
        print("    - Цена у поддержки: Указывает на вероятный разворот вверх (поддерживает long).")
        print("    - Цена у сопротивления: Указывает на вероятный разворот вниз (поддерживает short).")
        print(f"    - {'Подтверждено' if sr_confirmed else 'Не подтверждено'}: {'Уровни поддержки/сопротивления поддерживают сигнал' if sr_confirmed else 'Уровни поддержки/сопротивления не поддерживают сигнал (цена не у ключевого уровня)'}.")
    else:
        print("Сценарий: Нейтральная зона")
        print("- FGI и RSI находятся в нейтральных значениях (не экстремальные).")
        print("- Дополнительные индикаторы могут дать сигнал:")
        print("  * Bollinger Bands: Цена у нижней полосы (возможный long) или у верхней полосы (возможный short).")
        print("  * Уровни поддержки/сопротивления: Цена у поддержки (возможный long) или у сопротивления (возможный short).")

# Основная логика стратегии
def trading_strategy(symbol, timeframe):
    # Загружаем исторические данные для анализа
    historical_df = fetch_ohlcv(symbol, timeframe, limit=HISTORICAL_DATA_LIMIT)
    fgi = get_fgi()
    df = fetch_ohlcv(symbol, timeframe, limit=max(EMA_LONG_PERIOD + MACD_SIGNAL, BOLLINGER_PERIOD, SUPPORT_RESISTANCE_WINDOW * 2) + 1)
    rsi = calculate_rsi(df, RSI_PERIOD).iloc[-1]
    price, volume = get_price_volume(symbol, timeframe)
    ema_short, ema_long = calculate_ema(df, EMA_SHORT_PERIOD, EMA_LONG_PERIOD)
    ema_short, ema_long = float(ema_short.iloc[-1]), float(ema_long.iloc[-1])
    macd, macd_signal = calculate_macd(df, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    macd, macd_signal = float(macd.iloc[-1]), float(macd_signal.iloc[-1])
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df, BOLLINGER_PERIOD, BOLLINGER_DEVIATION)
    bb_upper, bb_middle, bb_lower = float(bb_upper.iloc[-1]), float(bb_middle.iloc[-1]), float(bb_lower.iloc[-1])
    support, resistance = calculate_support_resistance(df, SUPPORT_RESISTANCE_WINDOW)
    adx = calculate_adx(df, ADX_PERIOD).iloc[-1]

    if (rsi is None or price is None or volume is None or 
        ema_short is None or macd is None or bb_upper is None or support is None or adx is None):
        print("Ошибка: данные недоступны")
        return

    prev_volume = df['volume'].iloc[-2] if len(df) >= 2 else 0

    # Анализ исторических сигналов
    # Для упрощения используем текущий FGI для всех исторических данных
    fgi_values = [fgi] * len(historical_df)  # В реальном приложении нужно собирать исторические FGI
    success_rates = analyze_historical_signals(historical_df, fgi_values)

    # Определяем сценарий и тренд
    scenario = None
    recommendation = None
    ema_confirmed = False
    macd_confirmed = False
    bollinger_confirmed = False
    sr_confirmed = False
    trend = "bullish" if ema_short > ema_long else "bearish"
    trend_strength = "strong" if adx > 25 else "weak"

    if fgi <= FGI_THRESHOLD_LOW and rsi <= RSI_THRESHOLD_LOW:
        scenario = "long"
        recommendation = f"Открыть long: FGI = {fgi} (страх), RSI = {rsi:.2f} (перепроданность)"
    elif fgi >= FGI_THRESHOLD_HIGH and rsi >= RSI_THRESHOLD_HIGH:
        scenario = "short"
        recommendation = f"Открыть short: FGI = {fgi} (жадность), RSI = {rsi:.2f} (перекупленность)"
    elif fgi >= FGI_THRESHOLD_HIGH and rsi <= RSI_THRESHOLD_LOW:
        scenario = "divergence_long"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short > ema_long
        macd_confirmed = macd > macd_signal
        bollinger_confirmed = price <= bb_lower
        sr_confirmed = abs(price - support) / price < 0.02
        if volume_confirmed and ema_confirmed and macd_confirmed and bollinger_confirmed and sr_confirmed:
            recommendation = f"Перекос: FGI = {fgi} (жадность), RSI = {rsi:.2f} (перепроданность). Открыть long (объем, EMA, MACD, Bollinger Bands, уровни поддержки/сопротивления подтверждают)"
        else:
            confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                  f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                  f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                  f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                  f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
            recommendation = f"Перекос: FGI = {fgi} (жадность), RSI = {rsi:.2f} (перепроданность). Ждем подтверждения ({confirmation_status})"
    elif fgi <= FGI_THRESHOLD_LOW and rsi >= RSI_THRESHOLD_HIGH:
        scenario = "divergence_short"
        volume_confirmed = volume > prev_volume * 1.2
        ema_confirmed = ema_short < ema_long
        macd_confirmed = macd < macd_signal
        bollinger_confirmed = price >= bb_upper
        sr_confirmed = abs(price - resistance) / price < 0.02
        if volume_confirmed and ema_confirmed and macd_confirmed and bollinger_confirmed and sr_confirmed:
            recommendation = f"Перекос: FGI = {fgi} (страх), RSI = {rsi:.2f} (перекупленность). Открыть short (объем, EMA, MACD, Bollinger Bands, уровни поддержки/сопротивления подтверждают)"
        else:
            confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                  f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                  f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                  f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                  f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
            recommendation = f"Перекос: FGI = {fgi} (страх), RSI = {rsi:.2f} (перекупленность). Ждем подтверждения ({confirmation_status})"
    else:
        scenario = "neutral"
        if price <= bb_lower or abs(price - support) / price < 0.02:
            recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Возможный long (цена у нижней полосы Bollinger или у поддержки)"
        elif price >= bb_upper or abs(price - resistance) / price < 0.02:
            recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Возможный short (цена у верхней полосы Bollinger или у сопротивления)"
        else:
            recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Воздержаться или ждать пробоя с объемом"

    # Вывод базовой информации
    print("=== Анализ рынка ===")
    print(f"Актив: {symbol}, Таймфрейм: {timeframe}")
    print(f"Текущая цена: {price:.2f} USDT, Объем: {volume:.2f}")
    print(f"EMA: Short={ema_short:.2f}, Long={ema_long:.2f}, {'Бычий тренд' if ema_short > ema_long else 'Медвежий тренд'}")
    print(f"MACD: Line={macd:.2f}, Signal={macd_signal:.2f}, {'Бычий сигнал' if macd > macd_signal else 'Медвежий сигнал'}")
    print(f"Bollinger Bands: Upper={bb_upper:.2f}, Middle={bb_middle:.2f}, Lower={bb_lower:.2f}")
    print(f"Уровни поддержки/сопротивления: Поддержка={support:.2f}, Сопротивление={resistance:.2f}")
    print(f"Рекомендация: {recommendation}")

    # Расчет вероятности и рекомендации от ИИ
    if scenario in ["divergence_long", "divergence_short"]:
        probability = calculate_probability(scenario, trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed)
        if scenario == "divergence_long" and (volume_confirmed or ema_confirmed or macd_confirmed or bollinger_confirmed or sr_confirmed):
            print("\n=== Рекомендации от ИИ ===")
            print(f"Советую рассмотреть покупку (long) с учетом перекоса. Шанс успеха: {probability:.0f}%. Рекомендуется дождаться полного подтверждения всех индикаторов для снижения риска.")
        elif scenario == "divergence_short" and (volume_confirmed or ema_confirmed or macd_confirmed or bollinger_confirmed or sr_confirmed):
            print("\n=== Рекомендации от ИИ ===")
            print(f"Советую рассмотреть продажу (short) с учетом перекоса. Шанс успеха: {probability:.0f}%. Рекомендуется дождаться полного подтверждения всех индикаторов для снижения риска.")
        else:
            print("\n=== Рекомендации от ИИ ===")
            print(f"Сигнал слабый из-за недостатка подтверждений. Шанс успеха: {probability:.0f}%. Рекомендуется воздержаться или ждать улучшения условий.")
    elif scenario == "long" or scenario == "short":
        probability = calculate_probability(scenario, trend, trend_strength, success_rates, True, True, True, True, True)
        print("\n=== Рекомендации от ИИ ===")
        print(f"Сильный сигнал для {'покупки (long)' if scenario == 'long' else 'продажи (short)'}. Шанс успеха: {probability:.0f}%. Рекомендуется войти в позицию с учетом текущих рыночных данных.")
    else:
        probability = calculate_probability(scenario, trend, trend_strength, success_rates, False, False, False, price <= bb_lower or price >= bb_upper, abs(price - support) / price < 0.02 or abs(price - resistance) / price < 0.02)
        print("\n=== Рекомендации от ИИ ===")
        print(f"Рынок в нейтральной зоне. Шанс успеха: {probability:.0f}%. {'Рассмотрите long, если цена у поддержки или нижней полосы Bollinger.' if price <= bb_lower or abs(price - support) / price < 0.02 else ''} {'Рассмотрите short, если цена у сопротивления или верхней полосы Bollinger.' if price >= bb_upper or abs(price - resistance) / price < 0.02 else ''} В противном случае воздержитесь.")

    # Вывод пояснений (опционально)
    if SHOW_EXPLANATIONS:
        print_explanations(ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed, scenario)

# Запуск программы
if __name__ == "__main__":
    trading_strategy(SYMBOL, TIMEFRAME)