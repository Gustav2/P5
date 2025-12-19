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
    def broadcast(cls, sender: "Node", msg):
        #print(msg)
        #print(f"Node {sender.id:02d} is broadcasting message at time {msg['time']}")
        for node in cls.nodes:
            #print(node)
            #print(f"Node {sender.id:02d} is broadcasting message to {node.id:02d}")
            #print(f"Node {node.id:02d} State: {node.state}")
            if node.id == sender.id:
                #print(f"Node {node.id:02d} is sender, skipping")
                continue
            if node.state != State.Receive:
                continue
            if random.random() > PT_LOSS:
                #print(cls.nodes)
                #print(node)
                cls._deliver(node, msg)
    
    @classmethod
    def _deliver(cls, receiver: "Node", msg):
        receiver.env.process(receiver.receive(msg)) 
        cls.mailboxes[receiver.id].append(msg.copy())
        #if msg['to'] == None:
            #print(f"Node {msg['id']:02d} transmitted DISC       to all at time {msg['time']}")
        #if msg['to'] != None:
            #print(f"Node {msg['id']:02d} transmitted ACK DISC   to {msg['to']:02d}  at time {msg['time']}")


    @classmethod
    def messages_received(cls, node: "Node"):
        temp = cls.mailboxes[node.id]
        cls.mailboxes[node.id] = []
        return len(temp) > 0