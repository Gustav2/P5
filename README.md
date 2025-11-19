# Algorithm Explanation

## Run cycle

At the beginning of the cycle, each Node checks when is its **soonest_meet** with other node (the data has been taken from the **dictionary** with data about other nodes). If the **soonest_meet** will be in less amount of seconds, than wake up in a **WAKEUP_RANGE**, Node will change it's state to being wanted to perform **SYNC** for a next wake up point in a time.

After waiting for the **wakeup_in** amount of seconds, Node fisrst listen to a random amount of seconds, between 1 and **WAKEUP_POINT_THRESHOL** (which is used for both sync and discovery, and represents range of seconds in which Node performs any operation) and then perform either **SYNC** or discovery with **BEACON**.

All of the operations can be perform **only if Node has enough energy** and if it's in **Idle** mode.

## Harvesting

During the Node creation we randomly select how many _lux_ it will receive based on the range. We also introduced day cycle, so the _lux_ value changes for each node thtough the day.

## Listen stage

Node is listening to amount of seconds, which is available for it. If node receives a message during listening stage, it processes it.

## Transmitting

Typical payload for node to send includes:

```py
    "type": "BEACON" | "SYNC" | "ACK" # Type of sent message
    "id": int # Id of sender
    "time": int # Local time of sender with clock drift
```

If Node sends **SYNC**, it increases its _sync_tries_ (later used for evaluation of the performance).

## Receiving

Here it splits into 3 ways, depending of _msg_type_.

### BEACON

If sender is not in receiver's table, we add it and send **BEACON** to establish connection (2 way handshake).

Otherwise, we check **soonest_meet** with sender, and if it's 0 (which means they failed to perform **SYNC** at some point) then we update **last_meet** with current time and send **BEACON** to update **last_meet** on other side as well.

We use **last_meet** (considering clock drift) along with **MEETUP_INTERVAL** to calculate our time till next meeting.

### SYNC

First, we check if sender is in Node's table (if no, we just do handshake as well) and then check if current sender is in our meeting window, which specified by **WAKEUP_POINT_TRESHOLD** and if so, we update data in our table and send **ACK**.

### ACK

After receiving an **ACK**, the Node checks if this sender is in the list of nodes we wish to perform **SYNC** with and if so, we update the **last_meet** in our table.
