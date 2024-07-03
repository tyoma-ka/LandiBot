import json
import os

# Get the current directory of the localization.py file
current_dir = os.path.dirname(__file__)

# Construct the path to the localization.json file
json_path = os.path.join(current_dir, 'localization.json')

# Load localization data
with open(json_path, 'r') as file:
    localization_data = json.load(file)

# Set default language
DEFAULT_LANGUAGE = 'sk'
LANGUAGES_AVAILABLE = localization_data.keys()


def get_text(key, lang='default'):
    in_all_lang = set()
    if lang == 'default':
        for language in localization_data:
            in_all_lang.add(localization_data[language].get(key, key))
        return in_all_lang
    if lang in LANGUAGES_AVAILABLE:
        text = localization_data[lang].get(key, key)
    else:
        text = localization_data[DEFAULT_LANGUAGE].get(key, key)
    return text


if __name__ == '__main__':
    print(get_text('timetable'))