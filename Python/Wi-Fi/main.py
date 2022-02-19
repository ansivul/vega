import subprocess

def fetch_wifi_pass():
    wifi_profile_data = subprocess.check_output('netsh wlan show profiles').decode('utf-8').split('\n')
    profiles = [i.split(':')[1].strip() for i in wifi_profile_data if 'All User Profile' in i]
    for profile in profiles:
        profile_info = subprocess.check_output(f'netsh wlan show profile "{profile}" key=clear').decode('utf-8').split('\n')
        try:
            password = [i.split(':')[1].strip() for i in profile_info if 'Key Content' in i][0]
        except IndexError:
            password = None
        with open(file='wifi.txt', mode='a', encoding='utf-8') as file:
            file.write(f'Profile: {profile}\nPassword: {password}\n{"#"*20}\n')

def main():
    fetch_wifi_pass()

if __name__ == '__main__':
    main()
