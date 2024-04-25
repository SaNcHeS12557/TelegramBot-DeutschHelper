# -*- coding: utf-8 -*-
import telegram
import telebot
import requests
import json
import deepl
import os
# import wordfreq
from pprint import pprint
from german_nouns.lookup import Nouns

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
                            translation_ukrainian = "no translation found"
                            
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

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Hi, lets start! ")
    
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    word = message.text
    # if word size = 1 = try again
    if len(word) == 1:
        bot.reply_to(message, f'Error for: {word} / try another word :(')
        return
    article = get_article(word)
    if article:
        bot.reply_to(message, f'{article}')
    else:
        bot.reply_to(message, f'Error for: {word} / something went wrong :(')

    
bot.infinity_polling()