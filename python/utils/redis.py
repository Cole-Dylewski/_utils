import datetime as dt
import json

# Set up logging
import logging
import os
from typing import Any

from fastapi import HTTPException
import redis
import redis.asyncio as aioredis
from redis.asyncio.client import PubSub

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# TTL in seconds (24 hours)
DEFAULT_TTL = 60 * 60 * 24
# DEFAULT_TTL = 360


# %% Redis Handler Class
class RedisHandler:
    def __init__(
        self,
        host: str = "redis",
        port: int = 6379,
        password: str | None = os.getenv("REDIS_PASSWORD"),
        ssl: str | None = os.getenv("REDIS_SSL"),
    ):
        try:
            # Synchronous client (used in legacy TTL and key functions)
            self.client = redis.StrictRedis(
                host=host, port=port, password=password, decode_responses=True, db=0, ssl=ssl
            )

            # Async client (used for pub/sub and room features)
            self.async_client = aioredis.Redis(
                host=host, port=port, password=password, decode_responses=True, db=0, ssl=ssl
            )

            if not self.client.ping():
                raise HTTPException(status_code=500, detail="Unable to connect to Redis.")

            logger.info("Connected to Redis")
        except redis.ConnectionError as e:
            logger.exception(f"Error connecting to Redis: {e}")
            raise HTTPException(status_code=500, detail="Redis connection failed")

    async def get_all_keys(self) -> list[str]:
        """Retrieves a list of all keys in Redis."""
        try:
            keys = self.client.keys("*")
            logger.info(f"Retrieved {len(keys)} keys from Redis")
            return keys
        except Exception as e:
            logger.exception(f"Error retrieving keys from Redis: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving keys from Redis: {e!s}")

    async def flush(self) -> str:
        """Deletes all keys and clears the Redis memory."""
        try:
            result = self.client.flushdb()
            if result:
                logger.info("All keys deleted. Redis memory cleared.")
                return "All keys deleted. Redis memory cleared."
            logger.warning("Failed to clear Redis memory.")
            return "Failed to clear Redis memory."
        except Exception as e:
            logger.exception(f"Error clearing Redis memory: {e}")
            raise HTTPException(status_code=500, detail=f"Error clearing Redis memory: {e!s}")

    async def get_keys_without_ttl(self) -> list[str]:
        """
        Retrieves all Redis keys that do not have a TTL (expire time).

        Returns:
        - List[str]: A list of keys with no expiration (TTL of -1).

        Raises:
        - HTTPException: If an error occurs during the operation.
        """
        try:
            keys = self.client.keys("*")  # Retrieve all keys
            keys_without_ttl = []

            for key in keys:
                ttl = self.client.ttl(key)
                if ttl == -1:
                    keys_without_ttl.append(key)

            logger.info(f"Retrieved {len(keys_without_ttl)} keys with no TTL.")
            return keys_without_ttl
        except Exception as e:
            logger.exception(f"Error retrieving keys without TTL: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving keys without TTL: {e!s}")

    async def condemn_keys(self, ttl: int = DEFAULT_TTL) -> list[str]:
        """
        Assigns a default TTL to all Redis keys without expiration.

        Parameters:
        - ttl (int): Time-to-live in seconds (default is set to DEFAULT_TTL).

        Returns:
        - List[str]: A list of keys that had no TTL and were updated.

        Raises:
        - HTTPException: If an error occurs during the operation.
        """
        try:
            keys_without_ttl = await self.get_keys_without_ttl()

            if not keys_without_ttl:
                logger.info("No keys found without TTL.")
                return []

            for key in keys_without_ttl:
                await self.set_ttl_for_key(key, ttl)
                logger.info(f"TTL of {ttl} seconds set for key: {key}")

            logger.info(f"{len(keys_without_ttl)} keys updated with TTL of {ttl} seconds.")
            return keys_without_ttl

        except Exception as e:
            logger.exception(f"Error setting TTL for keys without TTL: {e}")
            raise HTTPException(status_code=500, detail=f"Error setting TTL for keys: {e!s}")

    async def set_ttl_for_key(self, key: str, ttl: int) -> bool:
        """
        Assigns a TTL (time-to-live) to an existing Redis key.

        Parameters:
        - key (str): The Redis key to set a TTL on.
        - ttl (int): Time-to-live in seconds.

        Returns:
        - bool: True if TTL was set successfully, False otherwise.

        Raises:
        - HTTPException: If an error occurs during the operation.
        """
        try:
            if not self.client.exists(key):
                logger.warning(f"Key '{key}' not found in Redis.")
                return False

            result = self.client.expire(key, ttl)
            if result:
                logger.info(f"TTL of {ttl} seconds set for key: {key}")
                return True
            logger.warning(f"Failed to set TTL for key '{key}'")
            return False
        except Exception as e:
            logger.exception(f"Error setting TTL for key '{key}': {e}")
            raise HTTPException(status_code=500, detail=f"Error setting TTL for key: {e!s}")

    async def set_key(self, key: str, obj: dict[str, Any], ttl: int | None = DEFAULT_TTL) -> None:
        """Stores a JSON object in Redis with an optional TTL."""
        try:
            obj_json = json.dumps(obj)
            if ttl:
                print("RESETTING TTL")
                self.client.setex(key, ttl, obj_json)
            else:
                self.client.set(key, obj_json)
            logger.info(f"Stored object with key '{key}' and TTL: {ttl if ttl else 'None'}")
        except Exception as e:
            logger.exception(f"Error storing object: {e}")
            raise HTTPException(status_code=500, detail=f"Error storing key: {e!s}")

    async def get_key(self, key: str) -> dict[str, Any]:
        """
        Retrieves metadata for a given Redis key, including TTL, type, last access time, and memory usage.
        """
        try:
            ttl = self.client.ttl(key)
            value = self.client.get(key)
            exists = self.client.exists(key)
            key_type = self.client.type(key)
            idle_time = self.client.object("idletime", key) if exists else None
            memory_usage = self.client.memory_usage(key) if exists else None
            expire_time = self.client.expiretime(key) if exists else None

            return {
                "key": key,
                "exists": bool(exists),
                "ttl": ttl,
                "type": key_type,
                "idle_time": idle_time,
                "memory_usage": memory_usage,
                "expire_time": expire_time,
                "value": json.loads(value) if value else None,
            }
        except Exception as e:
            logger.exception(f"Error retrieving metadata for key '{key}': {e}")
            raise HTTPException(
                status_code=500, detail=f"Error retrieving metadata from Redis: {e!s}"
            )

    def _format_memory(self, bytes_value: int) -> str:
        if bytes_value < 1024:
            return f"{bytes_value} Bytes"
        if bytes_value < 1048576:
            return f"{bytes_value / 1024:.2f} KB"
        if bytes_value < 1073741824:
            return f"{bytes_value / 1048576:.2f} MB"
        return f"{bytes_value / 1073741824:.2f} GB"

    async def get_total_memory_usage(self) -> dict[str, str]:
        """Returns Redis total memory usage with flexible units (bytes, KB, MB, GB)."""
        try:
            memory_info = self.client.info("memory")
            used_memory = memory_info.get("used_memory", 0)
            peak_memory = memory_info.get("used_memory_peak", 0)
            max_memory = memory_info.get("maxmemory", 0)

            return {
                "Used Memory": self._format_memory(used_memory),
                "Peak Memory": self._format_memory(peak_memory),
                "Max Memory Configured": self._format_memory(max_memory)
                if max_memory > 0
                else "Unlimited",
                "Memory Fragmentation Ratio": f"{memory_info.get('mem_fragmentation_ratio', 'N/A')}",
            }
        except Exception as e:
            logger.exception(f"Error retrieving total memory usage from Redis: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving memory usage: {e!s}")

    async def update_attribute_by_key(self, key: str, attribute: str, value: Any) -> bool:
        """
        Updates a specific attribute of the JSON object stored under the specified key.

        Parameters:
        - key (str): The key under which the object is stored in Redis.
        - attribute (str): The attribute to update in the JSON object.
        - value: The new value for the specified attribute.

        Returns:
        - bool: True if the update was successful, False otherwise.
        """
        try:
            data = await self.get_key(key)
            # print(data)
            # print(data.keys())
            if data is None:
                logger.info(f"Key '{key}' not found.")
                return False
            data["value"][attribute] = value
            # print('NEW VALUES',data['value'])
            await self.set_key(key, data["value"], DEFAULT_TTL)
            logger.info(f"Updated '{attribute}' for key '{key}' and reset TTL to {DEFAULT_TTL}s.")
            return True
        except Exception as e:
            logger.exception(f"Error updating key '{key}': {e}")
            raise HTTPException(status_code=500, detail=f"Update error: {e!s}")

    async def delete_key(self, key: str) -> bool:
        """
        Deletes a key from Redis.

        Parameters:
        - key (str): The key to be deleted.

        Returns:
        - bool: True if the key was deleted, False otherwise.
        """
        try:
            result = self.client.delete(key)  # Delete the key from Redis
            if result == 1:
                logger.info(f"Key '{key}' deleted from Redis")
                return True
            logger.info(f"Key '{key}' not found in Redis")
            return False
        except Exception as e:
            logger.exception(f"Error deleting key '{key}' from Redis: {e}")
            raise HTTPException(status_code=500, detail=f"Error deleting key from Redis: {e!s}")

    async def ping(self) -> str:
        """
        Pings the Redis server to test the connection.
        """
        try:
            pong = self.client.ping()
            if pong:
                logger.info("Ping successful: Pong")
                return "Pong"
            raise HTTPException(status_code=500, detail="Ping to Redis failed")
        except Exception as e:
            logger.exception(f"Error pinging Redis: {e}")
            raise HTTPException(status_code=500, detail=f"Error pinging Redis: {e!s}")

    async def create_room(self, room_name: str) -> bool:
        """
        Creates a new Redis key representing a logical chat room.

        This function ensures that a dedicated key for the room exists. It's not strictly
        necessary for Redis pub/sub (which works on channels), but this gives us a persistent
        metadata anchor for the room — useful for managing room state, TTL, permissions, etc.

        Parameters:
        - room_name (str): The name of the chat room to create.

        Returns:
        - bool: True if the room was created, False if it already exists.
        """
        try:
            key = f"room:{room_name}"
            # Check if the room key already exists in Redis
            if await self.async_client.exists(key):
                logger.info(f"Room '{room_name}' already exists.")
                return False
            # Set a basic JSON structure indicating creation; placeholder for future metadata
            # await self.async_client.set(key, json.dumps({"created": True}))
            await self.set_key(key=key, obj={"created": True, "active_users": 0, "messages": {}})
            logger.info(f"Room '{room_name}' created.")
            return True
        except Exception as e:
            logger.exception(f"Failed to create room '{room_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Room creation failed: {e!s}")

    async def publish_to_room(self, room_name: str, message: str) -> int:
        """
        Publishes a message to a given room.

        Internally uses Redis's pub/sub mechanism. Messages are sent to the channel
        corresponding to the room. All subscribers currently listening to that room's
        channel will receive the message.

        Parameters:
        - room_name (str): The target room to broadcast to.
        - message (str): The message content to send.

        Returns:
        - int: Number of subscribers that received the message.
        """
        try:
            print("Publishing to room:", room_name, "Message:", message)
            channel = f"room:{room_name}"
            room_val = await self.get_key(f"room:{room_name}")
            # print('ROOM KEY',room_val, room_val.get('value',{}))
            # print('msg key exists?',bool(room_val['value']['messages'].get(dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))))
            room_val["value"]["messages"][dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")] = (
                message
            )

            # for k,v in room_val.items():
            #     print(f"{k}: {v}")
            await self.set_key(key=f"room:{room_name}", obj=room_val["value"])
            result = await self.async_client.publish(channel, message)
            logger.info(f"Published message to '{channel}' ({result} subscribers).")
            return result
        except Exception as e:
            logger.exception(f"Failed to publish message to room '{room_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Publish failed: {e!s}")

    async def subscribe_to_room(self, room_name: str) -> PubSub:
        """
        Subscribes to the Redis pub/sub channel for the given room.

        Returns a PubSub object that allows you to listen to messages published
        to this channel. This object must be actively listened to via `listen_to_room`.

        Parameters:
        - room_name (str): The room name to subscribe to.

        Returns:
        - PubSub: The subscription object to listen on.
        """
        try:
            await self.create_room(room_name)  # Ensure the room exists before subscribing
            print("Subscribing to room:", room_name)
            pubsub = self.async_client.pubsub()
            await pubsub.subscribe(f"room:{room_name}")

            room_val = await self.get_key(f"room:{room_name}")
            active_users = room_val["value"].get("active_users", 0)
            active_users += 1
            room_val["value"]["active_users"] = active_users

            await self.set_key(key=f"room:{room_name}", obj=room_val["value"])

            await self.publish_to_room(room_name, "A user has joined the room")
            logger.info(f"Subscribed to room: {room_name}")
            return pubsub
        except Exception as e:
            logger.exception(f"Failed to subscribe to room '{room_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Subscribe failed: {e!s}")

    async def unsubscribe_from_room(self, pubsub: PubSub, room_name: str) -> None:
        """
        Unsubscribes from the Redis pub/sub channel for the given room.

        Parameters:
        - pubsub (PubSub): The subscription object.
        - room_name (str): The room to unsubscribe from.
        """
        try:
            await pubsub.unsubscribe(f"room:{room_name}")
            room_val = await self.get_key(f"room:{room_name}")
            active_users = room_val["value"].get("active_users", 0)
            active_users -= 1
            room_val["value"]["active_users"] = active_users

            await self.set_key(key=f"room:{room_name}", obj=room_val["value"])
            logger.info(f"Unsubscribed from room: {room_name}")
        except Exception as e:
            logger.exception(f"Failed to unsubscribe from room '{room_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Unsubscribe failed: {e!s}")

    async def listen_to_room(self, pubsub: PubSub, callback):
        """
        Listens to messages on the subscribed room's pub/sub channel.

        This method keeps running as long as the subscription is active. When a message
        is received, it passes the message data to the provided callback function.

        Parameters:
        - pubsub (PubSub): The subscription object to listen on.
        - callback (Callable): An async function that will be called with the message data.

        Notes:
        - The callback must be awaitable (async def).
        - Messages of type 'message' will be forwarded; other pubsub internal messages are ignored.
        """
        try:
            async for message in pubsub.listen():
                # print('listen msg',message)
                if message["type"] == "message":
                    # logger.info(f"Received message: {message['data']}")
                    await callback(message["data"])
        except Exception as e:
            logger.exception(f"Error while listening to room: {e}")
            raise
