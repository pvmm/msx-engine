import asyncio
import functools
from collections import defaultdict
from typing import Awaitable, Callable, Dict, Set, ParamSpec, TypeVar
from nicegui import ui


P = ParamSpec("P")
R = TypeVar("R")


class SessionBrokerManager:
    def __init__(self) -> None:
        # Structure: { client_id: { channel: set(callbacks) } }
        self._subscribers: Dict[str, Dict[str, Set[Callable[[str], None]]]] = defaultdict(lambda: defaultdict(set))


    def get_client_id(self) -> str:
        """Helper to get the current unique NiceGUI browser tab ID."""
        return ui.context.client.id


    def subscribe(self, channel: str, callback: Callable[[str], None]) -> None:
        client_id = self.get_client_id()
        self._subscribers[client_id][channel].add(callback)


    def unsubscribe(self, channel: str, callback: Callable[[str], None]) -> None:
        client_id = self.get_client_id()
        self._subscribers[client_id][channel].discard(callback)


    def publish_to_current_user(self, channel: str, payload: str) -> None:
        """Publishes a payload strictly to the user belonging to the current execution context."""
        client_id = self.get_client_id()
        callbacks = list(self._subscribers[client_id][channel])
        for callback in callbacks:
            try:
                callback(payload)
            except Exception as e:
                ui.notify(f"got a callback error: {e}")


def show_waiting_dialog(message: str) -> ui.dialog:
    with ui.dialog() as waiting_dialog, ui.card().classes('items-center p-6'):
        ui.spinner(size='lg').classes('mb-2')
        ui.label(message).classes('text-lg font-medium')

    def handle_message(payload: str) -> None:
        '''what to do when task is done'''
        if payload == "CLOSE_DIALOG":
            waiting_dialog.close()
            # clean up
            GLOBAL_BROKER.unsubscribe(channel='WAITING_DIALOG', callback=handle_message)

    # register subscriber
    GLOBAL_BROKER.subscribe(channel='WAITING_DIALOG', callback=handle_message)

    # trigger action
    waiting_dialog.open()
    return waiting_dialog


def display_task_dialog(message: str) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """
    Decorator that automatically sends a completion message to the
    GLOBAL_BROKER targeting the specific user session that triggered it.
    """

    def decorator(func: Callable[P, Awaitable[R]],) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            show_waiting_dialog(message)

            # allow event loop to breathe
            await asyncio.sleep(0.1)

            try:
                return await func(*args, **kwargs)
            finally:
                GLOBAL_BROKER.publish_to_current_user(
                    "WAITING_DIALOG",
                    "CLOSE_DIALOG",
                )
        return wrapper
    return decorator


# the global message broker
GLOBAL_BROKER = SessionBrokerManager()
