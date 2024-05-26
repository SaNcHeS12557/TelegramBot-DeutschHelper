# -*- coding: utf-8 -*-
import telegram
import telebot
import requests
import json
import deepl
import os
# import wordfreq
from german_nouns.lookup import Nouns
from bs4 import BeautifulSoup

TELEGRAM_API_KEY = os.environ.get('deutschHelperTelegramBotToken')
DEEPL_API_KEY = os.environ.get('deeeplToken')

bot = telebot.TeleBot(TELEGRAM_API_KEY) # telegram bot
translator = deepl.Translator(DEEPL_API_KEY) # deepl translator
nouns = Nouns() # dictionary of nouns

def get_article(word):
    word_info = nouns[word]

    if word_info:
        response = ""
        found_genuses = set()  # processed genuses
        for variation in word_info:
            genuses = [variation.get(f'genus {i}', variation.get('genus')) for i in range(1, 5)]
            # plural_word = variation['flexion']['nominativ plural']
            articles = {
                'm': {'definite': 'der', 'indefinite': 'ein'},
                'f': {'definite': 'die', 'indefinite': 'eine'},
                'n': {'definite': 'das', 'indefinite': 'ein'},
            }

            for genus in genuses:
                if genus not in found_genuses:
                    article_info = articles.get(genus, {})
                    plural_word = 'немає'
                    if 'nominativ plural' in variation['flexion']:
                        plural_word = variation['flexion'].get('nominativ plural', 'немає')
                    if article_info:
                        articledWord = f"{article_info['definite']} {word}"
                        translation_english = translator.translate_text(articledWord, target_lang="EN-GB", source_lang="DE")
                        if not translation_english:
                            translation_english = "no translation found"
                        translation_ukrainian = translator.translate_text(articledWord, target_lang="UK", source_lang="DE")
                        if not translation_ukrainian:
                            translation_ukrainian = "переклад не знайдено"
                            
                        # word_freq = wordfreq.word_frequency(articledWord, 'de', wordlist='best', minimum=0.0) * 1000000 
                        response += f"**{word.capitalize()}** ({genus}):\n"
                        
                        # get plural form of word
                        response += f"Множина: {plural_word}\n"
                            
                        response += f"- Означений артикль: {article_info['definite']}\n"
                        response += f"- Неозначений артикль: {article_info['indefinite']}\n"
                        # response += f"- Частота вживання: {word_freq}%\n"
                        response += f"\U0001F1EC\U0001F1E7: {translation_english}\n"
                        response += f"\U0001F1FA\U0001F1E6: {translation_ukrainian}\n\n"

                        found_genuses.add(genus)
                    break

        return response.strip()
    
def clean_conjugation_text(text):
    return ''.join(char for char in text if not char.isdigit())

def get_verb_info(word):
    url = f"https://www.verbformen.com/conjugation/?w={word}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        conjugation_info = soup.find('p', {'id': 'stammformen'}).text.strip()
        parts = conjugation_info.split('·')
        
        third_person_singular = clean_conjugation_text(parts[0].strip())
        preterite = clean_conjugation_text(parts[1].strip())
        perfect = clean_conjugation_text(parts[2].strip())

        translation_english = translator.translate_text(word + ' (verb)', target_lang="EN-GB", source_lang="DE").text.replace(" (verb)", "")
        if not translation_english:
            translation_english = "no translation found"

        translation_ukrainian = translator.translate_text(word + ' (verb)', target_lang="UK", source_lang="DE").text.replace(" (дієслово)", "")
        if not translation_ukrainian:
            translation_ukrainian = "переклад не знайдено"

        response = f"**{word}**:\n"
        response += f"- Третя особа: {third_person_singular}\n"
        response += f"- Претерітум: {preterite}\n"
        response += f"- Перфект: {perfect}\n"
        response += f"\U0001F1EC\U0001F1E7: {translation_english}\n"
        response += f"\U0001F1FA\U0001F1E6: {translation_ukrainian}\n\n"

        return response.strip()

    except AttributeError:
        return None


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Hi, let's start! ")
    
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    word = message.text.strip() #.lower()
    if len(word) == 1:
        bot.reply_to(message, f'Error for: {word} / try another word :(')
        return
    
    # if word - capital letter => priority for noun, else if not capital letter => priority for verb
    if word[0].isupper():
        article = get_article(word)
        if article:
            bot.reply_to(message, f'{article}')
        else:
            bot.reply_to(message, f'Error for: {word} / something went wrong :(')
    else:
        verb_info = get_verb_info(word)
        if verb_info:
            bot.reply_to(message, f'{verb_info}')
        else:
            bot.reply_to(message, f'Error for: {word} / something went wrong :(')
    
bot.infinity_polling()