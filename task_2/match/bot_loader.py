"""Small file-based bot interface, isolated so a slow bot can be stopped."""

import importlib.util
import multiprocessing as mp
from pathlib import Path
from time import perf_counter

from task_2.core.state import Action


def _call_bot(path, state, tank_id, draft, deadline, connection):
    try:
        spec = importlib.util.spec_from_file_location("guest_tank_bot", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        action = module.choose_action(state, tank_id, draft, deadline)
        connection.send(("ok", action))
    except Exception as error:
        connection.send(("error", f"{type(error).__name__}: {error}"))
    finally:
        connection.close()


class FileAgent:
    def __init__(self, path, tank_id):
        self.path = str(Path(path).resolve(strict=True))
        self.tank_id = tank_id
        self.cancel_event = None
        self.last_result = None

    def choose_action(self, state, draft, deadline=None):
        context = mp.get_context("spawn")
        receive, send = context.Pipe(duplex=False)
        process = context.Process(
            target=_call_bot,
            args=(self.path, state, self.tank_id, draft, deadline, send),
            daemon=True,
        )
        process.start()
        send.close()
        try:
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    raise TimeoutError("Bot cancelled")
                remaining = (
                    float("inf") if deadline is None else deadline - perf_counter()
                )
                if remaining <= 0:
                    raise TimeoutError("Bot exceeded its share of the turn budget")
                if receive.poll(min(0.01, remaining)):
                    status, value = receive.recv()
                    if status != "ok":
                        raise RuntimeError(value)
                    if isinstance(value, str):
                        value = Action[value]
                    if not isinstance(value, Action):
                        raise ValueError("Bot must return Action or its enum name")
                    return value
                if not process.is_alive():
                    raise RuntimeError("Bot exited without returning an action")
        finally:
            if process.is_alive():
                process.terminate()
            process.join(timeout=0.1)
            receive.close()
