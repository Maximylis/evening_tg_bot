from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram_calendar import DialogCalendar, DialogCalendarCallback
from datetime import datetime
import src.app.keyboards.kb as kb
from src.database.requests import (set_user, get_user, add_user_drink, get_user_drinks, get_drink_board)

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await set_user(message.from_user.id, message.from_user.username)
    await message.answer(f"Привет {message.from_user.username} !", reply_markup=kb.main)


@user_router.message(F.text == "Я выпил")
async def user_drink(message: Message):
    await set_user(message.from_user.id, message.from_user.username)
    await message.answer("Выбери дату:", reply_markup=await DialogCalendar().start_calendar())


@user_router.callback_query(DialogCalendarCallback.filter())
async def process_dialog_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    is_selected, selected_date = await DialogCalendar().process_selection(callback_query, callback_data)
    if is_selected:
        user = await get_user(callback_query.from_user.id)
        if selected_date <= datetime.now():
            await add_user_drink(user.id, selected_date)
            answer_text = (
                "Сюююююююда!!! Правильно, сегодня отдыхаем" if selected_date.strftime(
                    '%Y-%m-%d') == datetime.now().strftime('%Y-%m-%d')
                else "Одобряю твой поступок"
            )
            await callback_query.message.answer(answer_text, reply_markup=kb.main)
        else:
            await callback_query.message.answer(
                "Я так понимаю ты рассказал мне о своих планах, но все же выбери уже наступившую дату",
                reply_markup=kb.main)


@user_router.message(F.text == "Моя статистика")
async def mystats_handler(message: Message):
    await set_user(message.from_user.id, message.from_user.username)
    user = await get_user(message.from_user.id)
    drinks = await get_user_drinks(user.id)
    drink_unique_days_list = list(set([drink.action_dt.strftime('%Y-%m-%d') for drink in list(drinks)]))
    if len(drink_unique_days_list) > 0:
        message_text = "Ты пил в эти даты:\n-----------------------------------\n"
        for drink_day in drink_unique_days_list:
            message_text += f"{drink_day}\n"
    else:
        message_text = 'Я не знаю когда ты пил... Пора это исправлять.\nКогда выпьешь, нажми на кнопку "Я выпил"'
    await message.answer(message_text)


@user_router.message(F.text == "Лидерборд")
async def stats_handler(message: Message):
    await set_user(message.from_user.id, message.from_user.username)
    stats = await get_drink_board()
    stats_list = list(stats)
    if len(stats_list) > 0:
        drunk_today_users_list = []
        message_text = "Лидерборд\n-----------------------------------\nПользователь; Крайний раз пил; Дней трезвости\n-----------------------------------\n"
        for index, stats_element in enumerate(stats_list):
            days = stats_element.sober_time.days
            if days == 0:
                drunk_today_users_list.append(stats_element.user_name)
            message_text += f"{index + 1}) {stats_element.user_name};  {stats_element.last_drink.strftime('%Y-%m-%d')};  {days} дней\n"
        drunk_today_users_qty = len(drunk_today_users_list)
        message_text += "-----------------------------------"
        if drunk_today_users_qty > 0:
            message_suffix_you = "ты"
            message_suffix_i = ""
            if drunk_today_users_qty > 1:
                message_suffix_you = "вы"
                message_suffix_i = "и"
            message_text += f"""\n\n{", ".join(drunk_today_users_list)} - {message_suffix_you} сегодня хорош{message_suffix_i}, так держать !!!"""
        else:
            message_text += "\nСегодня еще никто не пил ? Займитесь делом !"
        message_text += f"\n\n{stats_list[-1].user_name} занимается ерундой, пора выпить..."
    else:
        message_text = "Я пока не собрал статистику. Пьем активнее !"
    await message.answer(message_text)
