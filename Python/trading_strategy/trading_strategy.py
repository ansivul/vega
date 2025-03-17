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
        "symbols": ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "DOTUSDT", "LTCUSDT", "LINKUSDT"],
        "timeframe": "4h",
        "fgi_threshold_low": 25,
        "fgi_threshold_high": 75,
        "rsi_threshold_low": 30,
        "rsi_threshold_high": 70,
        "rsi_period": 14,
        "ema_short_period": 12,
        "ema_long_period": 26,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "bollinger_period": 20,
        "bollinger_deviation": 2,
        "support_resistance_window": 10,
        "show_explanations": True,
        "historical_data_limit": 500,
        "success_threshold": 0.01,
        "success_horizon": 8,
        "adx_period": 14
    }

SYMBOLS = settings.get("symbols", ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT", "DOTUSDT", "LTCUSDT", "LINKUSDT"])
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
HISTORICAL_DATA_LIMIT = settings.get("historical_data_limit", 500)
SUCCESS_THRESHOLD = settings.get("success_threshold", 0.01)
SUCCESS_HORIZON = settings.get("success_horizon", 8)
ADX_PERIOD = settings.get("adx_period", 14)

exchange = ccxt.bybit({'enableRateLimit': True})

def get_fgi():
    url = "https://api.alternative.me/fng/?limit=1"
    response = requests.get(url)
    data = response.json()
    return int(data['data'][0]['value'])

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
    ema_short = talib.EMA(df["close"].dropna(), timeperiod=short_period)
    ema_long = talib.EMA(df["close"].dropna(), timeperiod=long_period)
    return ema_short, ema_long

def calculate_macd(df, fast_period, slow_period, signal_period):
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

    historical_signals = []
    for i in range(len(df) - SUCCESS_HORIZON):
        if pd.isna(rsi.iloc[i]) or pd.isna(ema_short.iloc[i]) or pd.isna(macd.iloc[i]) or pd.isna(bb_upper.iloc[i]) or pd.isna(adx.iloc[i]):
            continue

        fgi = fgi_values[i] if i < len(fgi_values) else 50
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

        trend = "bullish" if current_ema_short > current_ema_long else "bearish"
        trend_strength = "strong" if current_adx > 25 else "weak"

        future_price = df['close'].iloc[i + SUCCESS_HORIZON]
        price_change = (future_price - current_price) / current_price
        success = None
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
    print("\n--- Пояснения ---")
    if scenario == "long" or scenario == "short":
        print(f"Сценарий: {'Согласованный сигнал (Long)' if scenario == 'long' else 'Согласованный сигнал (Short)'}")
        print("- FGI и RSI указывают в одном направлении (FGI низкий и RSI низкий для long, или FGI высокий и RSI высокий для short).")
    elif scenario == "divergence_long" or scenario == "divergence_short":
        print(f"Сценарий: Перекос сигналов ({'Long' if scenario == 'divergence_long' else 'Short'})")
        print("- Перекос: FGI и RSI противоречат друг другу (например, FGI высокий (жадность), но RSI низкий (перепроданность)).")
    else:
        print("Сценарий: Нейтральная зона")
        print("- FGI и RSI находятся в нейтральных значениях (не экстремальные).")

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

def trading_strategy(symbols, timeframe):
    fgi = get_fgi()  # Получаем FGI один раз для всех пар
    for symbol in symbols:
        print(f"\n{'='*50}\nАнализ для {symbol}\n{'='*50}")
        
        historical_df = fetch_ohlcv(symbol, timeframe, limit=HISTORICAL_DATA_LIMIT)
        df = fetch_ohlcv(symbol, timeframe, limit=max(EMA_LONG_PERIOD + MACD_SIGNAL, BOLLINGER_PERIOD, SUPPORT_RESISTANCE_WINDOW * 2) + 1)
        rsi = calculate_rsi(df, RSI_PERIOD).iloc[-1] if df is not None else None
        price, volume = get_price_volume(symbol, timeframe)
        ema_short, ema_long = calculate_ema(df, EMA_SHORT_PERIOD, EMA_LONG_PERIOD) if df is not None else (None, None)
        ema_short, ema_long = float(ema_short.iloc[-1]) if ema_short is not None else None, float(ema_long.iloc[-1]) if ema_long is not None else None
        macd, macd_signal = calculate_macd(df, MACD_FAST, MACD_SLOW, MACD_SIGNAL) if df is not None else (None, None)
        macd, macd_signal = float(macd.iloc[-1]) if macd is not None else None, float(macd_signal.iloc[-1]) if macd_signal is not None else None
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df, BOLLINGER_PERIOD, BOLLINGER_DEVIATION) if df is not None else (None, None, None)
        bb_upper, bb_middle, bb_lower = float(bb_upper.iloc[-1]) if bb_upper is not None else None, float(bb_middle.iloc[-1]) if bb_middle is not None else None, float(bb_lower.iloc[-1]) if bb_lower is not None else None
        support, resistance = calculate_support_resistance(df, SUPPORT_RESISTANCE_WINDOW) if df is not None else (None, None)
        adx = calculate_adx(df, ADX_PERIOD).iloc[-1] if df is not None else None

        if (rsi is None or price is None or volume is None or 
            ema_short is None or macd is None or bb_upper is None or support is None or adx is None):
            print(f"Ошибка: данные для {symbol} недоступны")
            continue

        prev_volume = df['volume'].iloc[-2] if len(df) >= 2 else 0
        fgi_values = [fgi] * len(historical_df) if historical_df is not None else []
        success_rates = analyze_historical_signals(historical_df, fgi_values)

        scenario = None
        recommendation = None
        volume_confirmed = False
        ema_confirmed = False
        macd_confirmed = False
        bollinger_confirmed = False
        sr_confirmed = False
        trend = "bullish" if ema_short > ema_long else "bearish"
        trend_strength = "strong" if adx > 25 else "weak"

        if fgi <= FGI_THRESHOLD_LOW and rsi <= RSI_THRESHOLD_LOW:
            scenario = "long"
            volume_confirmed = volume > prev_volume * 1.2
            ema_confirmed = ema_short > ema_long
            macd_confirmed = macd > macd_signal
            bollinger_confirmed = price <= bb_lower
            sr_confirmed = abs(price - support) / price < 0.02
            confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                  f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                  f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                  f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                  f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
            confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
            if confirmed_count >= 3:
                recommendation = f"FGI = {fgi} (рынок в страхе), RSI = {rsi:.2f} (перепроданность). Рекомендую покупку ({confirmation_status})"
            else:
                recommendation = f"FGI = {fgi} (рынок в страхе), RSI = {rsi:.2f} (перепроданность). Сигнал на покупку слабый, ждем подтверждения ({confirmation_status})"

        elif fgi >= FGI_THRESHOLD_HIGH and rsi >= RSI_THRESHOLD_HIGH:
            scenario = "short"
            volume_confirmed = volume > prev_volume * 1.2
            ema_confirmed = ema_short < ema_long
            macd_confirmed = macd < macd_signal
            bollinger_confirmed = price >= bb_upper
            sr_confirmed = abs(price - resistance) / price < 0.02
            confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                  f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                  f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                  f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                  f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
            confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
            if confirmed_count >= 3:
                recommendation = f"FGI = {fgi} (рынок в жадности), RSI = {rsi:.2f} (перекупленность). Рекомендую продажу ({confirmation_status})"
            else:
                recommendation = f"FGI = {fgi} (рынок в жадности), RSI = {rsi:.2f} (перекупленность). Сигнал на продажу слабый, ждем подтверждения ({confirmation_status})"

        elif fgi >= FGI_THRESHOLD_HIGH and rsi <= RSI_THRESHOLD_LOW:
            scenario = "divergence_long"
            volume_confirmed = volume > prev_volume * 1.2
            ema_confirmed = ema_short > ema_long
            macd_confirmed = macd > macd_signal
            bollinger_confirmed = price <= bb_lower
            sr_confirmed = abs(price - support) / price < 0.02
            confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                  f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                  f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                  f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                  f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
            confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
            if confirmed_count >= 3:
                recommendation = f"Перекос: FGI = {fgi} (жадность), RSI = {rsi:.2f} (перепроданность). Рекомендую покупку ({confirmation_status})"
            else:
                recommendation = f"Перекос: FGI = {fgi} (жадность), RSI = {rsi:.2f} (перепроданность). Сигнал на покупку слабый, ждем подтверждения ({confirmation_status})"

        elif fgi <= FGI_THRESHOLD_LOW and rsi >= RSI_THRESHOLD_HIGH:
            scenario = "divergence_short"
            volume_confirmed = volume > prev_volume * 1.2
            ema_confirmed = ema_short < ema_long
            macd_confirmed = macd < macd_signal
            bollinger_confirmed = price >= bb_upper
            sr_confirmed = abs(price - resistance) / price < 0.02
            confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                  f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                  f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                  f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                  f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
            confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])
            if confirmed_count >= 3:
                recommendation = f"Перекос: FGI = {fgi} (страх), RSI = {rsi:.2f} (перекупленность). Рекомендую продажу ({confirmation_status})"
            else:
                recommendation = f"Перекос: FGI = {fgi} (страх), RSI = {rsi:.2f} (перекупленность). Сигнал на продажу слабый, ждем подтверждения ({confirmation_status})"

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
                confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                      f"EMA: {'подтверждено' if ema_confirmed else 'не подтверждено'}, "
                                      f"MACD: {'подтверждено' if macd_confirmed else 'не подтверждено'}, "
                                      f"Bollinger Bands: {'подтверждено' if bollinger_confirmed else 'не подтверждено'}, "
                                      f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed else 'не подтверждено'}")
                recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Возможна покупка ({confirmation_status})"
            elif confirmed_count_short >= 3:
                confirmation_status = (f"Объем: {'подтверждено' if volume_confirmed else 'не подтверждено'}, "
                                      f"EMA: {'подтверждено' if ema_confirmed_short else 'не подтверждено'}, "
                                      f"MACD: {'подтверждено' if macd_confirmed_short else 'не подтверждено'}, "
                                      f"Bollinger Bands: {'подтверждено' if bollinger_confirmed_short else 'не подтверждено'}, "
                                      f"Уровни поддержки/сопротивления: {'подтверждено' if sr_confirmed_short else 'не подтверждено'}")
                recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Возможна продажа ({confirmation_status})"
            else:
                recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Воздержаться или ждать пробоя с объемом"

        if recommendation is None:
            recommendation = f"Нейтральная зона: FGI = {fgi}, RSI = {rsi:.2f}. Нет четкого сигнала, ждите дополнительных данных."

        print("=== Анализ рынка ===")
        print(f"Актив: {symbol}, Таймфрейм: {timeframe}")
        print(f"Текущая цена: {price:.2f} USDT, Объем: {volume:.2f}")
        print(f"EMA: Short={ema_short:.2f}, Long={ema_long:.2f}, {'Бычий тренд' if ema_short > ema_long else 'Медвежий тренд'}")
        print(f"MACD: Line={macd:.2f}, Signal={macd_signal:.2f}, {'Бычий сигнал' if macd > macd_signal else 'Медвежий сигнал'}")
        print(f"Bollinger Bands: Upper={bb_upper:.2f}, Middle={bb_middle:.2f}, Lower={bb_lower:.2f}")
        print(f"Уровни поддержки/сопротивления: Поддержка={support:.2f}, Сопротивление={resistance:.2f}")
        print(f"Рекомендация: {recommendation}")

        print("\n=== Рекомендации от ИИ ===")
        probability = calculate_probability(scenario, trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed)
        confirmed_count = sum([volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed])

        if scenario in ["long", "divergence_long"]:
            if confirmed_count >= 3:
                if probability >= 50:
                    print(f"Сильный сигнал для покупки. Шанс успеха: {probability:.0f}%. Рекомендуется действовать на основе текущих данных.")
                else:
                    print(f"Сигнал для покупки есть, но шансы успеха низкие: {probability:.0f}%. Лучше подождать более благоприятных условий.")
            else:
                print(f"Сигнал для покупки слабый из-за недостатка подтверждений. Шанс успеха: {probability:.0f}%. Лучше подождать улучшения условий.")
        elif scenario in ["short", "divergence_short"]:
            if confirmed_count >= 3:
                if probability >= 50:
                    print(f"Сильный сигнал для продажи. Шанс успеха: {probability:.0f}%. Рекомендуется действовать на основе текущих данных.")
                else:
                    print(f"Сигнал для продажи есть, но шансы успеха низкие: {probability:.0f}%. Лучше подождать более благоприятных условий.")
            else:
                print(f"Сигнал для продажи слабый из-за недостатка подтверждений. Шанс успеха: {probability:.0f}%. Лучше подождать улучшения условий.")
        else:
            probability_long = calculate_probability("long", trend, trend_strength, success_rates, volume_confirmed, ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed)
            probability_short = calculate_probability("short", trend, trend_strength, success_rates, volume_confirmed, ema_confirmed_short, macd_confirmed_short, bollinger_confirmed_short, sr_confirmed_short)
            if confirmed_count_long >= 3 and probability_long >= 50:
                print(f"Рынок в нейтральной зоне, но есть слабый сигнал для покупки. Шанс успеха: {probability_long:.0f}%. Рассмотрите покупку, если цена у поддержки или нижней полосы Bollinger.")
            elif confirmed_count_short >= 3 and probability_short >= 50:
                print(f"Рынок в нейтральной зоне, но есть слабый сигнал для продажи. Шанс успеха: {probability_short:.0f}%. Рассмотрите продажу, если цена у сопротивления или верхней полосы Bollinger.")
            else:
                print(f"Рынок в нейтральной зоне. Шанс успеха для покупки: {probability_long:.0f}%, для продажи: {probability_short:.0f}%. Воздержитесь или ждите пробоя с объемом.")

        key = (scenario, trend, trend_strength)
        base_probability = 50
        if key in success_rates and success_rates[key]["total"] > 0:
            base_probability = (success_rates[key]["success"] / success_rates[key]["total"]) * 100
        total_indicators = 5
        confirmation_bonus = (confirmed_count / total_indicators) * 30

        print("\n--- Расчет вероятности успеха ---")
        print(f"Базовая вероятность: {base_probability:.2f}%")
        print(f"  * Рассчитана на основе исторических данных для сценария '{scenario}', тренда '{trend}' и силы тренда '{trend_strength}'.")
        print(f"  * Из {success_rates.get(key, {'total': 0})['total']} сигналов было успешно: {success_rates.get(key, {'success': 0})['success']}.")
        print(f"  * Формула: (успешные сигналы / общее количество сигналов) * 100 = {base_probability:.2f}%.")
        print(f"Бонус за подтверждения: {confirmation_bonus:.2f}%")
        print(f"  * Всего индикаторов: {total_indicators} (объем, EMA, MACD, Bollinger Bands, уровни поддержки/сопротивления).")
        print(f"  * Подтверждено индикаторов: {confirmed_count}.")
        print(f"  * Формула: (количество подтверждений / общее количество индикаторов) * 30 = {confirmation_bonus:.2f}%.")
        print(f"Итоговая вероятность: {probability:.2f}%")
        print(f"  * Формула: базовая вероятность + бонус за подтверждения = {base_probability:.2f} + {confirmation_bonus:.2f} = {probability:.2f}%.")

        if SHOW_EXPLANATIONS:
            print_explanations(ema_confirmed, macd_confirmed, bollinger_confirmed, sr_confirmed, scenario)

        time.sleep(1)  # Задержка 1 секунда между запросами для избежания rate limit

if __name__ == "__main__":
    trading_strategy(SYMBOLS, TIMEFRAME)