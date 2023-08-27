from threading import Thread

from berserk import Client, TokenSession
from dotenv import load_dotenv
import os


load_dotenv()


class LiChess:
    def __init__(self):
        self._session = TokenSession(os.getenv("API_TOKEN"))
        self._client = Client(session=self._session)
        self._stream = None
        self.stream_events = []

    def new_game(self):
        game = self._client.challenges.create_ai(level=1, clock_limit=1260, clock_increment=0, variant="standard")
        self._stream = self._client.board.stream_game_state(game["id"])
        print(self._stream)
        self.start_watching_thread()

    def start_watching_thread(self):
        def update_events():
            for event in self._stream:
                self.stream_events.append(event)
        thread = Thread(target=update_events)
        thread.start()

    def pop_events(self):
        events = self.stream_events.copy()
        self.stream_events = []
        return events

# x = {'id': 'vE8cv1Qk', 'variant': {'key': 'standard', 'name': 'Standard', 'short': 'Std'}, 'speed': 'bullet', 'perf': 'bullet', 'rated': False, 'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 'turns': 0, 'source': 'ai', 'status': {'id': 20, 'name': 'started'}, 'createdAt': 1693046497604, 'player': 'white'}
