from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    UnauthorizedError
)
from telethon.functions import messages, account
from telethon.sync import TelegramClient
from telethon.types import (
    InputBotAppShortName,
    AppWebViewResultUrl
)
from urllib.parse import unquote
from config import settings
import asyncio, json, os, sys

class Seed:
    def __init__(self) -> None:
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'alb.seeddao.org',
            'Origin': 'https://cf.seeddao.org',
            'Pragma': 'no-cache',
            'Referer': 'https://cf.seeddao.org/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    @staticmethod
    def clear_terminal():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def print_timestamp(message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_query(self, session: str):
        try:
            async with TelegramClient(session=f'sessions/{session}', api_id=settings.API_ID, api_hash=settings.API_HASH) as client:
                try:
                    if not client.is_connected():
                        await client.connect()
                except (AuthKeyUnregisteredError, UnauthorizedError, UserDeactivatedBanError, UserDeactivatedError) as err:
                    raise err

                me = await client.get_me()
                first_name = me.first_name if me.first_name is not None else me.username
                telegram_id = me.id

                if me.last_name is None or not '🌱SEED' in me.last_name: await client(account.UpdateProfileRequest(last_name='🌱SEED'))

                webapp_response: AppWebViewResultUrl = await client(messages.RequestAppWebViewRequest(
                    peer='seed_coin_bot',
                    app=InputBotAppShortName(bot_id=await client.get_input_entity('seed_coin_bot'), short_name='app'),
                    platform='ios',
                    write_allowed=True,
                    start_param='1190101871'
                ))
                query = unquote(string=webapp_response.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

                if client.is_connected():
                    await client.disconnect()

                return query, first_name, telegram_id
        except Exception as err:
            await client.disconnect()
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {session} Unexpected Error While Generating Query With Telethon: {str(err)} ]{Style.RESET_ALL}")
            return None

    async def generate_queries(self, sessions):
        tasks = [self.generate_query(session) for session in sessions]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def profile(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/profile'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError):
            return False

    async def profile2(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/profile2'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    profile2 = await response.json()
                    if not profile2['data']['give_first_egg']:
                        return await self.give_first_egg(query=query)
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Profile: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Profile: {str(err)} ]{Style.RESET_ALL}")

    async def give_first_egg(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/give-first-egg'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Already Received Give First Egg ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    give_first_egg = await response.json()
                    if give_first_egg['data']['status'] == 'in-inventory':
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {give_first_egg['data']['type']} From Give First Egg ]{Style.RESET_ALL}")
                        return await self.complete_egg_hatch(query=query, egg_id=give_first_egg['data']['id'])
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Give First Egg: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Give First Egg: {str(err)} ]{Style.RESET_ALL}")

    async def balance_profile(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/profile/balance'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as err:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Profile Balance: {str(err)} ]{Style.RESET_ALL}")
            return None
        except Exception as err:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Profile Balance: {str(err)} ]{Style.RESET_ALL}")
            return None

    async def upgrade_mining_seed(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/seed/mining-speed/upgrade'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Seed To Upgrade Mining Seed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Mining Seed ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrade Mining Seed: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrade Mining Seed: {str(err)} ]{Style.RESET_ALL}")

    async def upgrade_storage_size(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/seed/storage-size/upgrade'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Seed To Upgrade Storage Size ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Storage Size ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrade Storage Size: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrade Storage Size: {str(err)} ]{Style.RESET_ALL}")

    async def me_worms(self, query: str, telegram_id: int):
        url = 'https://alb.seeddao.org/api/v1/worms/me?page=1'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    me_worms = await response.json()
                    if me_worms['data']['items']:
                        for worm in me_worms['data']['items']:
                            if telegram_id != settings.TELEGRAM_ID:
                                if worm['status'] == 'successful':
                                    if not worm['on_market']:
                                        if worm['type'] == 'legendary':
                                            await self.add_market_item(query=query, payload={'worm_id':worm['id'],'price':settings.PRICE_LEGENDARY_WORM * 1000000000}, item_type=f"Worm {worm['type']}")
                                        elif worm['type'] == 'epic':
                                            await self.add_market_item(query=query, payload={'worm_id':worm['id'],'price':settings.PRICE_EPIC_WORM * 1000000000}, item_type=f"Worm {worm['type']}")
                                        elif worm['type'] == 'rare':
                                            await self.add_market_item(query=query, payload={'worm_id':worm['id'],'price':settings.PRICE_RARE_WORM * 1000000000}, item_type=f"Worm {worm['type']}")
                                    else:
                                        if worm['type'] == 'legendary' and worm['price'] != settings.PRICE_LEGENDARY_WORM * 1000000000:
                                            await self.cancel_market_item(query=query, payload={'worm_id':worm['id'],'price':settings.PRICE_LEGENDARY_WORM * 1000000000}, market_id=worm['market_id'], item_type=f"Worm {worm['type']}")
                                        elif worm['type'] == 'epic' and worm['price'] != settings.PRICE_EPIC_WORM * 1000000000:
                                            await self.cancel_market_item(query=query, payload={'worm_id':worm['id'],'price':settings.PRICE_EPIC_WORM * 1000000000}, market_id=worm['market_id'], item_type=f"Worm {worm['type']}")
                                        elif worm['type'] == 'rare' and worm['price'] != settings.PRICE_RARE_WORM * 1000000000:
                                            await self.cancel_market_item(query=query, payload={'worm_id':worm['id'],'price':settings.PRICE_RARE_WORM * 1000000000}, market_id=worm['market_id'], item_type=f"Worm {worm['type']}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me Worms: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me Worms: {str(err)} ]{Style.RESET_ALL}")

    async def me_egg(self, query: str, telegram_id: int):
        url = 'https://alb.seeddao.org/api/v1/egg/me?page=1'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    me_egg = await response.json()
                    if me_egg['data']['items']:
                        for egg in me_egg['data']['items']:
                            if telegram_id == settings.TELEGRAM_ID:
                                if egg['status'] == 'in-inventory':
                                    if egg['type'] == 'common':
                                        await self.add_market_item(query=query, payload={'egg_id':egg['id'],'price':settings.PRICE_COMMON_EGG * 1000000000}, item_type=f"Egg {egg['type']}")
                                elif egg['status'] == 'on-market':
                                    if egg['price'] != settings.PRICE_COMMON_EGG * 1000000000:
                                        await self.cancel_market_item(query=query, payload={'egg_id':egg['id'],'price':settings.PRICE_COMMON_EGG * 1000000000}, market_id=egg['market_id'], item_type=f"Egg {egg['type']}")
                            else:
                                await self.egg_transfer(query=query, egg_id=egg['id'])
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me Egg: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me Egg: {str(err)} ]{Style.RESET_ALL}")

    async def spin_ticket(self, query: str, telegram_id: int):
        url = 'https://alb.seeddao.org/api/v1/spin-ticket'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    spin_ticket = await response.json()
                    for spin in spin_ticket['data']:
                        await self.spin_reward(query=query, ticket_id=spin['id'])
                        await asyncio.sleep(2)
                    if id != settings.TELEGRAM_ID:
                        await self.egg_piece(query=query, telegram_id=telegram_id)
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Spin Ticket: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Spin Ticket: {str(err)} ]{Style.RESET_ALL}")

    async def spin_reward(self, query: str, ticket_id: str):
        url = 'https://alb.seeddao.org/api/v1/spin-reward'
        data = json.dumps({'ticket_id':ticket_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 404:
                        error_message_spin_reward = await response.json()
                        if error_message_spin_reward['message'] == 'ticket not found':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Ticket Not Found While Spin Reward ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    spin_reward = await response.json()
                    if spin_reward['data']['status'] == 'received':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {spin_reward['data']['type']} From Spin Reward ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Spin Reward: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Spin Reward: {str(err)} ]{Style.RESET_ALL}")

    async def egg_piece(self, query: str, telegram_id: int):
        url = 'https://alb.seeddao.org/api/v1/egg-piece'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    egg_piece = await response.json()
                    common_entries = [entry['id'] for entry in egg_piece['data'] if entry['type'] == 'common']
                    for i in range(0, len(common_entries), 5):
                        batch = common_entries[i:i+5]
                        if len(batch) == 5:
                            payload = {'egg_piece_ids':batch}
                            await self.egg_piece_merge(query=query, payload=payload)
                    if settings.AUTO_SELL_TRANSFER_EGG:
                        await self.me_egg(query=query, telegram_id=telegram_id)
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Egg Piece: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Egg Piece: {str(err)} ]{Style.RESET_ALL}")

    async def egg_piece_merge(self, query: str, payload: dict):
        url = 'https://alb.seeddao.org/api/v1/egg-piece-merge'
        data = json.dumps(payload)
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        error_message_egg_piece_merge = await response.json()
                        if error_message_egg_piece_merge['message'] == 'you can only fuse twice a day':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Can Only Fuse Twice A Day ]{Style.RESET_ALL}")
                        elif error_message_egg_piece_merge['message'] == 'you don\'t have enough seeds':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Don\'t Have Enough Seeds ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    egg_piece_merge = await response.json()
                    if egg_piece_merge['data']['status'] == 'in-inventory':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Egg Piece Merge {egg_piece_merge['data']['type']} ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Egg Piece Merge: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Egg Piece Merge: {str(err)} ]{Style.RESET_ALL}")

    async def egg_transfer(self, query: str, egg_id: str):
        url = 'https://alb.seeddao.org/api/v1/transfer/egg'
        data = json.dumps({'telegram_id':settings.TELEGRAM_ID,'egg_id':egg_id,'max_fee':2000000000})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 500:
                        error_message_egg_transfer = await response.json()
                        if error_message_egg_transfer['message'] == 'not enough seed':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Not Enough Seed While Transfer Egg ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    egg_transfer = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You ({egg_transfer['data']['created_by']}) Have Successfully Transfer {egg_transfer['data']['egg_type']} Egg To {egg_transfer['data']['received_by']} ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Egg Transfer: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Egg Transfer: {str(err)} ]{Style.RESET_ALL}")

    async def complete_egg_hatch(self, query: str, egg_id: str):
        url = 'https://alb.seeddao.org/api/v1/egg-hatch/complete'
        data = json.dumps({'egg_id':egg_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 404:
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Egg Not Existed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    complete_egg_hatch = await response.json()
                    if complete_egg_hatch['data']['status'] == 'in-inventory':
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {complete_egg_hatch['data']['type']} From Egg Hatch ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Complete Egg Hatch: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Complete Egg Hatch: {str(err)} ]{Style.RESET_ALL}")

    async def add_market_item(self, query: str, payload: dict, item_type: str):
        url = 'https://alb.seeddao.org/api/v1/market-item/add'
        data = json.dumps(payload)
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        error_message_add_market_item = await response.json()
                        if error_message_add_market_item['message'] == 'your price looks unusual, please adjust it':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Your Price Looks Unusual, Please Adjust It ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    add_market_item = await response.json()
                    if add_market_item['data']['status'] == 'on-sale':
                        return self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Successfully Add {item_type} To Market ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Price Net {add_market_item['data']['price_net'] / 1000000000} ]{Style.RESET_ALL}"
                        )
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Add Market Item: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Add Market Item: {str(err)} ]{Style.RESET_ALL}")

    async def cancel_market_item(self, query: str, payload: dict, market_id: str, item_type: str):
        url = f'https://alb.seeddao.org/api/v1/market-item/{market_id}/cancel'
        data = json.dumps({'id':market_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    return await self.add_market_item(query=query, payload=payload, item_type=item_type)
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Add Market Item: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Add Market Item: {str(err)} ]{Style.RESET_ALL}")

    async def login_bonuses(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/login-bonuses'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ You\'ve Already Claim Login Bonuses ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    login_bonuses = await response.json()
                    return self.print_timestamp(
                        f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {login_bonuses['data']['amount'] / 1000000000} From Login Bonuses ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Day {login_bonuses['data']['no']} ]{Style.RESET_ALL}"
                    )
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Login Bonuses: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Login Bonuses: {str(err)} ]{Style.RESET_ALL}")

    async def get_streak_reward(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/streak-reward'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    streak_reward = await response.json()
                    if streak_reward['data']:
                        for data in streak_reward['data']:
                            if data['status'] == 'created':
                                await self.streak_reward(query=query, streak_reward_ids=data['id'])
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Streak Reward: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Streak Reward: {str(err)} ]{Style.RESET_ALL}")

    async def streak_reward(self, query: str, streak_reward_ids: str):
        url = 'https://alb.seeddao.org/api/v1/streak-reward'
        data = json.dumps({'streak_reward_ids':[streak_reward_ids]})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 404:
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Streak Reward Not Existed ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    streak_reward = await response.json()
                    for data in streak_reward['data']:
                        if data['status'] == 'received':
                            self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Claimed Streak Reward ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Streak Reward: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Streak Reward: {str(err)} ]{Style.RESET_ALL}")

    async def worms(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/worms'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as err:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Worms: {str(err)} ]{Style.RESET_ALL}")
            return None
        except Exception as err:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Worms: {str(err)} ]{Style.RESET_ALL}")
            return None

    async def catch_worms(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/worms/catch'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        error_catch_worms = await response.json()
                        if error_catch_worms['message'] == 'worm already caught':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Worm Already Caught ]{Style.RESET_ALL}")
                    elif response.status == 404:
                        error_catch_worms = await response.json()
                        if error_catch_worms['message'] == 'worm disappeared':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Worm Disappeared ]{Style.RESET_ALL}")
                        elif error_catch_worms['message'] == 'worm not found':
                            return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Worm Not Found ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    catch_worms = await response.json()
                    if catch_worms['data']['status'] == 'successful':
                        return self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {catch_worms['data']['type']} From Catch Worms ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ Reward {catch_worms['data']['reward'] / 1000000000} ]{Style.RESET_ALL}"
                        )
                    elif catch_worms['data']['status'] == 'failed':
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Failed To Catch {catch_worms['data']['type']} Worms ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Catch Worms: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Catch Worms: {str(err)} ]{Style.RESET_ALL}")

    async def claim_seed(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/seed/claim'
        headers = {
            **self.headers,
            'Content-Length': '0',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Claim Seed Too Early ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    claim_seed = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {claim_seed['data']['amount'] / 1000000000} From Seeding ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Seed: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Seed: {str(err)} ]{Style.RESET_ALL}")

    async def is_leader_bird(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/bird/is-leader'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    is_leader_bird = await response.json()
                    if is_leader_bird['data']['status'] == 'hunting':
                        if datetime.now().astimezone() >= datetime.fromisoformat(is_leader_bird['data']['hunt_end_at'].replace('Z', '+00:00')).astimezone():
                            await self.complete_bird_hunt(query=query, bird_id=is_leader_bird['data']['id'], task_level=is_leader_bird['data']['task_level'])
                        else:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Bird Hunt Can Be Complete At {datetime.fromisoformat(is_leader_bird['data']['hunt_end_at'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                    elif is_leader_bird['data']['status'] == 'in-inventory':
                        if is_leader_bird['data']['happiness_level'] < 10000 or is_leader_bird['data']['energy_level'] < is_leader_bird['data']['energy_max']:
                            await self.bird_happiness(query=query, bird_id=is_leader_bird['data']['id'])
                            await self.me_all_worms(query=query, bird_id=is_leader_bird['data']['id'], task_level=is_leader_bird['data']['task_level'])
                        elif is_leader_bird['data']['happiness_level'] >= 10000 and is_leader_bird['data']['energy_level'] >= is_leader_bird['data']['energy_max']:
                            await self.start_bird_hunt(query=query, bird_id=is_leader_bird['data']['id'], task_level=is_leader_bird['data']['task_level'])
        except ClientResponseError as err:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Is Leader Bird: {str(err)} ]{Style.RESET_ALL}")
            return None
        except Exception as err:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Is Leader Bird: {str(err)} ]{Style.RESET_ALL}")
            return None

    async def me_all_worms(self, query: str, bird_id: str, task_level: int):
        url = 'https://alb.seeddao.org/api/v1/worms/me-all'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    me_all_worms = await response.json()
                    if me_all_worms['data']:
                        for data in me_all_worms['data']:
                            if data['status'] == 'successful' and (data['type'] == 'common' or data['type'] == 'uncommon'):
                                await self.bird_feed(query=query, bird_id=bird_id, worm_ids=data['id'])
                        return await self.start_bird_hunt(query=query, bird_id=bird_id, task_level=task_level)
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Me All Worms: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Me All Worms: {str(err)} ]{Style.RESET_ALL}")

    async def bird_happiness(self, query: str, bird_id):
        url = 'https://alb.seeddao.org/api/v1/bird-happiness'
        data = json.dumps({'bird_id':bird_id,'happiness_rate':10000})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    bird_happiness = await response.json()
                    if bird_happiness['data']['happiness_level'] >= 10000:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Your Bird Is Happy ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Bird Happiness: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Bird Happiness: {str(err)} ]{Style.RESET_ALL}")

    async def bird_feed(self, query: str, bird_id: str, worm_ids: str):
        url = 'https://alb.seeddao.org/api/v1/bird-feed'
        data = json.dumps({'bird_id':bird_id,'worm_ids':[worm_ids]})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ The Bird Is Full And Cannot Eat Any More ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    bird_feed = await response.json()
                    if bird_feed['data']['energy_level'] <= bird_feed['data']['energy_max']:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Feed Bird Successfully ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Bird Feed: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Bird Feed: {str(err)} ]{Style.RESET_ALL}")

    async def start_bird_hunt(self, query: str, bird_id: str, task_level: int):
        url = 'https://alb.seeddao.org/api/v1/bird-hunt/start'
        data = json.dumps({'bird_id':bird_id,'task_level':task_level})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Start Hunting Time Is Not Over Yet ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    start_bird_hunt = await response.json()
                    if start_bird_hunt['data']['status'] == 'hunting':
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Your Bird Is Hunting ]{Style.RESET_ALL}")
                        if datetime.now().astimezone() >= datetime.fromisoformat(start_bird_hunt['data']['hunt_end_at'].replace('Z', '+00:00')).astimezone():
                            return await self.complete_bird_hunt(query=query, bird_id=start_bird_hunt['data']['id'], task_level=start_bird_hunt['data']['task_level'])
                        return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Bird Hunt Can Be Complete At {datetime.fromisoformat(start_bird_hunt['data']['hunt_end_at'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Bird Hunt: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Bird Hunt: {str(err)} ]{Style.RESET_ALL}")

    async def complete_bird_hunt(self, query: str, bird_id: str, task_level: int):
        url = 'https://alb.seeddao.org/api/v1/bird-hunt/complete'
        data = json.dumps({'bird_id':bird_id,'task_level':task_level})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    if response.status == 400:
                        return self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Complete Hunting Time Is Not Over Yet ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    complete_bird_hunt = await response.json()
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {complete_bird_hunt['data']['seed_amount'] / 1000000000} From Bird Hunt ]{Style.RESET_ALL}")
                    return await self.is_leader_bird(query=query)
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Complete Bird Hunt: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Complete Bird Hunt: {str(err)} ]{Style.RESET_ALL}")

    @staticmethod
    async def answers():
        url = 'https://raw.githubusercontent.com/Shyzg/answer/refs/heads/main/answer.json'
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, ssl=False) as response:
                    response.raise_for_status()
                    return json.loads(await response.text())
        except (Exception, ClientResponseError):
            return None

    async def progresses_tasks(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/tasks/progresses'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    progresses_tasks = await response.json()
                    for task in progresses_tasks['data']:
                        if task['task_user'] is None or not task['task_user']['completed']:
                            if task['type'] == 'academy':
                                answers = await self.answers()
                                if answers is not None:
                                    answer = answers['seed']['youtube'][task['name']]
                                    await self.tasks(query=query, task_id=task['id'], task_name=task['name'], payload={'answer':answer})
                            else:
                                await self.tasks(query=query, task_id=task['id'], task_name=task['name'], payload={})
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Progresses Tasks: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Progresses Tasks: {str(err)} ]{Style.RESET_ALL}")

    async def tasks(self, query: str, task_id: str, task_name: str, payload: dict):
        url = f'https://alb.seeddao.org/api/v1/tasks/{task_id}'
        data = json.dumps(payload)
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'text/plain;charset=UTF-8',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ If {task_name} Still Appear In Next Restart, You Must Complete Manually ]{Style.RESET_ALL}")
        except (Exception, ClientResponseError):
            return None

    async def detail_member_guild(self, query: str):
        url = 'https://alb.seeddao.org/api/v1/guild/member/detail'
        headers = {
            **self.headers,
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    detail_member_guild = await response.json()
                    if detail_member_guild['data'] is None or detail_member_guild['data']['guild_id'] is None:
                        return await self.join_guild(query=query, guild_id='b4480be6-0f4a-42d2-8f58-bc087daa33c3')
                    elif detail_member_guild['data']['guild_id'] != 'b4480be6-0f4a-42d2-8f58-bc087daa33c3':
                        return await self.leave_guild(query=query, guild_id=detail_member_guild['data']['guild_id'])
        except ClientResponseError as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Detail Member Guild: {str(err)} ]{Style.RESET_ALL}")
        except Exception as err:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Detail Member Guild: {str(err)} ]{Style.RESET_ALL}")

    async def join_guild(self, query: str, guild_id: str):
        url = 'https://alb.seeddao.org/api/v1/guild/join'
        data = json.dumps({'guild_id':guild_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError):
            return False

    async def leave_guild(self, query: str, guild_id: str):
        url = 'https://alb.seeddao.org/api/v1/guild/leave'
        data = json.dumps({'guild_id':guild_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'telegram-data': query
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    return await self.join_guild(query=query, guild_id='b4480be6-0f4a-42d2-8f58-bc087daa33c3')
        except (Exception, ClientResponseError):
            return False

    async def main(self):
        while True:
            try:
                sessions = [file for file in os.listdir('sessions/') if file.endswith('.session')]
                if not sessions:
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Session Files Found In The Folder! Please Make Sure There Are '*.session' Files In The Folder. ]{Style.RESET_ALL}")
                accounts = await self.generate_queries(sessions)
                total_balance = 0.0
                restart_times = []

                for (query, name, telegram_id) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.profile(query=query)
                    await self.profile2(query=query)
                    await self.claim_seed(query=query)
                    worms = await self.worms(query=query)
                    if worms is not None:
                        if datetime.now().astimezone() >= datetime.fromisoformat(worms['data']['created_at'].replace('Z', '+00:00')).astimezone():
                            if not worms['data']['is_caught']:
                                await self.catch_worms(query=query)
                            restart_times.append(datetime.fromisoformat(worms['data']['next_worm'].replace('Z', '+00:00')).astimezone().timestamp())
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Next Worms Can Be Catch At {datetime.fromisoformat(worms['data']['next_worm'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                        else:
                            restart_times.append(datetime.fromisoformat(worms['data']['created_at'].replace('Z', '+00:00')).astimezone().timestamp())
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Next Worms Can Be Catch At {datetime.fromisoformat(worms['data']['created_at'].replace('Z', '+00:00')).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                    if settings.AUTO_SELL_TRANSFER_EGG:
                        await self.me_egg(query=query, telegram_id=telegram_id)
                    if settings.AUTO_SELL_WORMS:
                        await self.me_worms(query=query, telegram_id=telegram_id)

                for (query, name, telegram_id) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Earn ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.login_bonuses(query=query)
                    await self.get_streak_reward(query=query)
                    await self.progresses_tasks(query=query)

                for (query, name, telegram_id) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home/Is Leader ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                    )
                    await self.is_leader_bird(query=query)

                if settings.AUTO_UPGRADE:
                    for (query, name, telegram_id) in accounts:
                        self.print_timestamp(
                            f"{Fore.WHITE + Style.BRIGHT}[ Boost ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                        )
                        await self.upgrade_mining_seed(query=query)
                        await self.upgrade_storage_size(query=query)

                if settings.AUTO_SPIN:
                    for (query, name, telegram_id) in accounts:
                        self.print_timestamp(
                            f"{Fore.WHITE + Style.BRIGHT}[ Spin & Merge Egg ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {name} ]{Style.RESET_ALL}"
                        )
                        await self.spin_ticket(query=query, telegram_id=telegram_id)

                for (query, name, telegram_id) in accounts:
                    await self.detail_member_guild(query=query)
                    balance_profile = await self.balance_profile(query=query)
                    total_balance += float(balance_profile['data'] / 1000000000) if balance_profile else 0.0

                if restart_times:
                    wait_times = [catch_worms - datetime.now().astimezone().timestamp() for catch_worms in restart_times if catch_worms > datetime.now().astimezone().timestamp()]
                    if wait_times:
                        sleep_time = min(wait_times)
                    else:
                        sleep_time = 15 * 60
                else:
                    sleep_time = 15 * 60

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=sleep_time)).strftime('%x %X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(sleep_time)
                self.clear_terminal()
            except Exception as err:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(err)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        init(autoreset=True)

        if not settings.API_ID or not settings.API_HASH:
            raise ValueError("API_ID Or API_HASH Not Found In The .env File")

        seed = Seed()
        asyncio.run(seed.main())
    except (ValueError, IndexError, FileNotFoundError) as error:
        print(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}", flush=True)
    except KeyboardInterrupt:
        sys.exit(0)
