import random

from typing import TYPE_CHECKING, List

from ..config import PT_LOSS
from ..node.state import State

if TYPE_CHECKING:
    from ..node.node import Node

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
            if node.state != State.Receive:
                continue
            if random.random() > PT_LOSS:
                cls._deliver(node, message)
    
    @classmethod
    def _deliver(cls, receiver: "Node", msg):
        receiver.env.process(receiver.receive(msg)) 
        cls.mailboxes[receiver.id].append(msg)

    @classmethod
    def messages_received(cls, node: "Node"):
        temp = cls.mailboxes[node.id]
        cls.mailboxes[node.id] = []
        return len(temp) > 0