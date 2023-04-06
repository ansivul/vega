import os
from google.cloud import texttospeech


def synthesize_text(text):
    """Синтезирует речь из входного текста."""
    client = texttospeech.TextToSpeechClient()

    # Задаем параметры голоса
    voice = texttospeech.VoiceSelectionParams(
        language_code="ru-RU",
        name="ru-RU-Wavenet-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    # Задаем параметры аудио
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0,
        volume_gain_db=0.0,
    )

    # Синтезируем текст
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')



def main():  
    
    key = 'AIzaSyCJFz8tOaLZXO3Y67CNga4Yfw3eEYb-peY'
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./google-cloud-key1.json"
    synthesize_text('Это был просто кошмарный сон. Вершины лунных гор стремительно приближались. До удара осталось пять секунд.')
    # print(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    
    # # Инициализируем клиент для синтеза речи
    # client = texttospeech.TextToSpeechClient()

    # # Создаем запрос для синтеза речи
    # input_text = texttospeech.SynthesisInput(text="Это был просто кошмарный сон. Вершины лунных гор стремительно приближались. До удара осталось пять секунд. Девушку развернуло спиной к острым скалам. По позвоночнику прокатилась ледяная волна — человек предпочитает встречать смерть лицом. Четыре секунды. Космический катер падал на двадцать метров впереди и ниже.")
    # voice = texttospeech.VoiceSelectionParams(
    #     language_code="ru-RU", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    # )
    # audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

    # # Синтезируем речь и сохраняем ее в аудио-файл
    # response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    # with open("output.wav", "wb") as out:
    #     out.write(response.audio_content)
    #     print('Audio content written to file "output.wav"')


if __name__ == '__main__':
    main()   