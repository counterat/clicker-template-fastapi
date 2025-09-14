from apscheduler.schedulers.asyncio import AsyncIOScheduler

from server.repositories.game import GameRepository

scheduler = AsyncIOScheduler()

scheduler.add_job(GameRepository.click_for_tapbots, 'interval', minutes=1)
scheduler.add_job(GameRepository.regenerate_energy, 'interval', seconds=4)
scheduler.add_job(GameRepository.give_10_percents_of_income_to_invited_by, 'interval', hours=24)
scheduler.add_job(GameRepository.send_phrases, 'interval', seconds=10)
