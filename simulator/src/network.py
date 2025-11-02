import random

from typing import TYPE_CHECKING, List

from .config import TX_LOSS, DELAY_RANGE

if TYPE_CHECKING:
    from .node import Node

class Network:
    nodes: List["Node"] = []
    mailboxes = {}

    @classmethod
    def register_node(cls, node: "Node"):
        cls.nodes.append(node)
        cls.mailboxes[node.id] = []

    @classmethod
    def broadcast(cls, sender: "Node", message):
        for node in cls.nodes:
            if node.id == sender.id:
                continue
            if random.random() > TX_LOSS:
                delay = random.uniform(DELAY_RANGE[0], DELAY_RANGE[1])
                node.env.process(cls._deliver(node, message, delay))
    
    @classmethod
    def _deliver(cls, receiver: "Node", msg, delay: float):
        yield receiver.env.timeout(delay)
        receiver.receive(msg)
        cls.mailboxes[receiver.id].append(msg)

    @classmethod
    def messages_received(cls, node: "Node"):
        temp = cls.mailboxes[node.id]
        cls.mailboxes[node.id] = []
        return len(temp) > 0